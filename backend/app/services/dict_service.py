# -*- coding: utf-8 -*-
"""字典服务层 - 业务逻辑 + 缓存管理"""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.dictionary import DictType, DictItem
from app.schemas.dictionary import (
    DictTypeCreate,
    DictTypeUpdate,
    DictItemCreate,
    DictItemUpdate,
    DictItemReorderItem,
    PublicDictItem,
    PublicDictType,
    PublicDictResponse,
    PublicAllDictResponse,
)


# ============== 简单内存缓存（可后续替换为 Redis） ==============

class DictCache:
    """字典缓存管理器"""
    _cache: dict[str, list[PublicDictItem]] = {}
    _all_cache: Optional[PublicAllDictResponse] = None

    @classmethod
    def get(cls, type_code: str) -> Optional[list[PublicDictItem]]:
        return cls._cache.get(type_code)

    @classmethod
    def set(cls, type_code: str, items: list[PublicDictItem]) -> None:
        cls._cache[type_code] = items

    @classmethod
    def invalidate(cls, type_code: Optional[str] = None) -> None:
        if type_code:
            cls._cache.pop(type_code, None)
        else:
            cls._cache.clear()
        cls._all_cache = None

    @classmethod
    def get_all(cls) -> Optional[PublicAllDictResponse]:
        return cls._all_cache

    @classmethod
    def set_all(cls, data: PublicAllDictResponse) -> None:
        cls._all_cache = data


# ============== 服务类 ==============

class DictService:

    def __init__(self, db: Session):
        self.db = db

    # -------- DictType CRUD --------

    def list_types(self, page: int = 1, page_size: int = 20, keyword: Optional[str] = None):
        query = self.db.query(DictType)
        if keyword:
            query = query.filter(
                (DictType.code.contains(keyword)) | (DictType.name.contains(keyword))
            )
        total = query.count()
        items = query.order_by(DictType.sort_order.asc(), DictType.id.asc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()
        return items, total

    def get_type(self, type_id: int) -> Optional[DictType]:
        return self.db.query(DictType).filter(DictType.id == type_id).first()

    def get_type_by_code(self, code: str) -> Optional[DictType]:
        return self.db.query(DictType).filter(DictType.code == code).first()

    def create_type(self, data: DictTypeCreate) -> DictType:
        existing = self.get_type_by_code(data.code)
        if existing:
            raise ValueError(f"字典类型编码 {data.code} 已存在")
        item = DictType(**data.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        DictCache.invalidate()  # 全量缓存失效
        return item

    def update_type(self, type_id: int, data: DictTypeUpdate) -> Optional[DictType]:
        item = self.get_type(type_id)
        if not item:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        self.db.commit()
        self.db.refresh(item)
        DictCache.invalidate()  # 全量缓存失效
        return item

    def delete_type(self, type_id: int) -> bool:
        item = self.get_type(type_id)
        if not item:
            return False
        type_code = item.code
        self.db.delete(item)
        self.db.commit()
        DictCache.invalidate(type_code)  # 该类型缓存失效
        return True

    # -------- DictItem CRUD --------

    def list_items(self, page: int = 1, page_size: int = 20, type_id: Optional[int] = None, keyword: Optional[str] = None):
        query = self.db.query(DictItem)
        if type_id is not None:
            query = query.filter(DictItem.type_id == type_id)
        if keyword:
            query = query.filter(
                (DictItem.code.contains(keyword)) | (DictItem.name.contains(keyword))
            )
        total = query.count()
        items = query.order_by(DictItem.sort_order.asc(), DictItem.id.asc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()
        return items, total

    def get_items_by_type_id(self, type_id: int, page: int = 1, page_size: int = 100) -> tuple:
        """获取某类型下的字典项（分页）"""
        return self.list_items(page=page, page_size=page_size, type_id=type_id)

    def get_item(self, item_id: int) -> Optional[DictItem]:
        return self.db.query(DictItem).filter(DictItem.id == item_id).first()

    def create_item(self, data: DictItemCreate) -> DictItem:
        # 检查同类型下编码唯一
        existing = self.db.query(DictItem).filter(
            DictItem.type_id == data.type_id,
            DictItem.code == data.code,
        ).first()
        if existing:
            raise ValueError(f"该类型下字典编码 {data.code} 已存在")

        # 如果 is_default=True，同类型下其他项置为 False
        if data.is_default:
            self.db.query(DictItem).filter(
                DictItem.type_id == data.type_id
            ).update({"is_default": 0})

        item = DictItem(**data.model_dump())
        item.is_default = 1 if data.is_default else 0
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        self._invalidate_type_cache(data.type_id)
        return item

    def update_item(self, item_id: int, data: DictItemUpdate) -> Optional[DictItem]:
        item = self.get_item(item_id)
        if not item:
            return None

        updates = data.model_dump(exclude_unset=True)
        old_type_id = item.type_id

        # 如果设置 is_default=True，同类型下其他项置为 False
        if updates.get("is_default"):
            self.db.query(DictItem).filter(
                DictItem.type_id == item.type_id,
                DictItem.id != item_id,
            ).update({"is_default": 0})

        for key, value in updates.items():
            if key == "is_default":
                setattr(item, key, 1 if value else 0)
            else:
                setattr(item, key, value)

        self.db.commit()
        self.db.refresh(item)

        # 缓存失效
        self._invalidate_type_cache(old_type_id)
        if updates.get("type_id") and updates["type_id"] != old_type_id:
            self._invalidate_type_cache(updates["type_id"])

        return item

    def delete_item(self, item_id: int) -> bool:
        item = self.get_item(item_id)
        if not item:
            return False
        type_id = item.type_id
        self.db.delete(item)
        self.db.commit()
        self._invalidate_type_cache(type_id)
        return True

    def toggle_item_status(self, item_id: int) -> Optional[DictItem]:
        item = self.get_item(item_id)
        if not item:
            return None
        item.status = "disabled" if item.status == "active" else "active"
        self.db.commit()
        self.db.refresh(item)
        self._invalidate_type_cache(item.type_id)
        return item

    def reorder_items(self, items: list[DictItemReorderItem]) -> None:
        """批量更新字典项排序"""
        for reorder_item in items:
            self.db.query(DictItem).filter(DictItem.id == reorder_item.id).update(
                {"sort_order": reorder_item.sort_order}
            )
        self.db.commit()
        # 全量缓存失效（简化处理）
        DictCache.invalidate()

    # -------- 公开查询 API --------

    def get_public_dict(self, type_code: str) -> PublicDictResponse:
        """获取某类型所有启用的字典项（带缓存）"""
        cached = DictCache.get(type_code)
        if cached is not None:
            return PublicDictResponse(items=cached)

        dict_type = self.get_type_by_code(type_code)
        if not dict_type or dict_type.status != "active":
            return PublicDictResponse(items=[])

        items = self.db.query(DictItem).filter(
            DictItem.type_id == dict_type.id,
            DictItem.status == "active",
        ).order_by(DictItem.sort_order.asc()).all()

        public_items = [
            PublicDictItem(
                label=item.name,
                value=item.value or item.code,
                code=item.code,
                color=item.color or "",
                isDefault=bool(item.is_default),
            )
            for item in items
        ]

        DictCache.set(type_code, public_items)
        return PublicDictResponse(items=public_items)

    def get_all_public_dicts(self) -> PublicAllDictResponse:
        """获取所有启用字典（按类型分组，带缓存）"""
        cached = DictCache.get_all()
        if cached is not None:
            return cached

        types = self.db.query(DictType).filter(
            DictType.status == "active"
        ).order_by(DictType.sort_order.asc()).all()

        result_types = []
        for t in types:
            items = self.db.query(DictItem).filter(
                DictItem.type_id == t.id,
                DictItem.status == "active",
            ).order_by(DictItem.sort_order.asc()).all()

            public_items = [
                PublicDictItem(
                    label=item.name,
                    value=item.value or item.code,
                    code=item.code,
                    color=item.color or "",
                    isDefault=bool(item.is_default),
                )
                for item in items
            ]
            result_types.append(PublicDictType(
                code=t.code,
                name=t.name,
                items=public_items,
            ))

        response = PublicAllDictResponse(types=result_types)
        DictCache.set_all(response)
        return response

    # -------- 内部方法 --------

    def _invalidate_type_cache(self, type_id: int) -> None:
        """根据 type_id 找到 type_code 并失效缓存"""
        dict_type = self.db.query(DictType).filter(DictType.id == type_id).first()
        if dict_type:
            DictCache.invalidate(dict_type.code)
        else:
            DictCache.invalidate()
