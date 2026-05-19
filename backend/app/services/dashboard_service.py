# -*- coding: utf-8 -*-
"""
Phase 4 - 仪表盘服务
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.tenant import Dashboard, DashboardWidget
import json


class DashboardService:
    """仪表盘服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboards(self, owner_id: int = None, 
                     dashboard_type: str = None) -> List[dict]:
        """获取仪表盘列表"""
        query = self.db.query(Dashboard)
        
        if owner_id:
            query = query.filter(Dashboard.owner_id == owner_id)
        if dashboard_type:
            query = query.filter(Dashboard.type == dashboard_type)
        
        dashboards = query.order_by(Dashboard.is_default.desc(), 
                                     Dashboard.created_at.desc()).all()
        return [self._dashboard_to_dict(d) for d in dashboards]
    
    def get_dashboard_by_id(self, dashboard_id: int) -> Optional[dict]:
        """获取仪表盘详情"""
        dashboard = self.db.query(Dashboard).filter(
            Dashboard.id == dashboard_id
        ).first()
        
        if not dashboard:
            return None
        
        result = self._dashboard_to_dict(dashboard)
        # 获取组件
        widgets = self.db.query(DashboardWidget).filter(
            DashboardWidget.dashboard_id == dashboard_id
        ).order_by(DashboardWidget.created_at).all()
        result["widgets"] = [self._widget_to_dict(w) for w in widgets]
        return result
    
    def create_dashboard(self, name: str, dashboard_type: str,
                       owner_id: int = None, 
                       layout_config: dict = None) -> Tuple[Dashboard, bool, str]:
        """创建仪表盘"""
        try:
            # 如果是第一个仪表盘，设为默认
            existing = self.db.query(Dashboard).filter(
                Dashboard.owner_id == owner_id if owner_id else Dashboard.owner_id.is_(None)
            ).count()
            is_default = existing == 0
            
            dashboard = Dashboard(
                name=name,
                type=dashboard_type,
                owner_id=owner_id,
                is_default=is_default,
                layout_config=json.dumps(layout_config or {})
            )
            self.db.add(dashboard)
            self.db.commit()
            self.db.refresh(dashboard)
            return dashboard, True, ""
        except Exception as e:
            self.db.rollback()
            return None, False, str(e)
    
    def update_dashboard(self, dashboard_id: int,
                       name: str = None,
                       layout_config: dict = None,
                       is_default: bool = None) -> Tuple[Dashboard, bool, str]:
        """更新仪表盘"""
        dashboard = self.db.query(Dashboard).filter(
            Dashboard.id == dashboard_id
        ).first()
        
        if not dashboard:
            return None, False, "仪表盘不存在"
        
        try:
            if name is not None:
                dashboard.name = name
            if layout_config is not None:
                dashboard.layout_config = json.dumps(layout_config)
            if is_default is not None:
                if is_default:
                    # 取消其他默认
                    self.db.query(Dashboard).filter(
                        Dashboard.owner_id == dashboard.owner_id,
                        Dashboard.id != dashboard_id
                    ).update({"is_default": False})
                dashboard.is_default = is_default
            
            dashboard.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(dashboard)
            return dashboard, True, ""
        except Exception as e:
            self.db.rollback()
            return None, False, str(e)
    
    def delete_dashboard(self, dashboard_id: int) -> Tuple[bool, str]:
        """删除仪表盘"""
        dashboard = self.db.query(Dashboard).filter(
            Dashboard.id == dashboard_id
        ).first()
        
        if not dashboard:
            return False, "仪表盘不存在"
        
        if dashboard.is_default:
            return False, "不能删除默认仪表盘"
        
        # 删除关联组件
        self.db.query(DashboardWidget).filter(
            DashboardWidget.dashboard_id == dashboard_id
        ).delete()
        
        self.db.delete(dashboard)
        self.db.commit()
        return True, ""
    
    # ==================== 组件管理 ====================
    
    def get_widgets(self, dashboard_id: int) -> List[dict]:
        """获取仪表盘组件"""
        widgets = self.db.query(DashboardWidget).filter(
            DashboardWidget.dashboard_id == dashboard_id
        ).order_by(DashboardWidget.created_at).all()
        return [self._widget_to_dict(w) for w in widgets]
    
    def add_widget(self, dashboard_id: int, widget_type: str,
                  title: str = None, config: dict = None,
                  position: dict = None) -> Tuple[DashboardWidget, bool, str]:
        """添加组件"""
        dashboard = self.db.query(Dashboard).filter(
            Dashboard.id == dashboard_id
        ).first()
        
        if not dashboard:
            return None, False, "仪表盘不存在"
        
        try:
            widget = DashboardWidget(
                dashboard_id=dashboard_id,
                widget_type=widget_type,
                title=title or widget_type,
                config=json.dumps(config or {}),
                position=json.dumps(position or {"x": 0, "y": 0, "w": 4, "h": 3}),
                refresh_interval=60
            )
            self.db.add(widget)
            self.db.commit()
            self.db.refresh(widget)
            return widget, True, ""
        except Exception as e:
            self.db.rollback()
            return None, False, str(e)
    
    def update_widget(self, widget_id: int,
                    title: str = None, config: dict = None,
                    position: dict = None,
                    refresh_interval: int = None) -> Tuple[DashboardWidget, bool, str]:
        """更新组件"""
        widget = self.db.query(DashboardWidget).filter(
            DashboardWidget.id == widget_id
        ).first()
        
        if not widget:
            return None, False, "组件不存在"
        
        try:
            if title is not None:
                widget.title = title
            if config is not None:
                widget.config = json.dumps(config)
            if position is not None:
                widget.position = json.dumps(position)
            if refresh_interval is not None:
                widget.refresh_interval = refresh_interval
            
            self.db.commit()
            self.db.refresh(widget)
            return widget, True, ""
        except Exception as e:
            self.db.rollback()
            return None, False, str(e)
    
    def delete_widget(self, widget_id: int) -> Tuple[bool, str]:
        """删除组件"""
        widget = self.db.query(DashboardWidget).filter(
            DashboardWidget.id == widget_id
        ).first()
        
        if not widget:
            return False, "组件不存在"
        
        self.db.delete(widget)
        self.db.commit()
        return True, ""
    
    def _dashboard_to_dict(self, dashboard: Dashboard) -> dict:
        if not dashboard:
            return None
        try:
            layout_config = json.loads(dashboard.layout_config) if isinstance(dashboard.layout_config, str) else (dashboard.layout_config or {})
        except:
            layout_config = {}
        
        return {
            "id": dashboard.id,
            "name": dashboard.name,
            "type": dashboard.type,
            "owner_id": dashboard.owner_id,
            "is_default": dashboard.is_default,
            "layout_config": layout_config,
            "created_at": dashboard.created_at.isoformat() if dashboard.created_at else None,
            "updated_at": dashboard.updated_at.isoformat() if dashboard.updated_at else None
        }
    
    def _widget_to_dict(self, widget: DashboardWidget) -> dict:
        if not widget:
            return None
        try:
            config = json.loads(widget.config) if isinstance(widget.config, str) else (widget.config or {})
            position = json.loads(widget.position) if isinstance(widget.position, str) else (widget.position or {})
        except:
            config, position = {}, {}
        
        return {
            "id": widget.id,
            "dashboard_id": widget.dashboard_id,
            "widget_type": widget.widget_type,
            "title": widget.title,
            "config": config,
            "position": position,
            "refresh_interval": widget.refresh_interval,
            "created_at": widget.created_at.isoformat() if widget.created_at else None
        }


class OpenAPIService:
    """开放API服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_api_endpoints(self) -> List[dict]:
        """获取可用API端点列表"""
        endpoints = [
            {
                "path": "/api/cases",
                "method": "GET",
                "description": "获取用例列表",
                "category": "用例管理"
            },
            {
                "path": "/api/cases",
                "method": "POST",
                "description": "创建用例",
                "category": "用例管理"
            },
            {
                "path": "/api/cases/{id}",
                "method": "GET",
                "description": "获取用例详情",
                "category": "用例管理"
            },
            {
                "path": "/api/cases/{id}",
                "method": "PUT",
                "description": "更新用例",
                "category": "用例管理"
            },
            {
                "path": "/api/cases/{id}",
                "method": "DELETE",
                "description": "删除用例",
                "category": "用例管理"
            },
            {
                "path": "/api/scenarios",
                "method": "GET",
                "description": "获取场景列表",
                "category": "场景管理"
            },
            {
                "path": "/api/scenarios",
                "method": "POST",
                "description": "创建场景",
                "category": "场景管理"
            },
            {
                "path": "/api/projects",
                "method": "GET",
                "description": "获取项目列表",
                "category": "项目管理"
            },
            {
                "path": "/api/projects",
                "method": "POST",
                "description": "创建项目",
                "category": "项目管理"
            },
            {
                "path": "/api/executions",
                "method": "POST",
                "description": "触发执行",
                "category": "执行管理"
            },
            {
                "path": "/api/executions/{id}",
                "method": "GET",
                "description": "获取执行结果",
                "category": "执行管理"
            },
            {
                "path": "/api/reports",
                "method": "GET",
                "description": "获取测试报告",
                "category": "报告管理"
            },
            {
                "path": "/api/auth/me",
                "method": "GET",
                "description": "获取当前用户信息",
                "category": "认证"
            }
        ]
        return endpoints
    
    def validate_api_key(self, api_key: str) -> Tuple[bool, dict]:
        """
        验证API Key
        简化版：实际应该查询数据库中的api_keys表
        """
        # 简化：所有以 "sk-" 开头的key都有效
        if api_key.startswith("sk-"):
            return True, {
                "key_id": "demo",
                "tenant_id": 1,
                "permissions": ["read", "write"],
                "rate_limit": 1000
            }
        return False, {"error": "无效的API Key"}
