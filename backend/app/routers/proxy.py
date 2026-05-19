import httpx
import time
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

router = APIRouter()


class ProxyRequest(BaseModel):
    """代理请求模型"""
    method: str = "GET"  # GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
    url: str
    headers: Optional[Dict[str, str]] = {}
    params: Optional[Dict[str, str]] = {}
    body: Optional[str] = None
    timeout: int = 30  # 超时秒数


class BatchProxyRequest(BaseModel):
    """批量代理请求模型"""
    requests: List[ProxyRequest]
    concurrency: int = 1  # 并发数


@router.post("/")
async def forward_request(req: ProxyRequest):
    """单次请求转发"""
    start_time = time.time()

    # 验证 URL
    if not req.url:
        raise HTTPException(status_code=400, detail="URL is required")

    # 转换 headers 的 key 为小写（避免重复）
    headers = {k.lower(): v for k, v in req.headers.items()} if req.headers else {}

    # 构建 httpx 客户端配置
    # 注意：若 params 为空，则不传（让 httpx 使用 URL 中的 query string）
    client_config = {
        "method": req.method.upper(),
        "url": req.url,
        "headers": headers,
        "timeout": httpx.Timeout(req.timeout),
        "follow_redirects": True,
    }
    if req.params:
        client_config["params"] = req.params

    # 添加 body（仅 POST/PUT/PATCH）
    if req.body and req.method.upper() in ("POST", "PUT", "PATCH"):
        client_config["content"] = req.body.encode("utf-8") if isinstance(req.body, str) else req.body

    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(**client_config)

        duration_ms = round((time.time() - start_time) * 1000, 2)

        # 提取响应头（仅取必要的）
        response_headers = {}
        for key, value in response.headers.items():
            if key.lower() not in ("content-encoding", "transfer-encoding", "connection"):
                response_headers[key] = value

        # 响应内容（限制大小 5MB）
        content = response.text
        if len(content) > 5 * 1024 * 1024:
            content = content[:5 * 1024 * 1024] + "\n... [内容已截断，超出 5MB 限制]"

        return {
            "success": True,
            "status_code": response.status_code,
            "status_text": response.reason_phrase,
            "headers": response_headers,
            "content": content,
            "content_size": len(response.content),
            "duration_ms": duration_ms,
        }

    except httpx.TimeoutException:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        raise HTTPException(
            status_code=504,
            detail={
                "success": False,
                "error": "Request timeout",
                "duration_ms": duration_ms,
            }
        )
    except httpx.RequestError as e:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        raise HTTPException(
            status_code=502,
            detail={
                "success": False,
                "error": f"Request failed: {str(e)}",
                "duration_ms": duration_ms,
            }
        )
    except Exception as e:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Internal error: {str(e)}",
                "duration_ms": duration_ms,
            }
        )


@router.post("/batch")
async def batch_forward_requests(req: BatchProxyRequest):
    """批量请求转发"""
    results = []

    async def send_one(r: ProxyRequest, index: int):
        try:
            # 每个请求独立创建 client
            async with httpx.AsyncClient() as client:
                start_time = time.time()

                headers = {k.lower(): v for k, v in r.headers.items()} if r.headers else {}

                client_config = {
                    "method": r.method.upper(),
                    "url": r.url,
                    "headers": headers,
                    "timeout": httpx.Timeout(r.timeout),
                    "follow_redirects": True,
                }
                if r.params:
                    client_config["params"] = r.params

                if r.body and r.method.upper() in ("POST", "PUT", "PATCH"):
                    client_config["content"] = r.body.encode("utf-8") if isinstance(r.body, str) else r.body

                response = await client.request(**client_config)
                duration_ms = round((time.time() - start_time) * 1000, 2)

                return {
                    "index": index,
                    "success": True,
                    "status_code": response.status_code,
                    "status_text": response.reason_phrase,
                    "content": response.text[:1024] if response.text else "",  # 批量只返回前 1KB
                    "duration_ms": duration_ms,
                }
        except Exception as e:
            return {
                "index": index,
                "success": False,
                "error": str(e),
            }

    # 简单并发控制
    if req.concurrency <= 1:
        # 串行执行
        for i, r in enumerate(req.requests):
            result = await send_one(r, i)
            results.append(result)
    else:
        # 并发执行
        import asyncio
        semaphore = asyncio.Semaphore(req.concurrency)

        async def bounded_send(r: ProxyRequest, i: int):
            async with semaphore:
                return await send_one(r, i)

        tasks = [bounded_send(r, i) for i, r in enumerate(req.requests)]
        results = await asyncio.gather(*tasks)

    # 按顺序返回
    results.sort(key=lambda x: x["index"])

    success_count = sum(1 for r in results if r.get("success"))
    fail_count = len(results) - success_count
    durations = [r["duration_ms"] for r in results if r.get("success") and r.get("duration_ms")]

    return {
        "total": len(results),
        "success": success_count,
        "failed": fail_count,
        "avg_duration_ms": round(sum(durations) / len(durations), 2) if durations else 0,
        "min_duration_ms": min(durations) if durations else 0,
        "max_duration_ms": max(durations) if durations else 0,
        "results": results,
    }
