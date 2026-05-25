from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.quality_foundation import (
    QualityProject,
    QualityVersion,
    QualityIteration,
    RequirementItem,
)
from app.models.test_case import TestCase
from app.models.scenario import Scenario
from app.models.report import Report, Defect
from app.schemas.quality_foundation import (
    QualityProjectCreate,
    QualityProjectUpdate,
    QualityVersionCreate,
    QualityVersionUpdate,
    QualityIterationCreate,
    QualityIterationUpdate,
    RequirementItemCreate,
    RequirementItemUpdate,
    RequirementCoverageResponse,
)


def _bad_request(msg: str):
    raise ValueError(msg)


def list_projects(db: Session, keyword: str | None = None, status: str | None = None, skip: int = 0, limit: int = 100):
    query = db.query(QualityProject)
    if keyword:
        query = query.filter(QualityProject.name.contains(keyword) | QualityProject.code.contains(keyword))
    if status:
        query = query.filter(QualityProject.status == status)
    return query.offset(skip).limit(limit).all()


def get_project(db: Session, project_id: int):
    return db.query(QualityProject).filter(QualityProject.id == project_id).first()


def create_project(db: Session, data: QualityProjectCreate):
    project = QualityProject(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, project_id: int, data: QualityProjectUpdate):
    project = db.query(QualityProject).filter(QualityProject.id == project_id).first()
    if not project:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int):
    project = db.query(QualityProject).filter(QualityProject.id == project_id).first()
    if not project:
        return {"success": False}

    # 保护性删除：检查质量基础关联数据
    from app.models.quality_foundation import QualityVersion, QualityIteration, RequirementItem
    has_versions = db.query(QualityVersion).filter(QualityVersion.project_id == project_id).count() > 0
    has_iterations = db.query(QualityIteration).filter(QualityIteration.project_id == project_id).count() > 0
    has_requirements = db.query(RequirementItem).filter(RequirementItem.project_id == project_id).count() > 0
    if has_versions or has_iterations or has_requirements:
        return {"success": False, "error": "该项目下存在版本、迭代或需求，无法删除。建议先将项目状态改为归档。"}

    # 保护性删除：检查业务表引用（用例/场景/报告/缺陷）
    has_cases = db.query(TestCase).filter(TestCase.project_id == project_id).count() > 0
    has_scenarios = db.query(Scenario).filter(Scenario.project_id == project_id).count() > 0
    has_reports = db.query(Report).filter(Report.project_id == project_id).count() > 0
    has_defects_version = db.query(Defect).filter(Defect.project_id == project_id).count() > 0
    if has_cases or has_scenarios or has_reports or has_defects_version:
        return {"success": False, "error": "该项目下存在用例、场景、报告或缺陷，无法删除。建议先将项目状态改为归档。"}

    db.delete(project)
    db.commit()
    return {"success": True}


def list_versions(db: Session, project_id: int | None = None, skip: int = 0, limit: int = 100):
    query = db.query(QualityVersion)
    if project_id:
        query = query.filter(QualityVersion.project_id == project_id)
    return query.offset(skip).limit(limit).all()


def get_version(db: Session, version_id: int):
    return db.query(QualityVersion).filter(QualityVersion.id == version_id).first()


def create_version(db: Session, data: QualityVersionCreate):
    # 层级校验：project_id 必须存在
    project_id = data.project_id
    if project_id is not None:
        exists = db.query(QualityProject).filter(QualityProject.id == project_id).first()
        if not exists:
            raise ValueError(f"项目 {project_id} 不存在")
    version = QualityVersion(**data.model_dump())
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def update_version(db: Session, version_id: int, data: QualityVersionUpdate):
    version = db.query(QualityVersion).filter(QualityVersion.id == version_id).first()
    if not version:
        return None
    # 层级校验：若更新 project_id，目标项目必须存在
    updates = data.model_dump(exclude_unset=True)
    if "project_id" in updates and updates["project_id"] is not None:
        pid = updates["project_id"]
        exists = db.query(QualityProject).filter(QualityProject.id == pid).first()
        if not exists:
            raise ValueError(f"项目 {pid} 不存在")
    for key, value in updates.items():
        setattr(version, key, value)
    db.commit()
    db.refresh(version)
    return version


def delete_version(db: Session, version_id: int):
    version = db.query(QualityVersion).filter(QualityVersion.id == version_id).first()
    if not version:
        return {"success": False}

    from app.models.quality_foundation import QualityIteration, RequirementItem
    has_iterations = db.query(QualityIteration).filter(QualityIteration.version_id == version_id).count() > 0
    has_requirements = db.query(RequirementItem).filter(RequirementItem.version_id == version_id).count() > 0
    if has_iterations or has_requirements:
        return {"success": False, "error": "该版本下存在迭代或需求，无法删除。建议先将版本状态改为归档。"}

    # 保护性删除：检查业务表引用
    has_cases = db.query(TestCase).filter(TestCase.version_id == version_id).count() > 0
    has_scenarios = db.query(Scenario).filter(Scenario.version_id == version_id).count() > 0
    has_reports = db.query(Report).filter(Report.version_id == version_id).count() > 0
    has_defects = db.query(Defect).filter(Defect.version_id == version_id).count() > 0
    if has_cases or has_scenarios or has_reports or has_defects:
        return {"success": False, "error": "该版本下存在用例、场景、报告或缺陷，无法删除。建议先将版本状态改为归档。"}

    db.delete(version)
    db.commit()
    return {"success": True}


def list_iterations(db: Session, project_id: int | None = None, version_id: int | None = None, skip: int = 0, limit: int = 100):
    query = db.query(QualityIteration)
    if project_id:
        query = query.filter(QualityIteration.project_id == project_id)
    if version_id:
        query = query.filter(QualityIteration.version_id == version_id)
    return query.offset(skip).limit(limit).all()


def get_iteration(db: Session, iteration_id: int):
    return db.query(QualityIteration).filter(QualityIteration.id == iteration_id).first()


def create_iteration(db: Session, data: QualityIterationCreate):
    # 层级校验：version_id 存在且其 project_id 与 data.project_id 一致
    version_id = data.version_id
    project_id = data.project_id
    if version_id is not None:
        version = db.query(QualityVersion).filter(QualityVersion.id == version_id).first()
        if not version:
            raise ValueError(f"版本 {version_id} 不存在")
        if project_id is not None and version.project_id != project_id:
            raise ValueError("迭代的 project_id 必须与所属版本的 project_id 一致")
    iteration = QualityIteration(**data.model_dump())
    db.add(iteration)
    db.commit()
    db.refresh(iteration)
    return iteration


def update_iteration(db: Session, iteration_id: int, data: QualityIterationUpdate):
    iteration = db.query(QualityIteration).filter(QualityIteration.id == iteration_id).first()
    if not iteration:
        return None
    updates = data.model_dump(exclude_unset=True)
    # 层级校验
    if "version_id" in updates and updates["version_id"] is not None:
        vid = updates["version_id"]
        version = db.query(QualityVersion).filter(QualityVersion.id == vid).first()
        if not version:
            raise ValueError(f"版本 {vid} 不存在")
        p_id = updates.get("project_id", iteration.project_id)
        if p_id is not None and version.project_id != p_id:
            raise ValueError("迭代的 project_id 必须与所属版本的 project_id 一致")
    for key, value in updates.items():
        setattr(iteration, key, value)
    db.commit()
    db.refresh(iteration)
    return iteration


def delete_iteration(db: Session, iteration_id: int):
    iteration = db.query(QualityIteration).filter(QualityIteration.id == iteration_id).first()
    if not iteration:
        return {"success": False}

    from app.models.quality_foundation import RequirementItem
    has_requirements = db.query(RequirementItem).filter(RequirementItem.iteration_id == iteration_id).count() > 0
    if has_requirements:
        return {"success": False, "error": "该迭代下存在需求，无法删除。"}

    # 保护性删除：检查业务表引用
    has_cases = db.query(TestCase).filter(TestCase.iteration_id == iteration_id).count() > 0
    has_scenarios = db.query(Scenario).filter(Scenario.iteration_id == iteration_id).count() > 0
    has_reports = db.query(Report).filter(Report.iteration_id == iteration_id).count() > 0
    has_defects = db.query(Defect).filter(Defect.iteration_id == iteration_id).count() > 0
    if has_cases or has_scenarios or has_reports or has_defects:
        return {"success": False, "error": "该迭代下存在用例、场景、报告或缺陷，无法删除。建议先将迭代状态改为归档。"}

    db.delete(iteration)
    db.commit()
    return {"success": True}


def list_requirements(
    db: Session,
    project_id: int | None = None,
    version_id: int | None = None,
    iteration_id: int | None = None,
    keyword: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    query = db.query(RequirementItem)
    if project_id:
        query = query.filter(RequirementItem.project_id == project_id)
    if version_id:
        query = query.filter(RequirementItem.version_id == version_id)
    if iteration_id:
        query = query.filter(RequirementItem.iteration_id == iteration_id)
    if keyword:
        query = query.filter(RequirementItem.title.contains(keyword) | RequirementItem.source_key.contains(keyword))
    if status:
        query = query.filter(RequirementItem.status == status)
    return query.offset(skip).limit(limit).all()


def get_requirement(db: Session, requirement_id: int):
    return db.query(RequirementItem).filter(RequirementItem.id == requirement_id).first()


def create_requirement(db: Session, data: RequirementItemCreate):
    # 层级校验
    project_id = data.project_id
    version_id = data.version_id
    iteration_id = data.iteration_id

    if version_id is not None:
        version = db.query(QualityVersion).filter(QualityVersion.id == version_id).first()
        if not version:
            raise ValueError(f"版本 {version_id} 不存在")
        if project_id is not None and version.project_id != project_id:
            raise ValueError("需求的 project_id 必须与所属版本的 project_id 一致")

    if iteration_id is not None:
        iteration = db.query(QualityIteration).filter(QualityIteration.id == iteration_id).first()
        if not iteration:
            raise ValueError(f"迭代 {iteration_id} 不存在")
        if iteration.version_id != version_id:
            raise ValueError("需求的 version_id 必须与所属迭代的 version_id 一致")
        if project_id is not None and iteration.project_id != project_id:
            raise ValueError("需求的 project_id 必须与所属迭代的 project_id 一致")

    requirement = RequirementItem(**data.model_dump())
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    return requirement


def update_requirement(db: Session, requirement_id: int, data: RequirementItemUpdate):
    requirement = db.query(RequirementItem).filter(RequirementItem.id == requirement_id).first()
    if not requirement:
        return None
    updates = data.model_dump(exclude_unset=True)
    project_id = updates.get("project_id", requirement.project_id)
    version_id = updates.get("version_id", requirement.version_id)
    iteration_id = updates.get("iteration_id", requirement.iteration_id)

    if "version_id" in updates and version_id is not None:
        version = db.query(QualityVersion).filter(QualityVersion.id == version_id).first()
        if not version:
            raise ValueError(f"版本 {version_id} 不存在")
        if project_id is not None and version.project_id != project_id:
            raise ValueError("需求的 project_id 必须与所属版本的 project_id 一致")

    if "iteration_id" in updates and iteration_id is not None:
        iteration = db.query(QualityIteration).filter(QualityIteration.id == iteration_id).first()
        if not iteration:
            raise ValueError(f"迭代 {iteration_id} 不存在")
        if iteration.version_id != version_id:
            raise ValueError("需求的 version_id 必须与所属迭代的 version_id 一致")
        if project_id is not None and iteration.project_id != project_id:
            raise ValueError("需求的 project_id 必须与所属迭代的 project_id 一致")

    for key, value in updates.items():
        setattr(requirement, key, value)
    db.commit()
    db.refresh(requirement)
    return requirement


def delete_requirement(db: Session, requirement_id: int):
    requirement = db.query(RequirementItem).filter(RequirementItem.id == requirement_id).first()
    if not requirement:
        return {"success": False, "error": None}
    db.delete(requirement)
    db.commit()
    return {"success": True}


def get_requirement_coverage(db: Session, project_id: int | None = None):
    from app.models.test_case import TestCase
    from app.models.scenario import Scenario, ScenarioStep, ExecutionRun
    from app.models.report import Defect

    base_query = db.query(RequirementItem)
    if project_id:
        base_query = base_query.filter(RequirementItem.project_id == project_id)

    requirements = base_query.all()
    total = len(requirements)

    # with_test_case: 有关联用例的需求数
    with_test_case = sum(
        1 for r in requirements
        if db.query(TestCase).filter(TestCase.requirement_id == r.id).first() is not None
    )

    # with_scenario: 按需求逐个判断 — 该需求下任意用例出现在 ScenarioStep 中则计入
    with_scenario = 0
    for req in requirements:
        case_ids = [tc.id for tc in req.test_cases]
        if not case_ids:
            continue
        has_scenario_coverage = db.query(ScenarioStep.id).filter(
            ScenarioStep.case_id.in_(case_ids)
        ).first() is not None
        if has_scenario_coverage:
            with_scenario += 1

    # executed: 按需求逐个判断 — 该需求下任意用例有终态执行记录（直接用例执行 OR 包含该用例的场景执行）
    # 终态 = passed 或 failed
    executed = 0
    for req in requirements:
        case_ids = [tc.id for tc in req.test_cases]
        if not case_ids:
            continue
        # 1) 直接用例执行
        direct_exec = db.query(ExecutionRun.id).filter(
            ExecutionRun.run_type == "case",
            ExecutionRun.target_id.in_(case_ids),
            ExecutionRun.status.in_("passed", "failed")
        ).first() is not None
        if direct_exec:
            executed += 1
            continue
        # 2) 场景执行中包含该需求的用例
        scenario_exec = db.query(ExecutionRun.id).join(
            Scenario, ExecutionRun.target_id == Scenario.id
        ).filter(
            ExecutionRun.run_type == "scenario",
            ExecutionRun.status.in_("passed", "failed"),
            ScenarioStep.case_id.in_(case_ids)
        ).first() is not None
        if scenario_exec:
            executed += 1

    # with_defect: 有关联缺陷的需求数
    with_defect = sum(
        1 for r in requirements
        if db.query(Defect).filter(Defect.requirement_id == r.id).first() is not None
    )

    return RequirementCoverageResponse(
        total=total,
        with_test_case=with_test_case,
        with_scenario=with_scenario,
        executed=executed,
        with_defect=with_defect,
    )