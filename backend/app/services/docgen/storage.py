"""
文档生成服务 — 文件存储与安全
"""

import os
import uuid
import shutil
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "docgen"
UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUTS_DIR = DATA_DIR / "outputs"
TEMPLATES_DIR = DATA_DIR / "templates"
RULES_DIR = DATA_DIR / "rules"


def _ensure_dirs():
    for d in [UPLOADS_DIR, OUTPUTS_DIR, TEMPLATES_DIR, RULES_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def safe_filename(original_name: str) -> str:
    """安全清洗文件名，防止路径穿越和特殊字符"""
    name = os.path.basename(original_name)
    name = "".join(c for c in name if c.isalnum() or c in ('.', '-', '_')).strip()
    if not name:
        name = "file"
    name, ext = os.path.splitext(name)
    unique = str(uuid.uuid4())[:8]
    return f"{name}_{unique}{ext}"


def save_upload(content: bytes, original_name: str) -> str:
    """保存上传文件，返回相对路径"""
    _ensure_dirs()
    safe_name = safe_filename(original_name)
    path = UPLOADS_DIR / safe_name
    with open(path, "wb") as f:
        f.write(content)
    return str(path)


def get_upload_path(relative_path: str) -> Path:
    """解析上传文件路径（防路径穿越）"""
    _ensure_dirs()
    target = (UPLOADS_DIR / relative_path).resolve()
    if not str(target).startswith(str(UPLOADS_DIR.resolve())):
        raise ValueError("非法路径")
    return target


def save_output(content: bytes, filename: str) -> str:
    """保存输出文件，返回相对路径"""
    _ensure_dirs()
    safe_name = safe_filename(filename)
    path = OUTPUTS_DIR / safe_name
    with open(path, "wb") as f:
        f.write(content)
    return str(path)


def get_output_path(relative_path: str) -> Path:
    """解析输出文件路径（防路径穿越）"""
    _ensure_dirs()
    target = (OUTPUTS_DIR / relative_path).resolve()
    if not str(target).startswith(str(OUTPUTS_DIR.resolve())):
        raise ValueError("非法路径")
    return target


def get_templates_dir() -> Path:
    _ensure_dirs()
    return TEMPLATES_DIR


def get_rules_dir() -> Path:
    _ensure_dirs()
    return RULES_DIR