# -*- coding: utf-8 -*-
"""
Phase 5 - 插件市场服务
"""
import hashlib
import secrets
import re
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from app.models.plugin_models import (
    Plugin, PluginVersion, PluginReview, PluginInstall, CLIKey, CLIUsageLog
)


class PluginMarketplaceService:
    """插件市场服务"""

    CATEGORIES = {
        "executor": "测试执行",
        "assertion": "断言插件",
        "reporter": "报告生成",
        "integration": "集成对接",
    }

    def __init__(self, db: Session):
        self.db = db

    def _generate_slug(self, name: str) -> str:
        """生成 URL 友好的 slug"""
        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        return slug

    def _generate_key_prefix(self) -> str:
        """生成 Key 前缀"""
        return secrets.token_hex(4)

    def _hash_key(self, key: str) -> str:
        """Hash API Key"""
        return hashlib.sha256(key.encode()).hexdigest()

    # ==================== Plugin CRUD ====================

    def list_plugins(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "download_count",
        page: int = 1,
        page_size: int = 20,
    ):
        """获取插件列表"""
        query = self.db.query(Plugin).filter(Plugin.status == "approved")

        if category:
            query = query.filter(Plugin.category == category)

        if search:
            query = query.filter(
                or_(
                    Plugin.name.ilike(f"%{search}%"),
                    Plugin.description.ilike(f"%{search}%"),
                )
            )

        # 排序
        if sort_by == "rating":
            query = query.order_by(desc(Plugin.rating))
        elif sort_by == "recent":
            query = query.order_by(desc(Plugin.created_at))
        else:
            query = query.order_by(desc(Plugin.download_count))

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [self._serialize_plugin(p) for p in items],
        }

    def publish_plugin(self, data: dict, user_id: int) -> dict:
        """发布插件"""
        slug = data.get("slug") or self._generate_slug(data["name"])

        # 检查 slug 唯一性
        existing = self.db.query(Plugin).filter(Plugin.slug == slug).first()
        if existing:
            return {"success": False, "error": "Slug already exists, please use another name"}

        plugin = Plugin(
            name=data["name"],
            slug=slug,
            version=data.get("version", "1.0.0"),
            category=data["category"],
            description=data.get("description"),
            author=data.get("author"),
            author_url=data.get("author_url"),
            homepage=data.get("homepage"),
            license=data.get("license", "MIT"),
            tags=data.get("tags", []),
            requirements=data.get("requirements", {}),
            config_schema=data.get("config_schema"),
            manifest=data.get("manifest"),
            readme=data.get("readme"),
            status="pending",
            created_by=user_id,
        )

        self.db.add(plugin)
        self.db.commit()
        self.db.refresh(plugin)

        # 创建初始版本
        version = PluginVersion(
            plugin_id=plugin.id,
            version=plugin.version,
            release_notes="Initial release",
            created_at=datetime.now(),
        )
        self.db.add(version)
        self.db.commit()

        return {
            "success": True,
            "plugin_id": plugin.id,
            "message": "Plugin submitted for review",
        }

    def get_plugin(self, plugin_id: int) -> Optional[dict]:
        """获取插件详情"""
        plugin = self.db.query(Plugin).filter(Plugin.id == plugin_id).first()
        if not plugin:
            return None

        result = self._serialize_plugin(plugin)

        # 获取版本历史
        versions = self.db.query(PluginVersion).filter(
            PluginVersion.plugin_id == plugin_id
        ).order_by(PluginVersion.created_at.desc()).all()
        result["versions"] = [
            {"version": v.version, "created_at": v.created_at.isoformat() if v.created_at else None}
            for v in versions
        ]

        # 获取安装数量
        install_count = self.db.query(PluginInstall).filter(
            PluginInstall.plugin_id == plugin_id
        ).count()
        result["install_count"] = install_count

        return result

    def update_plugin(self, plugin_id: int, data: dict, user_id: int) -> dict:
        """更新插件"""
        plugin = self.db.query(Plugin).filter(
            Plugin.id == plugin_id,
            Plugin.created_by == user_id,
        ).first()

        if not plugin:
            return {"success": False, "error": "Plugin not found or not authorized"}

        # 更新字段
        for field in ["name", "description", "version", "tags", "readme", "homepage"]:
            if field in data:
                setattr(plugin, field, data[field])

        plugin.updated_at = datetime.now()

        # 如果有新版本
        if data.get("version") and data["version"] != plugin.version:
            new_version = PluginVersion(
                plugin_id=plugin_id,
                version=data["version"],
                release_notes=data.get("changelog", ""),
            )
            self.db.add(new_version)

        self.db.commit()
        return {"success": True, "plugin_id": plugin_id}

    def delete_plugin(self, plugin_id: int, user_id: int) -> dict:
        """删除插件"""
        plugin = self.db.query(Plugin).filter(
            Plugin.id == plugin_id,
            Plugin.created_by == user_id,
        ).first()

        if not plugin:
            return {"success": False, "error": "Plugin not found or not authorized"}

        self.db.delete(plugin)
        self.db.commit()
        return {"success": True}

    # ==================== Install/Uninstall ====================

    def install_plugin(
        self,
        plugin_id: int,
        user_id: int,
        project_id: Optional[int] = None,
        version: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> dict:
        """安装插件"""
        # 检查是否已安装
        existing = self.db.query(PluginInstall).filter(
            PluginInstall.plugin_id == plugin_id,
            PluginInstall.user_id == user_id,
        ).first()

        if existing:
            # 更新配置
            if config:
                existing.config = config
            if version:
                existing.version = version
            existing.updated_at = datetime.now()
            self.db.commit()
            return {"success": True, "install_id": existing.id, "updated": True}

        install = PluginInstall(
            plugin_id=plugin_id,
            user_id=user_id,
            project_id=project_id,
            version=version,
            config=config,
        )
        self.db.add(install)

        # 增加安装计数
        plugin = self.db.query(Plugin).filter(Plugin.id == plugin_id).first()
        if plugin:
            plugin.install_count = (plugin.install_count or 0) + 1

        self.db.commit()
        return {"success": True, "install_id": install.id, "updated": False}

    def uninstall_plugin(self, plugin_id: int, user_id: int) -> dict:
        """卸载插件"""
        install = self.db.query(PluginInstall).filter(
            PluginInstall.plugin_id == plugin_id,
            PluginInstall.user_id == user_id,
        ).first()

        if not install:
            return {"success": False, "error": "Not installed"}

        self.db.delete(install)
        self.db.commit()
        return {"success": True}

    def get_my_plugins(self, user_id: int) -> dict:
        """获取我的插件（已安装）"""
        installs = self.db.query(PluginInstall).filter(
            PluginInstall.user_id == user_id
        ).all()

        items = []
        for install in installs:
            plugin = self.db.query(Plugin).filter(Plugin.id == install.plugin_id).first()
            if plugin:
                item = self._serialize_plugin(plugin)
                item["installed_version"] = install.version
                item["installed_config"] = install.config
                item["installed_at"] = install.created_at.isoformat() if install.created_at else None
                items.append(item)

        return {"items": items, "total": len(items)}

    def get_my_published(self, user_id: int) -> dict:
        """获取我发布的插件"""
        plugins = self.db.query(Plugin).filter(Plugin.created_by == user_id).all()
        return {
            "items": [self._serialize_plugin(p) for p in plugins],
            "total": len(plugins),
        }

    # ==================== Reviews ====================

    def get_reviews(self, plugin_id: int, page: int = 1, page_size: int = 20) -> dict:
        """获取插件评论"""
        query = self.db.query(PluginReview).filter(
            PluginReview.plugin_id == plugin_id,
            PluginReview.status == "approved",
        ).order_by(desc(PluginReview.created_at))

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "rating": r.rating,
                    "title": r.title,
                    "content": r.content,
                    "pros": r.pros,
                    "cons": r.cons,
                    "is_verified_purchase": r.is_verified_purchase,
                    "helpful_count": r.helpful_count,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in items
            ],
        }

    def create_review(
        self,
        plugin_id: int,
        user_id: int,
        rating: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        pros: Optional[str] = None,
        cons: Optional[str] = None,
    ) -> dict:
        """评论插件"""
        # 检查是否已评论
        existing = self.db.query(PluginReview).filter(
            PluginReview.plugin_id == plugin_id,
            PluginReview.user_id == user_id,
        ).first()

        if existing:
            # 更新评论
            existing.rating = rating
            existing.title = title
            existing.content = content
            existing.pros = pros
            existing.cons = cons
        else:
            review = PluginReview(
                plugin_id=plugin_id,
                user_id=user_id,
                rating=rating,
                title=title,
                content=content,
                pros=pros,
                cons=cons,
            )
            self.db.add(review)

        # 更新插件评分
        plugin = self.db.query(Plugin).filter(Plugin.id == plugin_id).first()
        if plugin:
            reviews = self.db.query(PluginReview).filter(
                PluginReview.plugin_id == plugin_id,
                PluginReview.status == "approved",
            ).all()
            total_rating = sum(r.rating for r in reviews) + rating
            plugin.rating_count = len(reviews) + 1
            plugin.rating = total_rating / plugin.rating_count

        self.db.commit()
        return {"success": True}

    # ==================== CLI Keys ====================

    def create_cli_key(
        self,
        user_id: int,
        name: str,
        permissions: List[str] = None,
        expires_in_days: Optional[int] = None,
    ) -> dict:
        """创建 CLI Key"""
        raw_key = f"qc_{secrets.token_hex(24)}"
        key_hash = self._hash_key(raw_key)
        key_prefix = raw_key[:10]

        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        cli_key = CLIKey(
            user_id=user_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            permissions=permissions or ["read"],
            expires_at=expires_at,
        )
        self.db.add(cli_key)
        self.db.commit()

        return {
            "success": True,
            "key_id": cli_key.id,
            "api_key": raw_key,  # 只返回一次，之后不再展示
            "key_prefix": key_prefix,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }

    def validate_cli_key(self, api_key: str) -> dict:
        """验证 CLI Key（模拟）"""
        if not api_key or len(api_key) < 10:
            return {"success": False, "error": "Invalid key format"}

        # 查找 key
        key_hash = self._hash_key(api_key)
        cli_key = self.db.query(CLIKey).filter(
            CLIKey.key_hash == key_hash,
            CLIKey.is_active == True,
        ).first()

        if not cli_key:
            return {"success": False, "error": "Key not found or inactive"}

        if cli_key.expires_at and cli_key.expires_at < datetime.now():
            return {"success": False, "error": "Key expired"}

        # 更新最后使用时间
        cli_key.last_used_at = datetime.now()

        # 记录使用日志
        log = CLIUsageLog(
            cli_key_id=cli_key.id,
            endpoint="/api/cli/auth/token",
            method="POST",
            status_code=200,
        )
        self.db.add(log)
        self.db.commit()

        return {
            "success": True,
            "token": f"bearer_{secrets.token_hex(32)}",
            "permissions": cli_key.permissions,
            "expires_in": 3600,
        }

    def list_cli_keys(self, user_id: int) -> dict:
        """列出 CLI Keys"""
        keys = self.db.query(CLIKey).filter(CLIKey.user_id == user_id).all()
        return {
            "items": [
                {
                    "id": k.id,
                    "name": k.name,
                    "key_prefix": k.key_prefix,
                    "permissions": k.permissions,
                    "rate_limit": k.rate_limit,
                    "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                    "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                    "is_active": k.is_active,
                    "created_at": k.created_at.isoformat() if k.created_at else None,
                }
                for k in keys
            ]
        }

    def delete_cli_key(self, key_id: int, user_id: int) -> dict:
        """删除 CLI Key"""
        cli_key = self.db.query(CLIKey).filter(
            CLIKey.id == key_id,
            CLIKey.user_id == user_id,
        ).first()

        if not cli_key:
            return {"success": False, "error": "Key not found or not authorized"}

        self.db.delete(cli_key)
        self.db.commit()
        return {"success": True}

    # ==================== Categories ====================

    def get_categories(self) -> dict:
        """获取分类统计"""
        categories = []
        for cat_key, cat_name in self.CATEGORIES.items():
            count = self.db.query(Plugin).filter(
                Plugin.category == cat_key,
                Plugin.status == "approved",
            ).count()
            categories.append({
                "key": cat_key,
                "name": cat_name,
                "count": count,
            })
        return {"categories": categories}

    # ==================== Helpers ====================

    def _serialize_plugin(self, plugin: Plugin) -> dict:
        """序列化插件对象"""
        return {
            "id": plugin.id,
            "name": plugin.name,
            "slug": plugin.slug,
            "version": plugin.version,
            "category": plugin.category,
            "description": plugin.description,
            "author": plugin.author,
            "author_url": plugin.author_url,
            "homepage": plugin.homepage,
            "license": plugin.license,
            "price": plugin.price,
            "rating": plugin.rating,
            "rating_count": plugin.rating_count,
            "download_count": plugin.download_count,
            "install_count": plugin.install_count or 0,
            "is_official": plugin.is_official,
            "is_verified": plugin.is_verified,
            "is_premium": plugin.is_premium,
            "tags": plugin.tags or [],
            "requirements": plugin.requirements or {},
            "config_schema": plugin.config_schema,
            "readme": plugin.readme,
            "logo_url": plugin.logo_url,
            "status": plugin.status,
            "created_by": plugin.created_by,
            "published_at": plugin.published_at.isoformat() if plugin.published_at else None,
            "created_at": plugin.created_at.isoformat() if plugin.created_at else None,
            "updated_at": plugin.updated_at.isoformat() if plugin.updated_at else None,
        }
