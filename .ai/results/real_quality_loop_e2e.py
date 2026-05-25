#!/usr/bin/env python3
"""
真实系统接口 E2E 质量闭环验证脚本

验证完整链路：
启动后端服务 -> 登录 -> 创建用例 -> 创建场景 -> 添加步骤 ->
执行场景 -> 轮询执行结果 -> 确认自动生成报告 -> 一键评估门禁

使用本系统自己的 /api/health 作为被测接口。
"""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime

BASE_URL = "http://localhost:8000"
RESULTS = []


def log(msg):
    """打印带时间戳的日志"""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    # 替换可能引起 GBK 编码错误的特殊字符
    safe_msg = msg.replace("✓", "[OK]").replace("✗", "[FAIL]").replace("✔", "[OK]").replace("✖", "[FAIL]")
    try:
        print(f"[{ts}] {safe_msg}")
    except UnicodeEncodeError:
        print(f"[{ts}] [log output]")
    RESULTS.append(f"[{ts}] {msg}")


def api_call(method, path, data=None, token=None, silent=False):
    """发送 HTTP 请求，返回 (status_code, body_dict)"""
    url = BASE_URL + path
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            try:
                body = json.loads(resp.read().decode("utf-8"))
            except Exception:
                body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = e.read().decode("utf-8")
    except Exception as e:
        status = 0
        body = str(e)

    if not silent:
        log(f"  {method} {path} -> {status}")
    return status, body


def wait_for_backend(timeout=15):
    """等待后端服务就绪"""
    log("等待后端服务启动...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            status, _ = api_call("GET", "/api/health", silent=True)
            if status == 200:
                log("后端服务已就绪")
                return True
        except Exception:
            pass
        time.sleep(1)
    log("后端服务未能在预期时间内启动")
    return False


def main():
    print("=" * 70)
    print("真实系统接口 E2E 质量闭环验证")
    print("=" * 70)

    # 步骤 0：确认后端健康
    if not wait_for_backend():
        print("无法连接到后端服务，退出")
        return

    status, body = api_call("GET", "/api/health")
    if status != 200:
        print(f"健康检查失败: {status} {body}")
        return
    log(f"健康检查: {json.dumps(body, ensure_ascii=False)}")

    # 步骤 1：登录
    log("步骤1：登录系统")
    status, body = api_call("POST", "/api/auth/login", {"username": "admin", "password": "admin123"})
    if status != 200:
        print(f"登录失败: {status} {body}")
        return
    token = body.get("access_token")
    if not token:
        print(f"未获取到 access_token: {body}")
        return
    log(f"登录成功，token 前10位: {token[:10]}...")

    # 步骤 2：创建用例
    ts = datetime.now().strftime("%m%d%H%M%S")
    log(f"步骤2：创建 API 用例 E2E-{ts}")
    case_data = {
        "name": f"E2E-真实接口-{ts}",
        "description": "使用本系统 /api/health 验证真实质量闭环",
        "priority": "P1",
        "tags": ["e2e", "real-api"],
        "case_type": "api",
        "is_automated": True,
        "method": "GET",
        "url": "http://localhost:8000/api/health",
        "headers": {},
        "params": {},
        "body_type": "none",
        "body": "",
        "expected_status": 200,
        "assertions": [{"type": "status_code", "operator": "equals", "expected": 200}],
    }
    status, body = api_call("POST", "/api/case", case_data, token)
    if status not in (200, 201):
        print(f"创建用例失败: {status} {body}")
        return
    case_id = body.get("id") or (body.get("data", {}).get("id") if isinstance(body, dict) else None)
    if not case_id:
        # 尝试从响应体提取
        if isinstance(body, dict):
            case_id = body.get("id")
            if not case_id and "data" in body:
                case_id = body["data"].get("id") if isinstance(body["data"], dict) else None
        if not case_id:
            print(f"无法获取 case_id，响应: {body}")
            return
    log(f"用例创建成功，case_id={case_id}")

    # 步骤 3：创建场景
    log(f"步骤3：创建场景 E2E-{ts}")
    scenario_data = {
        "name": f"E2E-场景-{ts}",
        "description": "用平台自己的 /api/health 接口验证场景执行到报告门禁闭环",
        "scenario_type": "api",
        "priority": "P1",
        "version": 1,
        "status": "active",
    }
    status, body = api_call("POST", "/api/scenario", scenario_data, token)
    if status not in (200, 201):
        print(f"创建场景失败: {status} {body}")
        return
    scenario_id = body.get("id") or (body.get("data", {}).get("id") if isinstance(body, dict) else None)
    if not scenario_id:
        if isinstance(body, dict):
            scenario_id = body.get("id")
            if not scenario_id and "data" in body:
                scenario_id = body["data"].get("id") if isinstance(body["data"], dict) else None
        if not scenario_id:
            print(f"无法获取 scenario_id，响应: {body}")
            return
    log(f"场景创建成功，scenario_id={scenario_id}")

    # 步骤 4：添加场景步骤
    log(f"步骤4：添加场景步骤 case_id={case_id}")
    step_data = {
        "case_id": case_id,
        "name": "调用本系统健康检查接口",
        "sort_order": 1,
        "enabled": True,
        "retry_count": 0,
        "timeout_ms": 30000,
        "failure_strategy": "stop",
        "extract_rules": [],
        "inject_rules": [],
    }
    status, body = api_call("POST", f"/api/scenario/{scenario_id}/steps", step_data, token)
    if status not in (200, 201):
        print(f"添加步骤失败: {status} {body}")
        return
    step_id = None
    if isinstance(body, dict):
        step_id = body.get("id") or body.get("step_id")
        if not step_id and "data" in body:
            step_id = body["data"].get("id") if isinstance(body["data"], dict) else None
    log(f"步骤添加成功，step_id={step_id}")

    # 步骤 5：执行场景
    log(f"步骤5：执行场景 scenario_id={scenario_id}")
    status, body = api_call("POST", f"/api/scenario/{scenario_id}/run", None, token)
    if status not in (200, 201):
        print(f"执行场景失败: {status} {body}")
        return
    run_id = None
    if isinstance(body, dict):
        run_id = body.get("id") or body.get("run_id")
        if not run_id and "data" in body:
            run_id = body["data"].get("id") if isinstance(body["data"], dict) else None
    if not run_id:
        # 从响应中尝试提取
        if isinstance(body, dict):
            for k in ("id", "run_id", "data"):
                v = body.get(k)
                if isinstance(v, dict):
                    run_id = v.get("id") or v.get("run_id")
                    if run_id:
                        break
                elif isinstance(v, int):
                    run_id = v
                    break
        if not run_id:
            print(f"无法获取 run_id，响应: {body}")
            return
    log(f"场景执行启动，run_id={run_id}")

    # 步骤 6：轮询执行结果
    log(f"步骤6：轮询执行结果 run_id={run_id}")
    max_wait = 60
    interval = 2
    elapsed = 0
    final_run = None
    while elapsed < max_wait:
        status, body = api_call("GET", f"/api/scenario/runs/{run_id}", None, token)
        if status == 200 and isinstance(body, dict):
            run_status = body.get("status")
            log(f"  当前状态: {run_status}")
            if run_status in ("passed", "failed", "stopped"):
                final_run = body
                break
        elapsed += interval
        time.sleep(interval)

    if not final_run:
        log("执行超时，未获取到终态结果")
        return

    run_status = final_run.get("status")
    summary = final_run.get("summary", {})
    log(f"执行完成，状态={run_status}，summary={json.dumps(summary, ensure_ascii=False)}")

    # 步骤 7：确认自动生成报告
    log(f"步骤7：查询自动生成的报告 run_id={run_id}")
    time.sleep(2)  # 等待报告生成
    status, body = api_call("GET", "/api/reports?report_type=execution&page=1&page_size=50", None, token)
    if status != 200:
        print(f"查询报告失败: {status} {body}")
        return

    items = body.get("items", []) if isinstance(body, dict) else []
    target_report = None
    for r in items:
        if r.get("target_id") == run_id and r.get("report_type") == "execution":
            target_report = r
            break

    if not target_report:
        # 尝试更多页
        total = body.get("total", 0) if isinstance(body, dict) else 0
        pages = (total // 50) + 2
        for p in range(2, pages):
            status, body = api_call("GET", f"/api/reports?report_type=execution&page={p}&page_size=50", None, token)
            if status != 200:
                break
            for r in (body.get("items", []) if isinstance(body, dict) else []):
                if r.get("target_id") == run_id and r.get("report_type") == "execution":
                    target_report = r
                    break
            if target_report:
                break

    if not target_report:
        print(f"未找到自动生成的报告，run_id={run_id}，报告列表前5: {items[:5]}")
        return

    report_id = target_report.get("id")
    log(f"自动报告生成成功，report_id={report_id}")
    log(f"  summary={json.dumps(target_report.get('summary', {}), ensure_ascii=False)}")
    log(f"  metrics={json.dumps(target_report.get('metrics', {}), ensure_ascii=False)}")

    # 步骤 8：创建质量门禁
    log(f"步骤8：创建质量门禁")
    gate_data = {
        "name": f"E2E-门禁-{ts}",
        "description": "真实 E2E 验证用门禁",
        "gate_type": "execution",
        "enabled": True,
        "conditions": [
            {"metric": "pass_rate", "operator": ">=", "threshold": 100},
            {"metric": "avg_duration", "operator": "<=", "threshold": 60000},
        ],
        "gate_level": "blocking",
        "scope_filter": {},
    }
    status, body = api_call("POST", "/api/reports/quality-gates", gate_data, token)
    if status not in (200, 201):
        print(f"创建门禁失败: {status} {body}")
        return
    gate_id = None
    if isinstance(body, dict):
        gate_id = body.get("id")
        if not gate_id and "data" in body:
            gate_id = body["data"].get("id") if isinstance(body["data"], dict) else None
    if not gate_id:
        if isinstance(body, dict):
            gate_id = body.get("id")
        if not gate_id:
            print(f"无法获取 gate_id，响应: {body}")
            return
    log(f"门禁创建成功，gate_id={gate_id}")

    # 步骤 9：基于报告一键评估门禁
    log(f"步骤9：一键评估门禁 report_id={report_id}")
    status, body = api_call("POST", f"/api/reports/{report_id}/quality-gates/evaluate", None, token)
    if status != 200:
        print(f"门禁评估失败: {status} {body}")
        return

    log(f"Gate evaluation result received")

    evaluations = body.get("evaluations", []) if isinstance(body, dict) else []
    our_gate_result = None
    for ev in evaluations:
        if ev.get("gate_id") == gate_id:
            our_gate_result = ev
            break

    if not our_gate_result and evaluations:
        our_gate_result = evaluations[0]

    # 输出最终结论
    print("\n" + "=" * 70)
    print("E2E Verification Results")
    print("=" * 70)
    print(f"case_id:      {case_id}")
    print(f"scenario_id:  {scenario_id}")
    print(f"step_id:      {step_id}")
    print(f"run_id:       {run_id}")
    print(f"report_id:    {report_id}")
    print(f"gate_id:      {gate_id}")
    print(f"run_status:               {run_status}")
    print(f"run summary:           {json.dumps(summary, ensure_ascii=False)}")
    print(f"report summary:           {json.dumps(target_report.get('summary', {}), ensure_ascii=False)}")
    if our_gate_result:
        print(f"gate overall_result:           {our_gate_result.get('overall_result')}")
        details = our_gate_result.get('details', [])
        # Replace unicode characters that may cause GBK encode errors
        details_str = json.dumps(details, ensure_ascii=False).replace("✓", "[OK]").replace("✗", "[FAIL]")
        print(f"gate details:              {details_str}")
    print("=" * 70)

    if run_status == "passed" and target_report.get("summary", {}).get("pass_rate") == 100.0:
        if our_gate_result and our_gate_result.get("overall_result") == "pass":
            print("[PASS] E2E Quality Loop Verification Passed")
        else:
            print("[WARN] Execution and report correct, but gate result is not pass")
    else:
        print(f"[FAIL] Execution status or report data abnormal: status={run_status}, pass_rate={target_report.get('summary', {}).get('pass_rate')}")


if __name__ == "__main__":
    main()