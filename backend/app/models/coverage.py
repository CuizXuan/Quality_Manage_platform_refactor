from sqlalchemy import Column, Integer, String, Float, Text, Date, DateTime, Index
from datetime import datetime
from app.models.base import Base


class CoverageRecord(Base):
    __tablename__ = "coverage_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer, nullable=False)
    commit_hash = Column(String(64), nullable=False)
    file_path = Column(String(500), nullable=False)
    line_coverage = Column(Float, default=0.0)
    branch_coverage = Column(Float, default=0.0)
    function_coverage = Column(Float, default=0.0)
    total_lines = Column(Integer, default=0)
    covered_lines = Column(Integer, default=0)
    uncovered_lines = Column(Text, default="[]")  # JSON array of line numbers
    report_format = Column(String(20), default="lcov")  # lcov/cobertura/jacoco
    report_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_coverage_repo_commit", "repository_id", "commit_hash"),
        Index("idx_coverage_repo_date", "repository_id", "report_date"),
    )
