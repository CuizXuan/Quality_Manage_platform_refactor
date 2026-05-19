from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models import CodeRepository, CodeFile, CodeMethod

router = APIRouter(prefix="/api/repositories", tags=["代码仓库"])


class RepositoryCreate(BaseModel):
    name: str
    url: str
    branch: Optional[str] = "main"
    provider: Optional[str] = "gitlab"
    access_token: Optional[str] = ""


class RepositoryUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    branch: Optional[str] = None
    provider: Optional[str] = None
    access_token: Optional[str] = None


@router.get("")
def list_repos(db: Session = Depends(get_db)):
    repos = db.query(CodeRepository).order_by(CodeRepository.id.desc()).all()
    return {"code": 0, "data": repos}


@router.post("")
def create_repo(data: RepositoryCreate, db: Session = Depends(get_db)):
    repo = CodeRepository(**data.model_dump())
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return {"code": 0, "data": repo}


@router.get("/{repo_id}")
def get_repo(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(CodeRepository).filter(CodeRepository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="仓库不存在")
    return {"code": 0, "data": repo}


@router.put("/{repo_id}")
def update_repo(repo_id: int, data: RepositoryUpdate, db: Session = Depends(get_db)):
    repo = db.query(CodeRepository).filter(CodeRepository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="仓库不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(repo, k, v)
    db.commit()
    db.refresh(repo)
    return {"code": 0, "data": repo}


@router.delete("/{repo_id}")
def delete_repo(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(CodeRepository).filter(CodeRepository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="仓库不存在")
    db.query(CodeFile).filter(CodeFile.repository_id == repo_id).delete()
    db.delete(repo)
    db.commit()
    return {"code": 0, "message": "删除成功"}


@router.post("/{repo_id}/sync")
def sync_repo(repo_id: int, db: Session = Depends(get_db)):
    """同步代码结构 - 解析本地仓库文件列表"""
    repo = db.query(CodeRepository).filter(CodeRepository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="仓库不存在")
    from datetime import datetime
    import os
    files = []
    if repo.local_path and os.path.isdir(repo.local_path):
        for root, dirs, filenames in os.walk(repo.local_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'venv', '.git')]
            for fname in filenames:
                if fname.startswith('.'):
                    continue
                fpath = os.path.relpath(os.path.join(root, fname), repo.local_path)
                ext = os.path.splitext(fname)[1].lstrip('.')
                lang_map = {"py": "python", "java": "java", "js": "javascript", "ts": "javascript",
                            "go": "go", "rs": "rust", "cpp": "cpp", "c": "c"}
                files.append({
                    "file_path": fpath.replace("\\", "/"),
                    "file_name": fname,
                    "language": lang_map.get(ext, ext),
                })
    repo.last_sync_at = datetime.now()
    db.commit()
    return {"code": 0, "data": {"total": len(files), "files": files[:200]}}
