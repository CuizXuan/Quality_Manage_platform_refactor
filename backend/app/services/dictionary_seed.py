from app.models.dictionary import SystemDictionary


def seed_dictionaries(db):
    """Seed default dictionaries if they don't exist."""

    default_dictionaries = [
        # Priority
        {"category": "priority", "code": "P0", "name": "P0-紧急", "sort_order": 1},
        {"category": "priority", "code": "P1", "name": "P1-高", "sort_order": 2},
        {"category": "priority", "code": "P2", "name": "P2-中", "sort_order": 3},
        {"category": "priority", "code": "P3", "name": "P3-低", "sort_order": 4},
        # Case Type
        {"category": "case_type", "code": "api", "name": "接口用例", "sort_order": 1},
        {"category": "case_type", "code": "functional", "name": "功能用例", "sort_order": 2},
        # Tags
        {"category": "tag", "code": "login", "name": "登录", "sort_order": 1},
        {"category": "tag", "code": "payment", "name": "支付", "sort_order": 2},
        {"category": "tag", "code": "user", "name": "用户", "sort_order": 3},
        {"category": "tag", "code": "order", "name": "订单", "sort_order": 4},
        {"category": "tag", "code": "security", "name": "安全", "sort_order": 5},
        {"category": "tag", "code": "performance", "name": "性能", "sort_order": 6},
    ]

    for item in default_dictionaries:
        existing = db.query(SystemDictionary).filter(
            SystemDictionary.category == item["category"],
            SystemDictionary.code == item["code"],
        ).first()
        if not existing:
            db.add(SystemDictionary(**item))

    db.commit()