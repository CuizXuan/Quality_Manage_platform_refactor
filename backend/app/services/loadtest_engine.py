"""
Load Test Engine - 压力测试引擎
基于 asyncio + httpx.AsyncClient 实现并发请求
"""
import asyncio
import json
import time
import statistics
import httpx
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from app.services.variable_engine import VariableEngine


class LoadTestEngine:
    """压力测试引擎"""

    def __init__(self):
        self._tests: dict[str, dict] = {}  # test_id -> test data
        self.var_engine = VariableEngine()

    async def run_loadtest(
        self,
        case_data: dict,
        config: dict,
        env_vars: dict
    ) -> dict:
        """
        运行压力测试
        case_data: 用例数据（会被变量引擎处理后执行）
        config: {concurrency: int, total_requests: int, duration: int, ramp_up_time: int}
        env_vars: 环境变量
        返回: 测试结果
        """
        test_id = f"loadtest_{int(time.time() * 1000)}"

        concurrency = config.get("concurrency", 10)
        total_requests = config.get("total_requests", 1000)
        duration = config.get("duration", 0)  # 0 表示按 total_requests 限制
        ramp_up_time = config.get("ramp_up_time", 0)

        # 初始化测试数据
        self._tests[test_id] = {
            "test_id": test_id,
            "status": "running",
            "start_time": time.time(),
            "concurrency": concurrency,
            "total_requests": total_requests,
            "duration": duration,
            "ramp_up_time": ramp_up_time,
            "response_times": [],  # 响应时间列表（毫秒）
            "status_codes": [],  # 状态码列表
            "errors": [],  # 错误信息列表
            "request_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "stop_event": asyncio.Event(),
        }

        test_info = self._tests[test_id]

        # 构建变量空间
        self.var_engine.clear()
        self.var_engine.set_variables("global", {})
        self.var_engine.set_variables("environment", env_vars or {})
        self.var_engine.set_variables("scenario", {})
        self.var_engine.set_variables("data", {})
        self.var_engine.set_variables("step", {})

        # 替换用例数据
        processed_case = self.var_engine.replace_dict(case_data)

        # 选择执行函数
        if duration > 0:
            # 按时长执行
            await self._run_duration_based(
                test_id, processed_case, concurrency, duration, ramp_up_time
            )
        else:
            # 按请求数执行
            await self._run_count_based(
                test_id, processed_case, concurrency, total_requests, ramp_up_time
            )

        # 计算最终指标
        self._tests[test_id]["status"] = "completed"
        self._tests[test_id]["end_time"] = time.time()
        final_metrics = self.get_metrics(test_id)

        return final_metrics

    async def _run_count_based(
        self,
        test_id: str,
        case_data: dict,
        concurrency: int,
        total_requests: int,
        ramp_up_time: int
    ):
        """按请求数执行的测试"""
        test_info = self._tests[test_id]
        stop_event = test_info["stop_event"]

        # 计算每个 worker 的任务数
        tasks_per_worker = total_requests // concurrency
        extra_tasks = total_requests % concurrency

        # ramp_up 期间每个 worker 增量启动
        async def worker(worker_id: int, num_requests: int, start_delay: float):
            if ramp_up_time > 0 and worker_id > 0:
                delay = (ramp_up_time / concurrency) * worker_id
                await asyncio.sleep(delay)

            async with httpx.AsyncClient(timeout=case_data.get("timeout", 30)) as client:
                for i in range(num_requests):
                    if stop_event.is_set():
                        break
                    await self._execute_request(
                        test_id, client, case_data, case_data.get("timeout", 30)
                    )

        # 创建 worker 任务
        workers = []
        for i in range(concurrency):
            num_req = tasks_per_worker + (1 if i < extra_tasks else 0)
            if num_req > 0:
                workers.append(worker(i, num_req, 0))

        await asyncio.gather(*workers, return_exceptions=True)

    async def _run_duration_based(
        self,
        test_id: str,
        case_data: dict,
        concurrency: int,
        duration: int,
        ramp_up_time: int
    ):
        """按时长执行的测试"""
        test_info = self._tests[test_id]
        stop_event = test_info["stop_event"]

        async def worker(worker_id: int):
            if ramp_up_time > 0 and worker_id > 0:
                delay = (ramp_up_time / concurrency) * worker_id
                await asyncio.sleep(delay)

            async with httpx.AsyncClient(timeout=case_data.get("timeout", 30)) as client:
                end_time = time.time() + duration
                while time.time() < end_time:
                    if stop_event.is_set():
                        break
                    await self._execute_request(
                        test_id, client, case_data, case_data.get("timeout", 30)
                    )

        workers = [worker(i) for i in range(concurrency)]
        await asyncio.gather(*workers, return_exceptions=True)

    async def _execute_request(
        self,
        test_id: str,
        client: httpx.AsyncClient,
        case_data: dict,
        timeout: int
    ):
        """执行单个请求并记录指标"""
        test_info = self._tests[test_id]
        method = case_data.get("method", "GET").upper()
        url = case_data.get("url", "")
        headers = case_data.get("headers", {})
        params = case_data.get("params", {})
        body = case_data.get("body", "")
        body_type = case_data.get("body_type", "json")
        verify_ssl = case_data.get("verify_ssl", True)

        start_time = time.time()
        status_code = 0
        error_msg = ""

        try:
            req_headers = {str(k): str(v) for k, v in headers.items() if v}
            req_params = {str(k): str(v) for k, v in params.items() if v}

            request_kwargs = {
                "method": method,
                "url": url,
                "headers": req_headers,
                "timeout": timeout,
            }

            if method in ("POST", "PUT", "PATCH"):
                if body_type == "json":
                    try:
                        request_kwargs["json"] = json.loads(body) if isinstance(body, str) else body
                    except json.JSONDecodeError:
                        request_kwargs["content"] = body
                else:
                    request_kwargs["content"] = body

            if req_params:
                request_kwargs["params"] = req_params

            resp = await client.request(**request_kwargs, verify=verify_ssl)
            status_code = resp.status_code

        except asyncio.TimeoutError:
            error_msg = "Request timeout"
        except httpx.TimeoutException:
            error_msg = "Request timeout"
        except httpx.ConnectError as e:
            error_msg = f"Connection error: {str(e)}"
        except Exception as e:
            error_msg = f"Error: {str(e)}"

        elapsed_ms = int((time.time() - start_time) * 1000)

        # 记录指标
        test_info["response_times"].append(elapsed_ms)
        test_info["status_codes"].append(status_code)
        if error_msg:
            test_info["errors"].append(error_msg)
            test_info["failure_count"] += 1
        else:
            test_info["success_count"] += 1
        test_info["request_count"] += 1

    async def stop_loadtest(self, test_id: str):
        """停止压测"""
        if test_id in self._tests:
            self._tests[test_id]["stop_event"].set()
            self._tests[test_id]["status"] = "stopped"
            self._tests[test_id]["end_time"] = time.time()

    def get_metrics(self, test_id: str) -> dict:
        """获取测试指标"""
        if test_id not in self._tests:
            return {"error": "Test not found"}

        test_info = self._tests[test_id]
        response_times = test_info["response_times"]

        if not response_times:
            return {
                "test_id": test_id,
                "status": test_info["status"],
                "request_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "success_rate": 0,
                "tps": 0,
                "avg_rt": 0,
                "min_rt": 0,
                "max_rt": 0,
                "p50": 0,
                "p90": 0,
                "p95": 0,
                "p99": 0,
                "error_distribution": {},
                "status_code_distribution": {},
            }

        # 计算时间窗口和 TPS
        start_time = test_info["start_time"]
        end_time = test_info.get("end_time", time.time())
        duration_sec = end_time - start_time

        total_count = test_info["request_count"]
        success_count = test_info["success_count"]
        failure_count = test_info["failure_count"]

        # TPS = 成功请求数 / 耗时
        tps = success_count / duration_sec if duration_sec > 0 else 0

        # 响应时间统计
        sorted_times = sorted(response_times)
        n = len(sorted_times)

        # 状态码分布
        status_dist = {}
        for code in test_info["status_codes"]:
            status_dist[code] = status_dist.get(code, 0) + 1

        # 错误分布
        error_dist = {}
        for err in test_info["errors"]:
            error_dist[err] = error_dist.get(err, 0) + 1

        def percentile(data, p):
            if not data:
                return 0
            idx = int(len(data) * p / 100)
            idx = min(idx, len(data) - 1)
            return data[idx]

        return {
            "test_id": test_id,
            "status": test_info["status"],
            "start_time": start_time,
            "end_time": test_info.get("end_time", time.time()),
            "duration_sec": round(duration_sec, 2),
            "concurrency": test_info["concurrency"],
            "total_requests": test_info["total_requests"],
            "request_count": total_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": round(success_count / total_count * 100, 2) if total_count > 0 else 0,
            "tps": round(tps, 2),
            "avg_rt": round(statistics.mean(response_times), 2),
            "min_rt": min(response_times),
            "max_rt": max(response_times),
            "p50": percentile(sorted_times, 50),
            "p90": percentile(sorted_times, 90),
            "p95": percentile(sorted_times, 95),
            "p99": percentile(sorted_times, 99),
            "error_distribution": error_dist,
            "status_code_distribution": status_dist,
        }
