#!/bin/bash
# =============================================================================
# Quality_Manage_platform 测试运行脚本
# 功能：
#   1. 运行 pytest 测试
#   2. 生成美观的 HTML 报告
#   3. 同时生成 JSON 结果文件（供自定义报告使用）
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_NAME="Quality_Manage_platform"
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORTS_DIR="$BACKEND_DIR/reports"

# 创建报告目录
mkdir -p "$REPORTS_DIR"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║   🧪 $PROJECT_NAME 测试报告生成器                                             ║"
echo "║   ───────────────────────────────────────────────────────────               ║"
echo "║   报告目录: $REPORTS_DIR                                                     ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 解析命令行参数
TEST_TARGET="${1:-tests/}"  # 默认测试所有 tests/
MARKERS="${2:-}"            # 可选：按标记筛选，如 "-m p0"
VERBOSE="${3:-}"            # 可选：-v 显示详细输出

# 清理旧报告
echo -e "${YELLOW}🧹 清理旧报告...${NC}"
rm -rf "$REPORTS_DIR"/*.html "$REPORTS_DIR"/*.json "$REPORTS_DIR"/*.log 2>/dev/null || true
mkdir -p "$REPORTS_DIR"

# 记录开始时间
START_TIME=$(date +%s)

# 运行 pytest
echo -e "${BLUE}▶ 运行 pytest 测试...${NC}"
echo ""

# 构建 pytest 命令
PYTEST_CMD="python -m pytest $TEST_TARGET --tb=short -v"

# 如果安装了 pytest-json-report，使用它生成 JSON
if python -c "import pytest_json_report" 2>/dev/null; then
    PYTEST_CMD="$PYTEST_CMD --json-report --json-report-file=$REPORTS_DIR/test_results.json"
fi

# 如果安装了 pytest-html，使用它生成 HTML
if python -c "import pytest_html" 2>/dev/null; then
    PYTEST_CMD="$PYTEST_CMD --html=$REPORTS_DIR/pytest_native_report.html --self-contained-html"
fi

# 添加标记过滤
if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD $MARKERS"
fi

# 执行测试
cd "$BACKEND_DIR"
eval $PYTEST_CMD || true

echo ""

# 记录结束时间
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# 使用自定义报告生成器生成美观的HTML报告
echo -e "${BLUE}▶ 生成自定义HTML报告...${NC}"

python3 -c "
import sys
sys.path.insert(0, '$BACKEND_DIR/tests')
from report_generator import TestReportGenerator
from pathlib import Path
import json
from datetime import datetime

# 尝试读取 pytest JSON 结果
json_file = Path('$REPORTS_DIR/test_results.json')
if json_file.exists():
    with open(json_file) as f:
        data = json.load(f)
    
    results = []
    for item in data.get('report', {}).get('tests', []):
        results.append({
            'name': item.get('nodeid', 'Unknown').split('::')[-1],
            'status': item.get('outcome', 'unknown'),
            'duration': item.get('duration', 0),
            'module': item.get('nodeid', 'Unknown').split('/')[-1].split('::')[0].replace('test_', '').replace('.py', ''),
            'description': item.get('nodeid', ''),
            'error_message': '',
        })
    
    # 如果有失败详情
    for item in data.get('report', {}).get('error_details', []):
        for r in results:
            if item.get('nodeid', '') in r.get('name', ''):
                r['error_message'] = item.get('message', '')
else:
    results = []

generator = TestReportGenerator('$PROJECT_NAME', 'v1.0.0')
generator.start_time = datetime.fromtimestamp($START_TIME)
generator.end_time = datetime.fromtimestamp($END_TIME)
generator.generate(results, '$REPORTS_DIR/test_report.html')
"

echo ""

# 显示报告位置
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                           📊 测试执行完成                                     ║"
echo "╠══════════════════════════════════════════════════════════════════════════════╣"
echo "║   执行时长: ${DURATION}秒                                                              ║"
echo "║   ────────────────────────────────────────────────────────────────────       ║"
echo "║   📄 HTML报告: $REPORTS_DIR/test_report.html                                  ║"
echo "║   📋 JSON结果: $REPORTS_DIR/test_results.json                                 ║"
echo "║   📝 Pytest日志: $REPORTS_DIR/pytest.log                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 如果安装了 allure 且有 java，也生成 allure 报告
if command -v allure &> /dev/null && java -version &> /dev/null; then
    echo -e "${BLUE}▶ 生成 Allure 报告...${NC}"
    allure generate "$REPORTS_DIR/allure-results" -o "$REPORTS_DIR/allure-report" --clean 2>/dev/null || true
    echo -e "${GREEN}✅ Allure 报告: $REPORTS_DIR/allure-report/index.html${NC}"
fi

# 自动打开报告（可选）
if [ "$OPEN_REPORT" = "true" ]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open "$REPORTS_DIR/test_report.html"
    elif command -v open &> /dev/null; then
        open "$REPORTS_DIR/test_report.html"
    fi
fi

echo ""
echo -e "${YELLOW}💡 提示: 使用 Python 内置服务器查看报告:${NC}"
echo -e "   ${BLUE}cd $REPORTS_DIR && python -m http.server 8080${NC}"
echo -e "${YELLOW}   然后访问: http://localhost:8080/test_report.html${NC}"
echo ""
