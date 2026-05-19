"""
Scenario Repository — 场景 CRUD 操作
"""
from __future__ import annotations

import json
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session, joinedload

from app.models.scenario import Scenario, ScenarioStep


class ScenarioRepository:
    """Repository for Scenario database operations."""

    @staticmethod
    def create(db: Session, data: dict) -> Scenario:
        """Create a new scenario."""
        scenario = Scenario(**data)
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        return scenario

    @staticmethod
    def list(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[list[Scenario], int]:
        """List scenarios with pagination and filtering."""
        query = db.query(Scenario)

        if keyword:
            query = query.filter(Scenario.name.ilike(f"%{keyword}%"))

        if status:
            query = query.filter(Scenario.status == status)

        total = query.count()
        items = (
            query.order_by(Scenario.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def get_by_id(db: Session, scenario_id: int) -> Optional[Scenario]:
        """Get a scenario by ID with steps eagerly loaded."""
        return (
            db.query(Scenario)
            .options(joinedload(Scenario.steps))
            .filter(Scenario.id == scenario_id)
            .first()
        )

    @staticmethod
    def update(db: Session, scenario_obj: Scenario, data: dict) -> Scenario:
        """Update a scenario."""
        for key, value in data.items():
            if value is not None and hasattr(scenario_obj, key):
                setattr(scenario_obj, key, value)
        db.commit()
        db.refresh(scenario_obj)
        return scenario_obj

    @staticmethod
    def delete(db: Session, scenario_obj: Scenario) -> None:
        """Delete a scenario (cascades to steps)."""
        db.delete(scenario_obj)
        db.commit()

    # ── Scenario Steps ──────────────────────────────────────────

    @staticmethod
    def add_step(db: Session, scenario_id: int, data: dict) -> ScenarioStep:
        """Add a step to a scenario."""
        step = ScenarioStep(scenario_id=scenario_id, **data)
        db.add(step)
        db.commit()
        db.refresh(step)
        return step

    @staticmethod
    def update_step(db: Session, step_obj: ScenarioStep, data: dict) -> ScenarioStep:
        """Update a scenario step."""
        for key, value in data.items():
            if value is not None and hasattr(step_obj, key):
                setattr(step_obj, key, value)
        db.commit()
        db.refresh(step_obj)
        return step_obj

    @staticmethod
    def delete_step(db: Session, step_obj: ScenarioStep) -> None:
        """Delete a scenario step."""
        db.delete(step_obj)
        db.commit()

    @staticmethod
    def reorder_steps(db: Session, scenario_id: int, step_ids: List[int]) -> None:
        """Reorder steps by updating sort_order."""
        for idx, step_id in enumerate(step_ids):
            db.query(ScenarioStep).filter(
                ScenarioStep.id == step_id,
                ScenarioStep.scenario_id == scenario_id,
            ).update({"sort_order": idx})
        db.commit()
