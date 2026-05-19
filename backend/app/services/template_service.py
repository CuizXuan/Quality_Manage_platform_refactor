# -*- coding: utf-8 -*-
"""
Phase 4 - 资产模板服务
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from app.models.tenant import AssetTemplate, User
import json


class TemplateService:
    """资产模板服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_templates(self, tenant_id: int,
                     page: int = 1, page_size: int = 20,
                     template_type: str = None,
                     keyword: str = None,
                     include_public: bool = True) -> Tuple[List[dict], int]:
        """
        获取模板列表
        包括：系统模板 + 租户模板 + 公开模板
        """
        query = self.db.query(AssetTemplate).filter(
            or_(
                AssetTemplate.tenant_id == tenant_id,  # 租户自己的模板
                AssetTemplate.tenant_id == None,         # 系统模板
                AssetTemplate.is_public == True          # 公开模板
            )
        )
        
        if template_type:
            query = query.filter(AssetTemplate.type == template_type)
        
        if keyword:
            query = query.filter(
                or_(
                    AssetTemplate.name.ilike(f"%{keyword}%"),
                    AssetTemplate.description.ilike(f"%{keyword}%")
                )
            )
        
        total = query.count()
        templates = query.order_by(AssetTemplate.usage_count.desc(),
                                   AssetTemplate.created_at.desc())\
                        .offset((page - 1) * page_size)\
                        .limit(page_size)\
                        .all()
        
        return [self._template_to_dict(t) for t in templates], total
    
    def get_template_market(self, page: int = 1, page_size: int = 20,
                           template_type: str = None,
                           keyword: str = None) -> Tuple[List[dict], int]:
        """获取模板市场（只显示公开模板）"""
        query = self.db.query(AssetTemplate).filter(
            or_(
                AssetTemplate.is_public == True,
                AssetTemplate.tenant_id == None  # 系统模板
            )
        )
        
        if template_type:
            query = query.filter(AssetTemplate.type == template_type)
        
        if keyword:
            query = query.filter(
                or_(
                    AssetTemplate.name.ilike(f"%{keyword}%"),
                    AssetTemplate.description.ilike(f"%{keyword}%")
                )
            )
        
        total = query.count()
        templates = query.order_by(AssetTemplate.usage_count.desc())\
                        .offset((page - 1) * page_size)\
                        .limit(page_size)\
                        .all()
        
        return [self._template_to_dict(t) for t in templates], total
    
    def get_my_templates(self, tenant_id: int,
                         page: int = 1, page_size: int = 20) -> Tuple[List[dict], int]:
        """获取我的模板（租户自己的模板）"""
        query = self.db.query(AssetTemplate).filter(
            AssetTemplate.tenant_id == tenant_id
        )
        
        total = query.count()
        templates = query.order_by(AssetTemplate.created_at.desc())\
                        .offset((page - 1) * page_size)\
                        .limit(page_size)\
                        .all()
        
        return [self._template_to_dict(t) for t in templates], total
    
    def get_template_by_id(self, template_id: int) -> Optional[dict]:
        """获取模板详情"""
        template = self.db.query(AssetTemplate).filter(
            AssetTemplate.id == template_id
        ).first()
        
        if not template:
            return None
        
        return self._template_to_dict(template)
    
    def create_template(self, tenant_id: int, user_id: int,
                      name: str, template_type: str, content: dict,
                      description: str = None, tags: list = None,
                      is_public: bool = False) -> Tuple[AssetTemplate, bool, str]:
        """创建模板"""
        if template_type not in ["case", "scenario", "report", "environment"]:
            return None, False, "不支持的模板类型"
        
        try:
            template = AssetTemplate(
                name=name,
                type=template_type,
                content=json.dumps(content, ensure_ascii=False),
                description=description,
                tags=json.dumps(tags, ensure_ascii=False) if tags else None,
                tenant_id=tenant_id,
                created_by=user_id,
                is_public=is_public
            )
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)
            return template, True, ""
        except Exception as e:
            self.db.rollback()
            return None, False, str(e)
    
    def update_template(self, template_id: int, user_id: int,
                       name: str = None, description: str = None,
                       content: dict = None, tags: list = None,
                       is_public: bool = None) -> Tuple[AssetTemplate, bool, str]:
        """更新模板"""
        template = self.db.query(AssetTemplate).filter(
            AssetTemplate.id == template_id
        ).first()
        
        if not template:
            return None, False, "模板不存在"
        
        # 检查权限
        if template.tenant_id and template.tenant_id != user_id:
            # 如果是租户ID
            owner_user = self.db.query(User).filter(User.id == template.created_by).first()
            if not owner_user or owner_user.tenant_id != user_id:
                return None, False, "没有权限修改此模板"
        
        try:
            if name is not None:
                template.name = name
            if description is not None:
                template.description = description
            if content is not None:
                template.content = json.dumps(content, ensure_ascii=False)
            if tags is not None:
                template.tags = json.dumps(tags, ensure_ascii=False)
            if is_public is not None:
                template.is_public = is_public
            
            template.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(template)
            return template, True, ""
        except Exception as e:
            self.db.rollback()
            return None, False, str(e)
    
    def delete_template(self, template_id: int, user_id: int) -> Tuple[bool, str]:
        """删除模板"""
        template = self.db.query(AssetTemplate).filter(
            AssetTemplate.id == template_id
        ).first()
        
        if not template:
            return False, "模板不存在"
        
        # 检查权限
        if template.tenant_id:
            owner_user = self.db.query(User).filter(User.id == template.created_by).first()
            if not owner_user or owner_user.tenant_id != user_id:
                return False, "没有权限删除此模板"
        
        # 系统模板不能删除
        if template.tenant_id is None:
            return False, "系统模板不能删除"
        
        self.db.delete(template)
        self.db.commit()
        return True, ""
    
    def use_template(self, template_id: int) -> Tuple[dict, bool, str]:
        """
        使用模板创建资产
        返回模板内容供调用者创建资产
        """
        template = self.db.query(AssetTemplate).filter(
            AssetTemplate.id == template_id
        ).first()
        
        if not template:
            return None, False, "模板不存在"
        
        # 增加使用次数
        template.usage_count = (template.usage_count or 0) + 1
        self.db.commit()
        
        try:
            content = json.loads(template.content) if isinstance(template.content, str) else template.content
            return {
                "id": template.id,
                "name": template.name,
                "type": template.type,
                "content": content,
                "description": template.description
            }, True, ""
        except json.JSONDecodeError:
            return None, False, "模板内容解析失败"
    
    def _template_to_dict(self, template: AssetTemplate) -> dict:
        """转换模板为字典"""
        try:
            content = json.loads(template.content) if isinstance(template.content, str) else template.content
        except:
            content = template.content
        
        try:
            tags = json.loads(template.tags) if isinstance(template.tags, str) else template.tags
        except:
            tags = template.tags or []
        
        return {
            "id": template.id,
            "name": template.name,
            "type": template.type,
            "content": content,
            "description": template.description,
            "tags": tags,
            "icon": template.icon,
            "usage_count": template.usage_count or 0,
            "tenant_id": template.tenant_id,
            "is_public": template.is_public,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None
        }
