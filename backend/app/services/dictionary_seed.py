# -*- coding: utf-8 -*-
"""字典预置数据初始化"""
from app.models.dictionary import DictType, DictItem


def seed_dictionaries(db):
    """Seed default dictionaries if they don't exist."""

    # 检查是否已有数据，有则跳过
    existing_types = db.query(DictType).count()
    if existing_types > 0:
        return

    # 定义字典类型
    default_types = [
        {
            "code": "priority",
            "name": "优先级",
            "description": "用例优先级",
            "sort_order": 1,
            "items": [
                {"code": "P0", "name": "P0-紧急", "value": "P0", "sort_order": 1, "color": "#F56C6C", "is_default": 0},
                {"code": "P1", "name": "P1-高", "value": "P1", "sort_order": 2, "color": "#E6A23C", "is_default": 0},
                {"code": "P2", "name": "P2-中", "value": "P2", "sort_order": 3, "color": "#409EFF", "is_default": 1},
                {"code": "P3", "name": "P3-低", "value": "P3", "sort_order": 4, "color": "#909399", "is_default": 0},
            ],
        },
        {
            "code": "case_type",
            "name": "用例类型",
            "description": "用例类型分类",
            "sort_order": 2,
            "items": [
                {"code": "api", "name": "接口用例", "value": "api", "sort_order": 1, "color": "#67C23A", "is_default": 1},
                {"code": "functional", "name": "功能用例", "value": "functional", "sort_order": 2, "color": "#909399", "is_default": 0},
            ],
        },
        {
            "code": "tag",
            "name": "标签",
            "description": "用例标签",
            "sort_order": 3,
            "items": [
                {"code": "login", "name": "登录", "value": "login", "sort_order": 1, "color": "#409EFF", "is_default": 0},
                {"code": "payment", "name": "支付", "value": "payment", "sort_order": 2, "color": "#E6A23C", "is_default": 0},
                {"code": "user", "name": "用户", "value": "user", "sort_order": 3, "color": "#67C23A", "is_default": 0},
                {"code": "order", "name": "订单", "value": "order", "sort_order": 4, "color": "#F56C6C", "is_default": 0},
                {"code": "security", "name": "安全", "value": "security", "sort_order": 5, "color": "#9C27B0", "is_default": 0},
                {"code": "performance", "name": "性能", "value": "performance", "sort_order": 6, "color": "#00BCD4", "is_default": 0},
            ],
        },
    ]

    for type_data in default_types:
        type_items = type_data.pop("items")
        existing_type = db.query(DictType).filter(DictType.code == type_data["code"]).first()
        if existing_type:
            continue
        dict_type = DictType(**type_data)
        db.add(dict_type)
        db.flush()

        for item_data in type_items:
            db.add(DictItem(type_id=dict_type.id, **item_data))

    db.commit()
