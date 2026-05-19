#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest 报告定制化配置 - Quality_Manage_platform
包含：自定义元数据、失败截图、日志增强、报告样式
"""
import os
import sys
import json
import pytest
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# =============================================================================
# 项目元数据
# =============================================================================
PROJECT_NAME = "Quality_Manage_platform"
PROJECT_VERSION = "v1.0.0"
PROJECT_DESCRIPTION = "质量管理平台 - API Debug Tool"
TEST_ENVIRONMENT = os.getenv("TEST_ENV", "测试环境")
TEST_ENV_URL = os.getenv("TEST_ENV_URL", "http://localhost:8000")

# =============================================================================
# 全局测试结果收集器
# =============================================================================
class TestResultCollector:
    """收集所有测试结果，用于生成自定义报告"""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None
        self.session = None

    def reset(self):
        """重置收集器"""
        self.results = []
        self.start_time = datetime.now()
        self.end_time = None

    def add_result(self, result: Dict[str, Any]):
        """添加测试结果"""
        self.results.append(result)

    def finalize(self):
        """结束收集"""
        self.end_time = datetime.now()

    def save_to_json(self, filepath: str = "reports/test_results.json") -> str:
        """保存结果到JSON文件"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        duration = 0
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        data = {
            "metadata": {
                "project_name": PROJECT_NAME,
                "project_version": PROJECT_VERSION,
                "test_env": TEST_ENVIRONMENT,
                "test_env_url": TEST_ENV_URL,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration": duration,
                "python_version": sys.version.split()[0],
                "pytest_version": pytest.__version__,
            },
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r["status"] == "passed"),
                "failed": sum(1 for r in self.results if r["status"] == "failed"),
                "skipped": sum(1 for r in self.results if r["status"] == "skipped"),
                "error": sum(1 for r in self.results if r["status"] == "error"),
            },
            "results": self.results,
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON结果已保存: {filepath}")
        return filepath


# 全局收集器实例
collector = TestResultCollector()


# =============================================================================
# pytest 配置钩子
# =============================================================================
def pytest_configure(config):
    """全局配置"""
    # 注册自定义标记
    config.addinivalue_line("markers", "p0: P0级测试用例，核心流程")
    config.addinivalue_line("markers", "p1: P1级测试用例，重要功能")
    config.addinivalue_line("markers", "p2: P2级测试用例，边界/异常")
    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "api: API测试")
    config.addinivalue_line("markers", "slow: 执行较慢的测试")

    # 设置测试元数据
    config._metadata = {
        "项目名称": PROJECT_NAME,
        "项目版本": PROJECT_VERSION,
        "项目描述": PROJECT_DESCRIPTION,
        "测试环境": TEST_ENVIRONMENT,
        "环境地址": TEST_ENV_URL,
        "Python版本": sys.version.split()[0],
        "测试时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "操作人": os.getenv("TEST_OPERATOR", "自动化测试"),
    }
    config._metadata_description = f"{PROJECT_NAME} {PROJECT_VERSION} 自动化测试报告"


def pytest_sessionstart(session):
    """测试会话开始"""
    collector.reset()
    collector.session = session
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🧪 {PROJECT_NAME} - pytest 测试报告生成器                                      ║
║   ───────────────────────────────────────────────────────────               ║
║   版本: {PROJECT_VERSION}                                                            ║
║   环境: {TEST_ENVIRONMENT} ({TEST_ENV_URL})                                        ║
║   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)


# =============================================================================
# 测试结果收集 + 报告增强（统一的hook）
# =============================================================================
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """为每个测试用例生成报告并收集结果"""
    outcome = yield
    report = outcome.get_result()

    # 只在 call 阶段处理（跳过 setup/teardown）
    if report.when != "call":
        return

    # ---- 收集结果到全局收集器 ----
    nodeid_parts = report.nodeid.split('/')
    module = "unknown"
    if len(nodeid_parts) > 1:
        module_file = nodeid_parts[-1].split('::')[0]
        module = module_file.replace('test_', '').replace('.py', '')

    test_name = report.nodeid.split('::')[-1] if '::' in report.nodeid else report.nodeid

    description = ""
    if item.obj.__doc__:
        description = item.obj.__doc__.strip().split('\n')[0]

    result = {
        "nodeid": report.nodeid,
        "name": test_name,
        "status": report.outcome,
        "duration": getattr(report, 'duration', 0),
        "module": module,
        "description": description,
    }

    if report.failed:
        result["error_message"] = str(getattr(report, 'longrepr', ''))[:500]

        # 失败原因分类
        longrepr = str(getattr(report, 'longrepr', ''))
        if 'AssertionError' in longrepr:
            result["failure_type"] = "断言失败"
        elif 'Timeout' in longrepr or 'timed out' in longrepr.lower():
            result["failure_type"] = "超时"
        elif 'Connection' in longrepr or 'Network' in longrepr:
            result["failure_type"] = "网络问题"
        elif 'Database' in longrepr or 'sqlite' in longrepr:
            result["failure_type"] = "数据库问题"
        else:
            result["failure_type"] = "其他错误"

    collector.add_result(result)

    # ---- 添加失败详情到报告 sections ----
    if report.when == "call" and report.failed:
        excinfo = report.longrepr
        if excinfo:
            error_msg = str(excinfo)
            key_lines = []
            for line in error_msg.split('\n'):
                if 'AssertionError' in line or 'Error' in line or 'FAILED' in line:
                    key_lines.append(line.strip())
            if key_lines:
                report.sections.append(("关键错误信息", "\n".join(key_lines)))


# =============================================================================
# 测试结果摘要增强
# =============================================================================
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """自定义测试摘要"""
    print("\n")
    print("=" * 80)
    print("📋 测试摘要")
    print("=" * 80)

    stats = terminalreporter.stats
    passed = len(stats.get('passed', []))
    failed = len(stats.get('failed', []))
    skipped = len(stats.get('skipped', []))
    error = len(stats.get('error', []))
    total = passed + failed + skipped + error
    pass_rate = (passed / total * 100) if total > 0 else 0

    # 按模块统计
    module_stats = {}
    for rep in stats.get('passed', []) + stats.get('failed', []):
        parts = rep.nodeid.split('/')
        if len(parts) > 1:
            module = parts[-1].split('::')[0].replace('test_', '').replace('.py', '')
            if module not in module_stats:
                module_stats[module] = {'passed': 0, 'failed': 0}
            if rep in stats.get('passed', []):
                module_stats[module]['passed'] += 1
            else:
                module_stats[module]['failed'] += 1

    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              📊 测试统计                                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║   总用例数: {total:>5}                                                           ║
║   通过:     {passed:>5}  ✓                                                       ║
║   失败:     {failed:>5}  ✗                                                       ║
║   跳过:     {skipped:>5}  ○                                                       ║
║   错误:     {error:>5}  !                                                       ║
║   ────────────────────────────────────────────────────────────────────       ║
║   通过率:   {pass_rate:>5.1f}%                                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    if module_stats:
        print("\n📁 模块统计:")
        print("-" * 60)
        print(f"{'模块':<20} {'通过':>8} {'失败':>8} {'状态':>10}")
        print("-" * 60)
        for module, stat in sorted(module_stats.items()):
            status = "✅" if stat['failed'] == 0 else "⚠️"
            print(f"{module:<20} {stat['passed']:>8} {stat['failed']:>8} {status:>10}")
        print("-" * 60)

    print(f"""
📌 环境信息:
   Python: {sys.version.split()[0]}
   Pytest: {pytest.__version__}
   项目: {PROJECT_NAME} {PROJECT_VERSION}
   环境: {TEST_ENVIRONMENT}
""")
    print("=" * 80)


# =============================================================================
# 会话结束 - 保存 JSON + 生成 HTML 报告
# =============================================================================
def pytest_sessionfinish(session, exitstatus):
    """会话结束时保存测试结果并生成报告"""
    collector.finalize()

    # 1. 保存 JSON 结果
    json_path = collector.save_to_json("reports/test_results.json")

    # 2. 生成自定义 HTML 报告
    try:
        from tests.report import TestReportGenerator

        generator = TestReportGenerator(PROJECT_NAME, PROJECT_VERSION)
        generator.start_time = collector.start_time
        generator.end_time = collector.end_time
        html_path = generator.generate(collector.results, "reports/test_report.html")
        print(f"✅ HTML报告已生成: {html_path}")
    except Exception as e:
        print(f"⚠️ 生成自定义HTML报告失败: {e}")

    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           📊 测试执行完成                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║   JSON结果: reports/test_results.json                                      ║
║   HTML报告: reports/test_report.html                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
