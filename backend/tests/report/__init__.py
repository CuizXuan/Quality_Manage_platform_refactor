#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SRE Dashboard风格测试报告生成器 - Quality_Manage_platform
特性：
1. SRE监控仪表盘风格（深色主题，Grafana风格）
2. 服务健康状态指示
3. 实时监控感的数据可视化
4. 告警样式失败展示
5. 错误预算可视化
6. 时间线视图
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


# =============================================================================
# SRE Dashboard 风格报告生成器
# =============================================================================
class SREReportGenerator:
    """生成SRE Dashboard风格的HTML测试报告"""

    def __init__(self, project_name: str = "Quality_Manage_platform", project_version: str = "v1.0.0"):
        self.project_name = project_name
        self.project_version = project_version
        self.results: List[Dict[str, Any]] = []
        self.summary = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'error': 0,
            'pass_rate': 0.0
        }
        self.module_stats: Dict[str, Dict[str, int]] = {}
        self.failure_analysis: List[Dict] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.metadata: Dict[str, Any] = {}

    # =========================================================================
    # SRE风格HTML模板
    # =========================================================================
    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --bg-card: #1c2128;
            --border-color: #30363d;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --text-muted: #6e7681;
            
            --success: #238636;
            --success-light: #2ea043;
            --success-glow: rgba(46, 160, 67, 0.4);
            
            --danger: #da3633;
            --danger-light: #f85149;
            --danger-glow: rgba(248, 81, 73, 0.4);
            
            --warning: #9e6a03;
            --warning-light: #d29922;
            --warning-glow: rgba(210, 153, 34, 0.4);
            
            --info: #388bfd;
            --info-light: #58a6ff;
            
            --purple: #a371f7;
            --cyan: #39c5cf;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }}

        /* 滚动条样式 */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: var(--bg-secondary);
        }}
        ::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--text-muted);
        }}

        /* 主容器 */
        .dashboard-container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 1.5rem;
        }}

        /* 顶部导航 */
        .dashboard-header {{
            background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
            border-bottom: 1px solid var(--border-color);
            padding: 1rem 1.5rem;
            margin: -1.5rem -1.5rem 1.5rem -1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .header-left {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .logo {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .logo-icon {{
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, var(--info) 0%, var(--purple) 100%);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
        }}

        .header-status {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: var(--bg-tertiary);
            border-radius: 2rem;
            font-size: 0.875rem;
        }}

        .status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}

        .status-dot.healthy {{
            background: var(--success-light);
            box-shadow: 0 0 8px var(--success-glow);
        }}

        .status-dot.degraded {{
            background: var(--warning-light);
            box-shadow: 0 0 8px var(--warning-glow);
        }}

        .status-dot.down {{
            background: var(--danger-light);
            box-shadow: 0 0 8px var(--danger-glow);
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}

        /* 健康状态卡片 */
        .health-overview {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}

        .health-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
            position: relative;
            overflow: hidden;
        }}

        .health-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
        }}

        .health-card.total::before {{ background: linear-gradient(90deg, var(--info), var(--purple)); }}
        .health-card.passed::before {{ background: linear-gradient(90deg, var(--success), var(--success-light)); }}
        .health-card.failed::before {{ background: linear-gradient(90deg, var(--danger), var(--danger-light)); }}
        .health-card.skipped::before {{ background: linear-gradient(90deg, var(--warning), var(--warning-light)); }}

        .health-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.75rem;
        }}

        .health-card-title {{
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
        }}

        .health-card-icon {{
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
        }}

        .health-card.total .health-card-icon {{ background: rgba(56, 139, 253, 0.15); color: var(--info-light); }}
        .health-card.passed .health-card-icon {{ background: rgba(46, 160, 67, 0.15); color: var(--success-light); }}
        .health-card.failed .health-card-icon {{ background: rgba(248, 81, 73, 0.15); color: var(--danger-light); }}
        .health-card.skipped .health-card-icon {{ background: rgba(210, 153, 34, 0.15); color: var(--warning-light); }}

        .health-card-value {{
            font-size: 2.25rem;
            font-weight: 700;
            line-height: 1;
            margin-bottom: 0.25rem;
        }}

        .health-card-trend {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        /* 通过率仪表盘 */
        .metrics-row {{
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        @media (max-width: 1024px) {{
            .metrics-row {{
                grid-template-columns: 1fr;
            }}
        }}

        .pass-rate-gauge {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
        }}

        .gauge-header {{
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .gauge-container {{
            position: relative;
            width: 200px;
            height: 200px;
            margin: 0 auto 1rem;
        }}

        .gauge-svg {{
            transform: rotate(-90deg);
        }}

        .gauge-bg {{
            fill: none;
            stroke: var(--bg-tertiary);
            stroke-width: 12;
        }}

        .gauge-fill {{
            fill: none;
            stroke-width: 12;
            stroke-linecap: round;
            transition: stroke-dashoffset 1s ease;
        }}

        .gauge-fill.excellent {{ stroke: var(--success-light); }}
        .gauge-fill.good {{ stroke: var(--info-light); }}
        .gauge-fill.warning {{ stroke: var(--warning-light); }}
        .gauge-fill.critical {{ stroke: var(--danger-light); }}

        .gauge-center {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }}

        .gauge-value {{
            font-size: 2.5rem;
            font-weight: 700;
            line-height: 1;
        }}

        .gauge-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
        }}

        .gauge-status {{
            text-align: center;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 600;
        }}

        .gauge-status.excellent {{ background: rgba(46, 160, 67, 0.15); color: var(--success-light); }}
        .gauge-status.good {{ background: rgba(56, 139, 253, 0.15); color: var(--info-light); }}
        .gauge-status.warning {{ background: rgba(210, 153, 34, 0.15); color: var(--warning-light); }}
        .gauge-status.critical {{ background: rgba(248, 81, 73, 0.15); color: var(--danger-light); }}

        /* 模块健康度 */
        .module-health {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
        }}

        .section-header {{
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .module-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 1rem;
        }}

        .module-item {{
            background: var(--bg-tertiary);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
            border: 1px solid transparent;
            transition: all 0.2s;
        }}

        .module-item:hover {{
            border-color: var(--border-color);
            transform: translateY(-2px);
        }}

        .module-item.healthy {{
            border-left: 3px solid var(--success-light);
        }}

        .module-item.degraded {{
            border-left: 3px solid var(--warning-light);
        }}

        .module-item.down {{
            border-left: 3px solid var(--danger-light);
        }}

        .module-name {{
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }}

        .module-stats {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        .module-stats span {{
            margin: 0 0.25rem;
        }}

        .module-rate {{
            font-size: 1.25rem;
            font-weight: 700;
            margin-top: 0.5rem;
        }}

        /* 错误预算 */
        .error-budget {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .budget-bar-container {{
            background: var(--bg-tertiary);
            border-radius: 4px;
            height: 24px;
            overflow: hidden;
            position: relative;
            margin: 1rem 0;
        }}

        .budget-bar-used {{
            height: 100%;
            background: linear-gradient(90deg, var(--danger), var(--danger-light));
            transition: width 1s ease;
        }}

        .budget-bar-remaining {{
            height: 100%;
            background: linear-gradient(90deg, var(--success), var(--success-light));
            position: absolute;
            right: 0;
            top: 0;
            transition: width 1s ease;
        }}

        .budget-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        /* 告警面板 */
        .alerts-panel {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 1.5rem;
            overflow: hidden;
        }}

        .alerts-header {{
            padding: 1rem 1.5rem;
            background: rgba(248, 81, 73, 0.1);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .alert-icon {{
            width: 24px;
            height: 24px;
            background: var(--danger);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            animation: blink 1s infinite;
        }}

        @keyframes blink {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}

        .alerts-title {{
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--danger-light);
        }}

        .alerts-count {{
            margin-left: auto;
            background: var(--danger);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .alert-item {{
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            gap: 1rem;
            align-items: flex-start;
        }}

        .alert-item:last-child {{
            border-bottom: none;
        }}

        .alert-severity {{
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.625rem;
            font-weight: 700;
            text-transform: uppercase;
        }}

        .alert-severity.critical {{
            background: rgba(248, 81, 73, 0.2);
            color: var(--danger-light);
        }}

        .alert-severity.warning {{
            background: rgba(210, 153, 34, 0.2);
            color: var(--warning-light);
        }}

        .alert-content {{
            flex: 1;
        }}

        .alert-test-name {{
            font-weight: 600;
            font-size: 0.875rem;
            margin-bottom: 0.25rem;
        }}

        .alert-message {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            font-family: 'Monaco', 'Menlo', monospace;
            background: var(--bg-tertiary);
            padding: 0.5rem;
            border-radius: 4px;
            margin-top: 0.5rem;
            overflow-x: auto;
        }}

        /* 测试详情表 */
        .tests-table-container {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
        }}

        .tests-table-header {{
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .tests-table-title {{
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .filter-buttons {{
            display: flex;
            gap: 0.5rem;
        }}

        .filter-btn {{
            padding: 0.5rem 1rem;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-secondary);
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .filter-btn:hover {{
            background: var(--bg-secondary);
            color: var(--text-primary);
        }}

        .filter-btn.active {{
            background: var(--info);
            border-color: var(--info);
            color: white;
        }}

        .tests-table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .tests-table th {{
            text-align: left;
            padding: 0.75rem 1rem;
            background: var(--bg-tertiary);
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border-color);
        }}

        .tests-table td {{
            padding: 0.875rem 1rem;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.875rem;
        }}

        .tests-table tr:last-child td {{
            border-bottom: none;
        }}

        .tests-table tr:hover td {{
            background: var(--bg-tertiary);
        }}

        .test-status {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .test-status.passed {{
            background: rgba(46, 160, 67, 0.15);
            color: var(--success-light);
        }}

        .test-status.failed {{
            background: rgba(248, 81, 73, 0.15);
            color: var(--danger-light);
        }}

        .test-status.skipped {{
            background: rgba(210, 153, 34, 0.15);
            color: var(--warning-light);
        }}

        .test-name {{
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.8125rem;
        }}

        .test-description {{
            color: var(--text-secondary);
            font-size: 0.75rem;
        }}

        .test-duration {{
            font-family: 'Monaco', 'Menlo', monospace;
            color: var(--text-muted);
        }}

        /* 元数据面板 */
        .metadata-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}

        .metadata-item {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
        }}

        .metadata-label {{
            font-size: 0.625rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 0.25rem;
        }}

        .metadata-value {{
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-primary);
        }}

        /* 响应式 */
        @media (max-width: 768px) {{
            .dashboard-container {{
                padding: 1rem;
            }}
            
            .dashboard-header {{
                flex-direction: column;
                gap: 1rem;
                margin: -1rem -1rem 1rem -1rem;
                padding: 1rem;
            }}
            
            .health-overview {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .health-card-value {{
                font-size: 1.75rem;
            }}
            
            .tests-table {{
                font-size: 0.75rem;
            }}
            
            .tests-table th, .tests-table td {{
                padding: 0.5rem;
            }}
        }}

        /* 动画 */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .dashboard-header, .health-overview, .metrics-row, .error-budget, .alerts-panel, .tests-table-container {{
            animation: fadeIn 0.5s ease;
        }}

        .health-card:nth-child(1) {{ animation-delay: 0.05s; }}
        .health-card:nth-child(2) {{ animation-delay: 0.1s; }}
        .health-card:nth-child(3) {{ animation-delay: 0.15s; }}
        .health-card:nth-child(4) {{ animation-delay: 0.2s; }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <!-- 顶部导航 -->
        <header class="dashboard-header">
            <div class="header-left">
                <div class="logo">
                    <div class="logo-icon">📊</div>
                    {project_name}
                </div>
                <div class="header-status">
                    <span class="status-dot {health_class}"></span>
                    {health_status}
                </div>
            </div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">
                Generated: {generate_time}
            </div>
        </header>

        <!-- 健康状态概览 -->
        <div class="health-overview">
            <div class="health-card total">
                <div class="health-card-header">
                    <div class="health-card-title">总测试数</div>
                    <div class="health-card-icon">📋</div>
                </div>
                <div class="health-card-value">{total}</div>
                <div class="health-card-trend">Test Cases</div>
            </div>
            <div class="health-card passed">
                <div class="health-card-header">
                    <div class="health-card-title">通过</div>
                    <div class="health-card-icon">✓</div>
                </div>
                <div class="health-card-value">{passed}</div>
                <div class="health-card-trend">{pass_rate}% 通过率</div>
            </div>
            <div class="health-card failed">
                <div class="health-card-header">
                    <div class="health-card-title">失败</div>
                    <div class="health-card-icon">✗</div>
                </div>
                <div class="health-card-value">{failed}</div>
                <div class="health-card-trend">需关注</div>
            </div>
            <div class="health-card skipped">
                <div class="health-card-header">
                    <div class="health-card-title">跳过</div>
                    <div class="health-card-icon">⏭</div>
                </div>
                <div class="health-card-value">{skipped}</div>
                <div class="health-card-trend">未执行</div>
            </div>
        </div>

        <!-- 指标行 -->
        <div class="metrics-row">
            <!-- 通过率仪表盘 -->
            <div class="pass-rate-gauge">
                <div class="gauge-header">📈 通过率</div>
                <div class="gauge-container">
                    <svg class="gauge-svg" width="200" height="200" viewBox="0 0 200 200">
                        <circle class="gauge-bg" cx="100" cy="100" r="85"/>
                        <circle class="gauge-fill {gauge_class}" cx="100" cy="100" r="85" 
                            stroke-dasharray="534" stroke-dashoffset="{gauge_offset}"/>
                    </svg>
                    <div class="gauge-center">
                        <div class="gauge-value">{pass_rate}%</div>
                        <div class="gauge-label">Pass Rate</div>
                    </div>
                </div>
                <div class="gauge-status {gauge_class}">
                    {gauge_status}
                </div>
            </div>

            <!-- 模块健康度 -->
            <div class="module-health">
                <div class="section-header">🏥 模块健康度</div>
                <div class="module-grid">
                    {module_health_html}
                </div>
            </div>
        </div>

        <!-- 错误预算 -->
        {error_budget_html}

        <!-- 告警面板 -->
        {alerts_html}

        <!-- 环境信息 -->
        <div class="metadata-grid">
            <div class="metadata-item">
                <div class="metadata-label">项目版本</div>
                <div class="metadata-value">{project_version}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">测试环境</div>
                <div class="metadata-value">{test_env}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">开始时间</div>
                <div class="metadata-value">{start_time}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">执行时长</div>
                <div class="metadata-value">{duration}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Python版本</div>
                <div class="metadata-value">{python_version}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Pytest版本</div>
                <div class="metadata-value">{pytest_version}</div>
            </div>
        </div>

        <!-- 测试详情表 -->
        <div class="tests-table-container">
            <div class="tests-table-header">
                <div class="tests-table-title">📜 测试详情</div>
                <div class="filter-buttons">
                    <button class="filter-btn active" data-filter="all">全部 ({total})</button>
                    <button class="filter-btn" data-filter="passed">通过 ({passed})</button>
                    <button class="filter-btn" data-filter="failed">失败 ({failed})</button>
                    <button class="filter-btn" data-filter="skipped">跳过 ({skipped})</button>
                </div>
            </div>
            <table class="tests-table">
                <thead>
                    <tr>
                        <th>状态</th>
                        <th>测试用例</th>
                        <th>模块</th>
                        <th>耗时</th>
                    </tr>
                </thead>
                <tbody>
                    {test_rows_html}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // 筛选功能
        document.querySelectorAll('.filter-btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                const filter = this.dataset.filter;
                const rows = document.querySelectorAll('.test-row');
                
                rows.forEach(row => {{
                    if (filter === 'all' || row.dataset.status === filter) {{
                        row.style.display = '';
                    }} else {{
                        row.style.display = 'none';
                    }}
                }});
            }});
        }});

        // 进度条动画
        document.querySelectorAll('.budget-bar-used, .budget-bar-remaining').forEach(bar => {{
            const width = bar.style.width;
            bar.style.width = '0%';
            setTimeout(() => {{
                bar.style.width = width;
            }}, 100);
        }});
    </script>
</body>
</html>
"""

    # =========================================================================
    # 主方法
    # =========================================================================
    def generate(self, results: List[Dict], output_path: str = "reports/test_report.html",
                 metadata: Optional[Dict] = None) -> str:
        """生成SRE风格HTML报告"""
        self.results = results
        self.metadata = metadata or {}
        self._calculate_stats()
        self._analyze_failures()
        
        # 计算时长
        duration = ""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            duration = self._format_duration(delta.total_seconds())
        
        # 确定健康状态
        health_class, health_status = self._get_health_status()
        
        # 确定仪表盘状态
        gauge_class, gauge_offset, gauge_status = self._get_gauge_status()
        
        # 生成模块健康度HTML
        module_health_html = self._generate_module_health_html()
        
        # 生成错误预算HTML
        error_budget_html = self._generate_error_budget_html()
        
        # 生成告警面板HTML
        alerts_html = self._generate_alerts_html()
        
        # 生成测试详情行HTML
        test_rows_html = self._generate_test_rows_html()
        
        # 填充模板
        html = self.HTML_TEMPLATE.format(
            title=f"{self.project_name} - SRE监控仪表盘",
            project_name=self.project_name,
            project_version=self.project_version,
            health_class=health_class,
            health_status=health_status,
            generate_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total=self.summary['total'],
            passed=self.summary['passed'],
            failed=self.summary['failed'],
            skipped=self.summary['skipped'],
            pass_rate=f"{self.summary['pass_rate']:.1f}",
            gauge_class=gauge_class,
            gauge_offset=gauge_offset,
            gauge_status=gauge_status,
            module_health_html=module_health_html,
            error_budget_html=error_budget_html,
            alerts_html=alerts_html,
            test_rows_html=test_rows_html,
            test_env=self.metadata.get('test_env', '测试环境'),
            start_time=self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else "-",
            duration=duration,
            python_version=self.metadata.get('python_version', sys.version.split()[0]),
            pytest_version=self.metadata.get('pytest_version', 'N/A'),
        )
        
        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ SRE Dashboard报告已生成: {output_path}")
        return output_path

    def _calculate_stats(self):
        """计算统计数据"""
        self.summary['total'] = len(self.results)
        self.summary['passed'] = sum(1 for r in self.results if r['status'] == 'passed')
        self.summary['failed'] = sum(1 for r in self.results if r['status'] == 'failed')
        self.summary['skipped'] = sum(1 for r in self.results if r['status'] == 'skipped')
        self.summary['error'] = sum(1 for r in self.results if r['status'] == 'error')
        
        if self.summary['total'] > 0:
            self.summary['pass_rate'] = (self.summary['passed'] / self.summary['total']) * 100
        
        # 按模块统计
        for r in self.results:
            module = r.get('module', 'unknown')
            if module not in self.module_stats:
                self.module_stats[module] = {'passed': 0, 'failed': 0, 'skipped': 0, 'error': 0}
            self.module_stats[module][r['status']] = self.module_stats[module].get(r['status'], 0) + 1

    def _analyze_failures(self):
        """分析失败原因"""
        self.failure_analysis = []
        for r in self.results:
            if r['status'] in ('failed', 'error'):
                self.failure_analysis.append({
                    'name': r['name'],
                    'description': r.get('description', ''),
                    'type': r.get('failure_type', '断言失败'),
                    'message': r.get('error_message', ''),
                    'module': r.get('module', 'unknown'),
                    'duration': r.get('duration', 0),
                })

    def _get_health_status(self) -> tuple:
        """获取健康状态"""
        rate = self.summary['pass_rate']
        if rate >= 99:
            return 'healthy', '所有服务正常'
        elif rate >= 95:
            return 'degraded', '服务性能下降'
        else:
            return 'down', '服务中断'

    def _get_gauge_status(self) -> tuple:
        """获取仪表盘状态"""
        rate = self.summary['pass_rate']
        # 圆的周长 = 2 * π * 85 ≈ 534
        circumference = 534
        
        if rate >= 99:
            return 'excellent', str(int(circumference * (100 - rate) / 100)), '优秀 - 超过SLO目标'
        elif rate >= 95:
            return 'good', str(int(circumference * (100 - rate) / 100)), '良好 - 符合SLO'
        elif rate >= 80:
            return 'warning', str(int(circumference * (100 - rate) / 100)), '警告 - 接近错误预算上限'
        else:
            return 'critical', str(int(circumference * (100 - rate) / 100)), '严重 - 超出错误预算'

    def _generate_module_health_html(self) -> str:
        """生成模块健康度HTML"""
        html_parts = []
        for module, stats in sorted(self.module_stats.items()):
            total = stats['passed'] + stats['failed'] + stats['skipped'] + stats['error']
            if total == 0:
                rate = 100
            else:
                rate = (stats['passed'] / total) * 100
            
            if rate == 100:
                status_class = 'healthy'
            elif rate >= 80:
                status_class = 'degraded'
            else:
                status_class = 'down'
            
            html_parts.append(f"""
                <div class="module-item {status_class}">
                    <div class="module-name">{module}</div>
                    <div class="module-stats">
                        <span style="color: var(--success-light)">{stats['passed']}✓</span>
                        <span style="color: var(--danger-light)">{stats['failed']}✗</span>
                        <span style="color: var(--warning-light)">{stats['skipped']}○</span>
                    </div>
                    <div class="module-rate" style="color: {'var(--success-light)' if rate >= 95 else 'var(--warning-light)'}">{rate:.0f}%</div>
                </div>
            """)
        
        return ''.join(html_parts) if html_parts else '<div class="module-item healthy"><div class="module-name">无数据</div></div>'

    def _generate_error_budget_html(self) -> str:
        """生成错误预算HTML"""
        if self.summary['total'] == 0:
            return ""
        
        budget_used = self.summary['failed'] + self.summary['error']
        budget_total = self.summary['total']
        budget_remaining = budget_total - budget_used
        used_percent = (budget_used / budget_total) * 100
        remaining_percent = 100 - used_percent
        
        return f"""
        <div class="error-budget">
            <div class="section-header">⚠️ 错误预算 (Error Budget)</div>
            <div class="budget-bar-container">
                <div class="budget-bar-used" style="width: {used_percent}%"></div>
                <div class="budget-bar-remaining" style="width: {remaining_percent}%"></div>
            </div>
            <div class="budget-labels">
                <span>已消耗: {budget_used} ({used_percent:.1f}%)</span>
                <span>剩余: {budget_remaining} ({remaining_percent:.1f}%)</span>
            </div>
        </div>
        """

    def _generate_alerts_html(self) -> str:
        """生成告警面板HTML"""
        if not self.failure_analysis:
            return f"""
            <div class="alerts-panel">
                <div class="alerts-header">
                    <div class="alert-icon">✓</div>
                    <div class="alerts-title">无告警 - 所有测试通过</div>
                    <div class="alerts-count" style="background: var(--success)">0</div>
                </div>
            </div>
            """
        
        alerts = self.failure_analysis[:10]  # 最多显示10个
        alert_items = []
        
        for f in alerts:
            severity = 'critical' if f['type'] in ('断言失败', '超时', '网络问题') else 'warning'
            alert_items.append(f"""
                <div class="alert-item">
                    <span class="alert-severity {severity}">{f['type']}</span>
                    <div class="alert-content">
                        <div class="alert-test-name">{f['description'] or f['name']}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">
                            {f['module']} • {f['duration']:.2f}s
                        </div>
                        <div class="alert-message">{self._escape_html(f['message'][:300])}</div>
                    </div>
                </div>
            """)
        
        return f"""
        <div class="alerts-panel">
            <div class="alerts-header">
                <div class="alert-icon">!</div>
                <div class="alerts-title">检测到 {len(self.failure_analysis)} 个失败测试</div>
                <div class="alerts-count">{len(self.failure_analysis)}</div>
            </div>
            {''.join(alert_items)}
        </div>
        """

    def _generate_test_rows_html(self) -> str:
        """生成测试详情行HTML"""
        if not self.results:
            return '<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">暂无测试结果</td></tr>'
        
        html_parts = []
        for r in self.results:
            status_icon = {'passed': '✓', 'failed': '✗', 'skipped': '○', 'error': '!'}.get(r['status'], '?')
            duration = r.get('duration', 0)
            description = r.get('description', '') or r['name']
            
            html_parts.append(f"""
                <tr class="test-row" data-status="{r['status']}">
                    <td><span class="test-status {r['status']}">{status_icon} {r['status'].upper()}</span></td>
                    <td>
                        <div class="test-name">{r['name']}</div>
                        <div class="test-description">{description}</div>
                    </td>
                    <td>{r.get('module', 'unknown')}</td>
                    <td class="test-duration">{duration:.3f}s</td>
                </tr>
            """)
        
        return ''.join(html_parts)

    @staticmethod
    def _escape_html(text: str) -> str:
        """转义HTML特殊字符"""
        if not text:
            return ""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.0f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"


# =============================================================================
# 兼容旧接口
# =============================================================================
class TestReportGenerator(SREReportGenerator):
    """向后兼容的别名"""
    pass


# =============================================================================
# 主函数
# =============================================================================
def main():
    """从pytest JSON结果生成SRE风格报告"""
    import argparse

    parser = argparse.ArgumentParser(description='生成SRE Dashboard风格的pytest HTML报告')
    parser.add_argument('--input', '-i', default='reports/test_results.json',
                        help='pytest JSON结果文件')
    parser.add_argument('--output', '-o', default='reports/test_report.html',
                        help='输出HTML报告路径')
    parser.add_argument('--project', default='Quality_Manage_platform',
                        help='项目名称')
    parser.add_argument('--version', default='v1.0.0',
                        help='项目版本')

    args = parser.parse_args()

    # 读取JSON结果
    if os.path.exists(args.input):
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        print(f"⚠️ 找不到JSON结果文件: {args.input}")
        print("请先运行: pytest")
        return

    # 解析数据
    results = data.get('results', data.get('test_results', []))
    metadata = data.get('metadata', {})

    # 生成报告
    generator = SREReportGenerator(args.project, args.version)
    if metadata.get('start_time'):
        generator.start_time = datetime.fromisoformat(metadata['start_time'])
    if metadata.get('end_time'):
        generator.end_time = datetime.fromisoformat(metadata['end_time'])
    
    html_path = generator.generate(results, args.output, metadata)
    print(f"✅ 报告已生成: {html_path}")


if __name__ == '__main__':
    main()
