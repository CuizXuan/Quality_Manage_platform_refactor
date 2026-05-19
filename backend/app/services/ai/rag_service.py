# -*- coding: utf-8 -*-
"""
Phase 5 - RAG 向量检索服务
"""
import json
import hashlib
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.ai_models import VectorDoc, EmbeddingCache


class RAGService:
    """RAG 向量检索服务"""

    # 向量维度 (text-embedding-ada-002)
    EMBEDDING_DIM = 1536

    # 简单的中文 / 英文分词
    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """简单的分词"""
        import re

        # 移除特殊字符，按空格和标点分割
        tokens = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
        return tokens

    @staticmethod
    def _compute_hash(text: str) -> str:
        """计算文本哈希"""
        return hashlib.sha256(text.encode()).hexdigest()

    def __init__(self, db: Session):
        self.db = db

    def retrieve(
        self,
        query: str,
        project_id: int,
        top_k: int = 5,
        doc_types: Optional[List[str]] = None,
    ) -> List[dict]:
        """
        向量检索

        Args:
            query: 查询文本
            project_id: 项目 ID
            top_k: 返回数量
            doc_types: 文档类型过滤

        Returns:
            检索结果列表
        """
        # 获取查询向量 (模拟)
        query_embedding = self._get_embedding(query)

        # 查询向量文档
        query_filter = VectorDoc.project_id == project_id
        if doc_types:
            query_filter = VectorDoc.doc_type.in_(doc_types)

        docs = (
            self.db.query(VectorDoc)
            .filter(query_filter)
            .order_by(VectorDoc.created_at.desc())
            .limit(top_k * 2)  # 多查一些用于模拟筛选
            .all()
        )

        # 模拟向量相似度计算
        results = []
        for doc in docs:
            # 简化模拟：基于关键词匹配计算相似度
            similarity = self._calculate_similarity(query, doc.content)
            results.append(
                {
                    "id": doc.id,
                    "doc_type": doc.doc_type,
                    "content": doc.content[:500]
                    + "..."
                    if len(doc.content) > 500
                    else doc.content,
                    "metadata": json.loads(doc.doc_metadata) if doc.doc_metadata else {},
                    "similarity": similarity,
                }
            )

        # 排序并返回 top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def _calculate_similarity(self, query: str, content: str) -> float:
        """
        简化的相似度计算
        实际项目中应该使用向量数据库计算余弦相似度
        """
        query_tokens = set(self._tokenize(query))
        content_tokens = set(self._tokenize(content))

        if not query_tokens:
            return 0.0

        # Jaccard 相似度
        intersection = query_tokens & content_tokens
        union = query_tokens | content_tokens

        return len(intersection) / len(union) if union else 0.0

    def index_document(
        self,
        doc_type: str,
        content: str,
        project_id: int,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        索引文档

        Args:
            doc_type: 文档类型
            content: 文档内容
            project_id: 项目 ID
            metadata: 元数据

        Returns:
            索引结果
        """
        # 分块处理 (简化版，每 500 字符一块)
        chunk_size = 500
        chunks = []
        for i in range(0, len(content), chunk_size):
            chunk = content[i : i + chunk_size]
            chunks.append(chunk)

        indexed_count = 0
        for idx, chunk in enumerate(chunks):
            # 获取或创建 embedding
            embedding = self._get_or_create_embedding(chunk)

            # 创建向量文档
            vector_doc = VectorDoc(
                doc_type=doc_type,
                content=chunk,
                embedding_id=embedding.get("id"),
                doc_metadata=json.dumps(metadata, ensure_ascii=False) if metadata else None,
                chunk_index=idx,
                project_id=project_id,
            )
            self.db.add(vector_doc)
            indexed_count += 1

        self.db.commit()

        return {
            "success": True,
            "indexed_count": indexed_count,
            "chunk_count": len(chunks),
        }

    def _get_or_create_embedding(self, text: str) -> dict:
        """获取或创建 embedding (带缓存)"""
        content_hash = self._compute_hash(text)

        # 检查缓存
        cached = (
            self.db.query(EmbeddingCache)
            .filter(EmbeddingCache.content_hash == content_hash)
            .first()
        )

        if cached:
            return {
                "id": cached.id,
                "embedding": json.loads(cached.embedding),
                "cached": True,
            }

        # 创建新的 embedding (模拟)
        embedding = self._generate_embedding(text)
        content_hash = self._compute_hash(text)

        cache = EmbeddingCache(
            content_hash=content_hash,
            embedding=json.dumps(embedding),
            model="mock-embedding",
        )
        self.db.add(cache)
        self.db.commit()
        self.db.refresh(cache)

        return {
            "id": cache.id,
            "embedding": embedding,
            "cached": False,
        }

    def _get_embedding(self, text: str) -> List[float]:
        """获取文本向量"""
        cached = self._get_or_create_embedding(text)
        return cached.get("embedding", [])

    def _generate_embedding(self, text: str) -> List[float]:
        """
        生成 embedding (模拟)
        实际项目中应该调用 OpenAI Ada 或其他 embedding 模型
        """
        # 简化的模拟：基于文本哈希生成固定维度的随机向量
        import random

        random.seed(hash(text) % (2**32))
        return [random.random() for _ in range(self.EMBEDDING_DIM)]

    def delete_docs_by_project(self, project_id: int) -> int:
        """删除项目的所有向量文档"""
        count = (
            self.db.query(VectorDoc)
            .filter(VectorDoc.project_id == project_id)
            .delete()
        )
        self.db.commit()
        return count

    def get_docs_count(self, project_id: int) -> dict:
        """获取项目的文档统计"""
        from sqlalchemy import func

        results = (
            self.db.query(
                VectorDoc.doc_type, func.count(VectorDoc.id).label("count")
            )
            .filter(VectorDoc.project_id == project_id)
            .group_by(VectorDoc.doc_type)
            .all()
        )

        stats = {doc_type: count for doc_type, count in results}
        stats["total"] = sum(stats.values())

        return stats
