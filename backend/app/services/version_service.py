# -*- coding: utf-8 -*-
"""
Phase 4 - 版本服务
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from app.models.tenant import Version, Project
from app.services.rbac_service import RBACService


class VersionService:
    """版本服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.rbac_service = RBACService(db)
    
    def get_versions(self, project_id: int, page: int = 1, 
                    page_size: int = 20, status: str = None) -> Tuple[List[Version], int]:
        """获取版本列表"""
        query = self.db.query(Version).filter(Version.project_id == project_id)
        
        if status:
            query = query.filter(Version.status == status)
        
        total = query.count()
        versions = query.order_by(Version.created_at.desc())\
                        .offset((page - 1) * page_size)\
                        .limit(page_size)\
                        .all()
        
        return versions, total
    
    def get_version_by_id(self, version_id: int) -> Optional[Version]:
        """获取版本详情"""
        return self.db.query(Version).filter(Version.id == version_id).first()
    
    def get_version_by_name(self, project_id: int, name: str) -> Optional[Version]:
        """根据名称获取版本"""
        return self.db.query(Version).filter(
            Version.project_id == project_id,
            Version.name == name
        ).first()
    
    def create_version(self, project_id: int, user_id: int,
                      name: str, tag: str = None, commit_hash: str = None,
                      description: str = None, baseline_id: int = None) -> Tuple[Version, bool, str]:
        """
        创建版本
        """
        # 检查项目存在
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None, False, "项目不存在"
        
        # 检查名称唯一性
        existing = self.get_version_by_name(project_id, name)
        if existing:
            return None, False, f"版本名称 '{name}' 已存在"
        
        try:
            version = Version(
                project_id=project_id,
                name=name,
                tag=tag,
                commit_hash=commit_hash,
                description=description,
                baseline_id=baseline_id,
                status="draft"
            )
            self.db.add(version)
            self.db.commit()
            self.db.refresh(version)
            return version, True, ""
        except Exception as e:
            self.db.rollback()
            return None, False, str(e)
    
    def update_version(self, version_id: int, user_id: int,
                     name: str = None, tag: str = None,
                     description: str = None, status: str = None) -> Tuple[Version, bool, str]:
        """
        更新版本
        """
        version = self.get_version_by_id(version_id)
        if not version:
            return None, False, "版本不存在"
        
        # 检查状态转换合法性
        if status:
            if not self._is_valid_status_transition(version.status, status):
                return None, False, f"不支持从 {version.status} 到 {status} 的状态转换"
        
        try:
            if name is not None:
                # 检查新名称唯一性
                existing = self.get_version_by_name(version.project_id, name)
                if existing and existing.id != version_id:
                    return None, False, f"版本名称 '{name}' 已存在"
                version.name = name
            if tag is not None:
                version.tag = tag
            if description is not None:
                version.description = description
            if status is not None:
                version.status = status
                if status == "released":
                    version.released_at = datetime.utcnow()
            
            version.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(version)
            return version, True, ""
        except Exception as e:
            self.db.rollback()
            return None, False, str(e)
    
    def delete_version(self, version_id: int) -> Tuple[bool, str]:
        """删除版本"""
        version = self.get_version_by_id(version_id)
        if not version:
            return False, "版本不存在"
        
        if version.status == "released":
            return False, "无法删除已发布的版本，请先归档"
        
        self.db.delete(version)
        self.db.commit()
        return True, ""
    
    def release_version(self, version_id: int) -> Tuple[Version, bool, str]:
        """发布版本"""
        return self.update_version(version_id, None, status="released")
    
    def archive_version(self, version_id: int) -> Tuple[Version, bool, str]:
        """归档版本"""
        return self.update_version(version_id, None, status="archived")
    
    def bind_quality_report(self, version_id: int, report_data: dict) -> Tuple[Version, bool, str]:
        """绑定质量报告"""
        version = self.get_version_by_id(version_id)
        if not version:
            return None, False, "版本不存在"
        
        try:
            version.quality_report_id = report_data.get("report_id")
            version.test_summary = report_data.get("summary")
            version.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(version)
            return version, True, ""
        except Exception as e:
            self.db.rollback()
            return None, False, str(e)
    
    def get_quality_report(self, version_id: int) -> dict:
        """获取版本质量报告"""
        version = self.get_version_by_id(version_id)
        if not version:
            return None
        
        return {
            "version_id": version.id,
            "version_name": version.name,
            "tag": version.tag,
            "commit_hash": version.commit_hash,
            "test_summary": version.test_summary,
            "status": version.status,
            "released_at": version.released_at.isoformat() if version.released_at else None,
            "created_at": version.created_at.isoformat() if version.created_at else None
        }
    
    def get_version_summary(self, version_id: int) -> dict:
        """获取版本测试摘要"""
        version = self.get_version_by_id(version_id)
        if not version:
            return None
        
        return {
            "id": version.id,
            "name": version.name,
            "status": version.status,
            "test_summary": version.test_summary,
            "created_at": version.created_at.isoformat() if version.created_at else None
        }
    
    def _is_valid_status_transition(self, from_status: str, to_status: str) -> bool:
        """检查状态转换是否合法"""
        valid_transitions = {
            "draft": ["testing", "archived"],
            "testing": ["draft", "released", "archived"],
            "released": ["archived"],
            "archived": []
        }
        return to_status in valid_transitions.get(from_status, [])
    
    def compare_versions(self, version_id1: int, version_id2: int) -> dict:
        """对比两个版本的测试结果"""
        v1 = self.get_version_by_id(version_id1)
        v2 = self.get_version_by_id(version_id2)
        
        if not v1 or not v2:
            return None
        
        summary1 = v1.test_summary or {}
        summary2 = v2.test_summary or {}
        
        return {
            "version1": {
                "id": v1.id,
                "name": v1.name,
                "status": v1.status,
                "summary": summary1
            },
            "version2": {
                "id": v2.id,
                "name": v2.name,
                "status": v2.status,
                "summary": summary2
            },
            "comparison": {
                "pass_rate_diff": self._calc_diff(
                    summary1.get("pass_rate", 0),
                    summary2.get("pass_rate", 0)
                ),
                "coverage_diff": self._calc_diff(
                    summary1.get("coverage", {}).get("line", 0),
                    summary2.get("coverage", {}).get("line", 0)
                )
            }
        }
    
    def _calc_diff(self, val1: float, val2: float) -> float:
        """计算差值"""
        return round(val2 - val1, 2)
