# =============================================================================
# pytest conftest — 测试共享 fixtures
# =============================================================================
# 将 backend 目录加入 sys.path，确保从项目根目录执行 pytest 时能正确导入 app 模块
# =============================================================================

import sys
from pathlib import Path

# 获取 backend 目录的绝对路径
_backend_path = Path(__file__).resolve().parent.parent
if str(_backend_path) not in sys.path:
    sys.path.insert(0, str(_backend_path))