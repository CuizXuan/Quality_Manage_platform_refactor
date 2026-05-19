from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class DataSet(Base):
    __tablename__ = "data_set"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, nullable=False, default=1)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    type = Column(String(10), default="csv")  # csv / json
    file_path = Column(String(500), default="")
    content = Column(Text, default="")
    headers = Column(Text, default="[]")  # JSON array
    row_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_dataset_name", "name"),
    )


class DataSetRow(Base):
    __tablename__ = "data_set_row"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, nullable=False, default=1)
    dataset_id = Column(Integer, ForeignKey("data_set.id", ondelete="CASCADE"), nullable=False)
    row_index = Column(Integer, nullable=False)
    variables = Column(Text, default="{}")  # JSON object
    enabled = Column(Boolean, default=True)

    __table_args__ = (
        Index("idx_dataset_row_dataset", "dataset_id"),
        Index("idx_dataset_row_index", "dataset_id", "row_index"),
    )
