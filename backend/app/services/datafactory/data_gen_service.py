# -*- coding: utf-8 -*-
"""
Phase 5 - 测试数据生成服务
"""
import json
import random
import string
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.data_factory_models import DataGenTemplate


class DataGenService:
    """测试数据生成服务"""

    # 内置模板类型
    TEMPLATE_TYPES = {
        "user": "用户",
        "order": "订单",
        "product": "商品",
        "card": "卡片",
    }

    # 内置字段类型生成器
    FIELD_GENERATORS = {
        "id": lambda opts: random.randint(1, 999999),
        "name": lambda opts: random.choice(["张三", "李四", "王五", "赵六", "钱七"]) + str(random.randint(1, 100)),
        "username": lambda opts: f"user{random.randint(1000, 9999)}",
        "email": lambda opts: f"user{random.randint(100, 999)}@example.com",
        "phone": lambda opts: f"138{random.randint(10000000, 99999999)}",
        "mobile": lambda opts: f"+86 138{random.randint(10000000, 99999999)}",
        "age": lambda opts: random.randint(18, 80),
        "gender": lambda opts: random.choice(["M", "F"]),
        "city": lambda opts: random.choice(["北京", "上海", "广州", "深圳", "杭州", "成都"]),
        "address": lambda opts: f"{random.choice(['北京市', '上海市', '广州市'])}{random.choice(['朝阳区', '海淀区', '浦东新区'])}xxx街道{random.randint(1, 999)}号",
        "price": lambda opts: round(random.uniform(10, 10000), 2),
        "quantity": lambda opts: random.randint(1, 100),
        "order_no": lambda opts: f"ORD{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}",
        "product_name": lambda opts: random.choice(["商品A", "商品B", "商品C", "商品D"]) + str(random.randint(1, 50)),
        "sku": lambda opts: f"SKU{random.randint(10000, 99999)}",
        "status": lambda opts: random.choice(["pending", "processing", "completed", "cancelled"]),
        "created_at": lambda opts: datetime.now().isoformat(),
        "updated_at": lambda opts: datetime.now().isoformat(),
        "description": lambda opts: f"这是一段描述文本 {random.randint(1, 1000)}",
        "url": lambda opts: f"https://example.com/{random.randint(1000, 9999)}",
        "ip": lambda opts: f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
        "boolean": lambda opts: random.choice([True, False]),
        "integer": lambda opts: random.randint(1, 1000),
        "float": lambda opts: round(random.uniform(0, 100), 2),
        "string": lambda opts: "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 20))),
        "text": lambda opts: "".join(random.choices(string.ascii_letters + string.digits + " " * 10, k=random.randint(50, 200))),
    }

    def __init__(self, db: Session):
        self.db = db

    def create_template(
        self,
        name: str,
        template_type: str,
        schema: dict,
        project_id: int,
        generation_rules: Optional[dict] = None,
    ) -> dict:
        """创建数据生成模板"""
        if template_type not in self.TEMPLATE_TYPES:
            return {"success": False, "error": f"Invalid template type: {template_type}"}

        template = DataGenTemplate(
            name=name,
            template_type=template_type,
            schema=json.dumps(schema, ensure_ascii=False),
            generation_rules=json.dumps(generation_rules, ensure_ascii=False) if generation_rules else None,
            project_id=project_id,
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        return {"success": True, "id": template.id}

    def update_template(
        self,
        template_id: int,
        name: Optional[str] = None,
        schema: Optional[dict] = None,
        generation_rules: Optional[dict] = None,
    ) -> dict:
        """更新模板"""
        template = self.db.query(DataGenTemplate).filter(DataGenTemplate.id == template_id).first()
        if not template:
            return {"success": False, "error": "Template not found"}

        if name is not None:
            template.name = name
        if schema is not None:
            template.schema = json.dumps(schema, ensure_ascii=False)
        if generation_rules is not None:
            template.generation_rules = json.dumps(generation_rules, ensure_ascii=False)

        self.db.commit()
        return {"success": True}

    def delete_template(self, template_id: int) -> dict:
        """删除模板"""
        template = self.db.query(DataGenTemplate).filter(DataGenTemplate.id == template_id).first()
        if not template:
            return {"success": False, "error": "Template not found"}

        self.db.delete(template)
        self.db.commit()
        return {"success": True}

    def list_templates(self, project_id: int) -> List[dict]:
        """获取模板列表"""
        templates = (
            self.db.query(DataGenTemplate)
            .filter(DataGenTemplate.project_id == project_id)
            .order_by(DataGenTemplate.created_at.desc())
            .all()
        )

        return [self._template_to_dict(t) for t in templates]

    def get_template(self, template_id: int) -> Optional[dict]:
        """获取模板详情"""
        template = self.db.query(DataGenTemplate).filter(DataGenTemplate.id == template_id).first()
        if not template:
            return None
        return self._template_to_dict(template)

    def _template_to_dict(self, template: DataGenTemplate) -> dict:
        """转换模板为字典"""
        return {
            "id": template.id,
            "name": template.name,
            "template_type": template.template_type,
            "template_type_name": self.TEMPLATE_TYPES.get(template.template_type, template.template_type),
            "schema": json.loads(template.schema) if template.schema else {},
            "generation_rules": json.loads(template.generation_rules) if template.generation_rules else None,
            "usage_count": template.usage_count,
            "project_id": template.project_id,
            "created_at": template.created_at.isoformat() if template.created_at else None,
        }

    def generate(self, template_id: int, count: int = 1, unique_fields: Optional[List[str]] = None) -> dict:
        """
        生成测试数据

        Args:
            template_id: 模板 ID
            count: 生成数量
            unique_fields: 需要保证唯一的字段列表

        Returns:
            生成的数据列表
        """
        template = self.get_template(template_id)
        if not template:
            return {"success": False, "error": "Template not found"}

        schema = template["schema"]
        generation_rules = template.get("generation_rules", {}) or {}

        # 更新使用计数
        db_template = self.db.query(DataGenTemplate).filter(DataGenTemplate.id == template_id).first()
        if db_template:
            db_template.usage_count += 1
            self.db.commit()

        # 生成数据
        data = []
        for i in range(count):
            record = self._generate_record(schema, generation_rules)
            data.append(record)

        # 确保唯一性
        if unique_fields:
            data = self._ensure_uniqueness(data, unique_fields)

        return {
            "success": True,
            "count": len(data),
            "data": data,
        }

    def _generate_record(self, schema: dict, rules: dict) -> dict:
        """根据 schema 生成单条记录"""
        record = {}

        for field_name, field_type in schema.items():
            field_rules = rules.get(field_name, {})
            generator = self.FIELD_GENERATORS.get(field_type, self.FIELD_GENERATORS["string"])
            record[field_name] = generator(field_rules)

        return record

    def _ensure_uniqueness(self, data: List[dict], unique_fields: List[str]) -> List[dict]:
        """确保指定字段的唯一性"""
        seen = {field: set() for field in unique_fields}

        for record in data:
            for field in unique_fields:
                if field in record:
                    value = record[field]
                    if value in seen[field]:
                        # 重复了，生成新值
                        record[field] = self._generate_unique_value(field, seen[field])
                    seen[field].add(record[field])

        return data

    def _generate_unique_value(self, field: str, seen: set) -> Any:
        """为已存在的字段生成新的唯一值"""
        generator = self.FIELD_GENERATORS.get(field, self.FIELD_GENERATORS["string"])
        max_attempts = 100

        for _ in range(max_attempts):
            value = generator({})
            if value not in seen:
                seen.add(value)
                return value

        # 如果实在无法生成唯一的，返回原值
        return generator({})

    def preview_template(self, template_id: int) -> dict:
        """预览模板生成的一条数据"""
        result = self.generate(template_id, count=1)
        if result.get("success"):
            return {
                "success": True,
                "preview": result["data"][0] if result["data"] else {},
            }
        return result

    def get_builtin_fields(self) -> dict:
        """获取内置字段类型"""
        return {
            name: desc for name, desc in self.FIELD_GENERATORS.items()
        }
