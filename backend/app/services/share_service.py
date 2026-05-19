# -*- coding: utf-8 -*-
"""
Phase 4 - 资产共享服务
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from app.models.tenant import SharedAsset, User, Project, Tenant
import json


class ShareService:
    """资产共享服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_shared_assets(self, tenant_id: int, user_id: int,
                         page: int = 1, page_size: int = 20,
                         asset_type: str = None,
                         keyword: str = None) -> Tuple[List[dict], int]:
        """
        获取共享资产列表
        包括：我收到的共享 + 我发出的共享 + 公开资产
        """
        # 查询条件：收到的共享 或 我发出的共享 或 公开资产
        query = self.db.query(SharedAsset).filter(
            or_(
                SharedAsset.shared_to_tenant_id == tenant_id,  # 收到的共享
                SharedAsset.owner_tenant_id == tenant_id,     # 我发出的共享
                SharedAsset.shared_to_tenant_id == None       # 公开资产
            )
        )
        
        if asset_type:
            query = query.filter(SharedAsset.asset_type == asset_type)
        
        # 排除已过期的
        query = query.filter(
            or_(
                SharedAsset.expires_at == None,
                SharedAsset.expires_at > datetime.utcnow()
            )
        )
        
        total = query.count()
        assets = query.order_by(SharedAsset.created_at.desc())\
                      .offset((page - 1) * page_size)\
                      .limit(page_size)\
                      .all()
        
        # 补充详细信息
        result = []
        for asset in assets:
            asset_dict = self._asset_to_dict(asset)
            # 获取所有者信息
            owner_user = self.db.query(User).filter(User.id == asset.created_by).first()
            if owner_user:
                asset_dict["owner_username"] = owner_user.username
            result.append(asset_dict)
        
        return result, total
    
    def get_received_assets(self, tenant_id: int, project_id: int = None,
                           page: int = 1, page_size: int = 20) -> Tuple[List[dict], int]:
        """获取收到的共享资产"""
        query = self.db.query(SharedAsset).filter(
            SharedAsset.shared_to_tenant_id == tenant_id
        )
        
        if project_id:
            query = query.filter(
                or_(
                    SharedAsset.shared_to_project_id == project_id,
                    SharedAsset.shared_to_project_id == None
                )
            )
        
        # 排除已过期的
        query = query.filter(
            or_(
                SharedAsset.expires_at == None,
                SharedAsset.expires_at > datetime.utcnow()
            )
        )
        
        total = query.count()
        assets = query.order_by(SharedAsset.created_at.desc())\
                      .offset((page - 1) * page_size)\
                      .limit(page_size)\
                      .all()
        
        return [self._asset_to_dict(a) for a in assets], total
    
    def get_sent_assets(self, tenant_id: int, 
                        page: int = 1, page_size: int = 20) -> Tuple[List[dict], int]:
        """获取我发出的共享"""
        query = self.db.query(SharedAsset).filter(
            SharedAsset.owner_tenant_id == tenant_id
        )
        
        total = query.count()
        assets = query.order_by(SharedAsset.created_at.desc())\
                      .offset((page - 1) * page_size)\
                      .limit(page_size)\
                      .all()
        
        result = []
        for asset in assets:
            asset_dict = self._asset_to_dict(asset)
            owner_user = self.db.query(User).filter(User.id == asset.created_by).first()
            if owner_user:
                asset_dict["owner_username"] = owner_user.username
            result.append(asset_dict)
        
        return result, total
    
    def create_share(self, owner_tenant_id: int, owner_project_id: int,
                    user_id: int, asset_type: str, asset_id: int,
                    shared_to_tenant_id: int = None,
                    shared_to_project_id: int = None,
                    permission: str = "read",
                    expires_days: int = None) -> Tuple[SharedAsset, bool, str]:
        """分享资产"""
        # 验证资产存在（这里简化处理，实际应该检查对应类型的资产表）
        if asset_type not in ["case", "scenario", "environment", "template"]:
            return None, False, "不支持的资产类型"
        
        if permission not in ["read", "copy", "execute"]:
            return None, False, "无效的权限类型"
        
        try:
            expires_at = None
            if expires_days and expires_days > 0:
                expires_at = datetime.utcnow() + timedelta(days=expires_days)
            
            share = SharedAsset(
                asset_type=asset_type,
                asset_id=asset_id,
                owner_tenant_id=owner_tenant_id,
                owner_project_id=owner_project_id,
                shared_to_tenant_id=shared_to_tenant_id,
                shared_to_project_id=shared_to_project_id,
                permission=permission,
                created_by=user_id,
                expires_at=expires_at
            )
            self.db.add(share)
            self.db.commit()
            self.db.refresh(share)
            return share, True, ""
        except Exception as e:
            self.db.rollback()
            return None, False, str(e)
    
    def update_share(self, share_id: int, user_id: int,
                    shared_to_tenant_id: int = None,
                    shared_to_project_id: int = None,
                    permission: str = None,
                    expires_days: int = None) -> Tuple[SharedAsset, bool, str]:
        """更新共享"""
        share = self.db.query(SharedAsset).filter(SharedAsset.id == share_id).first()
        if not share:
            return None, False, "共享不存在"
        
        # 验证权限（只有所有者可以更新）
        if share.owner_tenant_id != user_id:
            # 如果是租户ID
            owner_user = self.db.query(User).filter(User.id == share.created_by).first()
            if not owner_user or owner_user.tenant_id != user_id:
                return None, False, "没有权限更新此共享"
        
        try:
            if shared_to_tenant_id is not None:
                share.shared_to_tenant_id = shared_to_tenant_id
            if shared_to_project_id is not None:
                share.shared_to_project_id = shared_to_project_id
            if permission is not None:
                share.permission = permission
            if expires_days is not None:
                if expires_days > 0:
                    share.expires_at = datetime.utcnow() + timedelta(days=expires_days)
                else:
                    share.expires_at = None
            
            self.db.commit()
            self.db.refresh(share)
            return share, True, ""
        except Exception as e:
            self.db.rollback()
            return None, False, str(e)
    
    def delete_share(self, share_id: int, user_id: int) -> Tuple[bool, str]:
        """取消分享"""
        share = self.db.query(SharedAsset).filter(SharedAsset.id == share_id).first()
        if not share:
            return False, "共享不存在"
        
        # 验证权限
        owner_user = self.db.query(User).filter(User.id == share.created_by).first()
        if owner_user and owner_user.tenant_id != user_id:
            return False, "没有权限删除此共享"
        
        self.db.delete(share)
        self.db.commit()
        return True, ""
    
    def import_asset(self, share_id: int, user_id: int, 
                   target_project_id: int) -> Tuple[bool, str]:
        """
        导入共享资产
        根据 asset_type 和 asset_id 从对应表获取资产数据
        创建一份副本到目标项目
        """
        share = self.db.query(SharedAsset).filter(SharedAsset.id == share_id).first()
        if not share:
            return False, "共享不存在"
        
        if share.permission not in ["read", "copy", "execute"]:
            return False, "没有导入权限"
        
        # 检查是否过期
        if share.expires_at and share.expires_at < datetime.utcnow():
            return False, "共享已过期"
        
        try:
            # 根据资产类型处理
            if share.asset_type == "case":
                return self._import_case(share, user_id, target_project_id)
            elif share.asset_type == "scenario":
                return self._import_scenario(share, user_id, target_project_id)
            elif share.asset_type == "environment":
                return self._import_environment(share, user_id, target_project_id)
            elif share.asset_type == "template":
                return self._import_template(share, user_id, target_project_id)
            else:
                return False, "不支持的资产类型"
        except Exception as e:
            return False, f"导入失败: {str(e)}"
    
    def _import_case(self, share, user_id, target_project_id) -> Tuple[bool, str]:
        """导入用例"""
        from app.models.case import TestCase
        original = self.db.query(TestCase).filter(TestCase.id == share.asset_id).first()
        if not original:
            return False, "原始用例不存在"
        
        # 创建副本
        new_case = TestCase(
            project_id=target_project_id,
            name=f"{original.name} (导入)",
            method=original.method,
            path=original.path,
            headers=original.headers,
            params=original.params,
            body=original.body,
            response=original.response,
            status="active",
            created_by=user_id
        )
        self.db.add(new_case)
        self.db.commit()
        return True, f"用例已导入，ID: {new_case.id}"
    
    def _import_scenario(self, share, user_id, target_project_id) -> Tuple[bool, str]:
        """导入场景"""
        from app.models.scenario import Scenario
        original = self.db.query(Scenario).filter(Scenario.id == share.asset_id).first()
        if not original:
            return False, "原始场景不存在"
        
        new_scenario = Scenario(
            project_id=target_project_id,
            name=f"{original.name} (导入)",
            description=original.description,
            steps=original.steps,
            status="active",
            created_by=user_id
        )
        self.db.add(new_scenario)
        self.db.commit()
        return True, f"场景已导入，ID: {new_scenario.id}"
    
    def _import_environment(self, share, user_id, target_project_id) -> Tuple[bool, str]:
        """导入环境"""
        from app.models.environment import Environment
        original = self.db.query(Environment).filter(Environment.id == share.asset_id).first()
        if not original:
            return False, "原始环境不存在"
        
        new_env = Environment(
            project_id=target_project_id,
            name=f"{original.name} (导入)",
            base_url=original.base_url,
            headers=original.headers,
            global_params=original.global_params,
            created_by=user_id
        )
        self.db.add(new_env)
        self.db.commit()
        return True, f"环境已导入，ID: {new_env.id}"
    
    def _import_template(self, share, user_id, target_project_id) -> Tuple[bool, str]:
        """导入模板"""
        from app.models.tenant import AssetTemplate
        original = self.db.query(AssetTemplate).filter(AssetTemplate.id == share.asset_id).first()
        if not original:
            return False, "原始模板不存在"
        
        new_template = AssetTemplate(
            name=f"{original.name} (导入)",
            type=original.type,
            content=original.content,
            description=original.description,
            tags=original.tags,
            tenant_id=target_project_id,
            created_by=user_id
        )
        self.db.add(new_template)
        self.db.commit()
        return True, f"模板已导入，ID: {new_template.id}"
    
    def _asset_to_dict(self, asset: SharedAsset) -> dict:
        """转换资产为字典"""
        return {
            "id": asset.id,
            "asset_type": asset.asset_type,
            "asset_id": asset.asset_id,
            "owner_tenant_id": asset.owner_tenant_id,
            "owner_project_id": asset.owner_project_id,
            "shared_to_tenant_id": asset.shared_to_tenant_id,
            "shared_to_project_id": asset.shared_to_project_id,
            "permission": asset.permission,
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
            "expires_at": asset.expires_at.isoformat() if asset.expires_at else None
        }
