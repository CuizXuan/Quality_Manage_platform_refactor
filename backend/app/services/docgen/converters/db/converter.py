"""
数据库转换器 — 将 SQLite 表结构转为 LeafData
从 doc-generator 迁入（精简版，仅保留 SQLite）
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict

from app.services.docgen.datamodel import LeafData, FlowRow


@dataclass
class TableInfo:
    name: str
    comment: str = ""
    columns: List["ColumnInfo"] = field(default_factory=list)
    indexes: List["IndexInfo"] = field(default_factory=list)
    foreign_keys: list = field(default_factory=list)


@dataclass
class ColumnInfo:
    name: str
    dtype: str
    length: Optional[int] = None
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False
    comment: str = ""


@dataclass
class IndexInfo:
    name: str
    columns: List[str]
    unique: bool = False
    index_type: str = "BTREE"


class DbConnectorBase:
    """数据库连接基类"""

    def get_tables(self) -> List[str]:
        raise NotImplementedError

    def get_table_info(self, table_name: str) -> TableInfo:
        raise NotImplementedError


class SqliteConnector(DbConnectorBase):
    """SQLite 连接器"""

    def __init__(self, db_path: str):
        import sqlite3
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row

    def get_tables(self) -> List[str]:
        cursor = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row[0] for row in cursor.fetchall()]

    def get_table_info(self, table_name: str) -> TableInfo:
        # 获取列信息
        cursor = self._conn.execute(f"PRAGMA table_info('{table_name}')")
        columns = []
        for row in cursor.fetchall():
            col = ColumnInfo(
                name=row["name"],
                dtype=row["type"].upper(),
                length=None,
                nullable=not bool(row["notnull"]),
                default=row["dflt_value"],
                primary_key=bool(row["pk"]),
            )
            columns.append(col)

        # 获取索引信息
        idx_cursor = self._conn.execute(f"PRAGMA index_list('{table_name}')")
        indexes = []
        for row in idx_cursor.fetchall():
            idx_name = row["name"]
            idx_info_cursor = self._conn.execute(f"PRAGMA index_info('{idx_name}')")
            idx_cols = [r["name"] for r in idx_info_cursor.fetchall()]
            indexes.append(IndexInfo(
                name=idx_name,
                columns=idx_cols,
                unique=bool(row["unique"]),
            ))

        return TableInfo(name=table_name, columns=columns, indexes=indexes)


class DbConverter:
    """数据库转换器"""

    def __init__(self, connector: DbConnectorBase, table_names: Optional[List[str]] = None):
        self.connector = connector
        self._table_names = table_names

    def get_tables(self) -> list[str]:
        if self._table_names:
            return self._table_names
        return self.connector.get_tables()

    def to_leaf_data(self, table_name: str) -> LeafData:
        info = self.connector.get_table_info(table_name)
        return LeafData(
            desc=self._build_desc(info),
            flow=self._build_flow(info),
        )

    def to_leaf_datas(self, table_names: Optional[List[str]] = None) -> Dict[str, LeafData]:
        if table_names is None:
            table_names = self.get_tables()
        return {name: self.to_leaf_data(name) for name in table_names}

    def _build_desc(self, info: TableInfo) -> str:
        lines = [f"表名: {info.name}"]
        if info.comment:
            lines.append(f"说明: {info.comment}")
        lines.append(f"字段数: {len(info.columns)}")
        pk_count = sum(1 for c in info.columns if c.primary_key)
        lines.append(f"主键: {pk_count}")
        lines.append(f"索引: {len(info.indexes)}")
        return "\n".join(lines)

    def _build_flow(self, info: TableInfo) -> List[FlowRow]:
        rows = []
        for col in info.columns:
            col_type = col.dtype
            if col.length:
                col_type = f"{col.dtype}({col.length})"

            comment = col.comment or ""
            flags = []
            if col.primary_key:
                flags.append("PK")
            if not col.nullable:
                flags.append("NOT NULL")
            if col.default is not None:
                flags.append(f"DEFAULT {col.default}")

            constraint = " ".join(flags)
            rows.append(FlowRow(
                action=f"{col.name}  {col_type}",
                response=f"{constraint}  {comment}".strip(),
            ))

        for idx in info.indexes:
            rows.append(FlowRow(
                action=f"索引: {idx.name}",
                response=f"字段: {', '.join(idx.columns)}  {'UNIQUE' if idx.unique else ''}  {idx.index_type}",
            ))

        return rows