"""
AgentWatch SDK 客户端
连接 AgentWatch API 并管理 Traces
"""

import os
import uuid
import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
import json

import httpx


@dataclass
class AgentWatchConfig:
    """AgentWatch 配置"""
    
    api_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    timeout: float = 30.0
    auto_start: bool = True  # 自动创建trace
    
    # 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0  # 初始延迟（秒）
    retry_multiplier: float = 2.0  # 指数退避乘数
    retry_on_timeout: bool = True
    retry_on_connection: bool = True
    retry_on_server_error: bool = True


class AgentWatch:
    """
    AgentWatch SDK 主客户端

    使用示例:
        aw = AgentWatch()

        # 手动追踪
        trace = aw.create_trace(
            agent_id="my_agent",
            agent_name="MyAgent",
            provider="openai",
            model="gpt-4o"
        )

        # 添加事件
        trace.add_event("call", input_tokens=100)
        trace.add_event("response", output_tokens=200)
        trace.complete()

        # 或使用上下文管理器自动追踪
        with aw.trace("my_agent", model="gpt-4o") as t:
            result = llm_call()
            t.log_tokens(input=100, output=result.tokens)
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[AgentWatchConfig] = None,
    ):
        self.config = config or AgentWatchConfig()

        if api_url:
            self.config.api_url = api_url
        if api_key:
            self.config.api_key = api_key

        # 从环境变量读取
        self.config.api_url = os.getenv("AGENTWATCH_API_URL", self.config.api_url)
        self.config.api_key = os.getenv("AGENTWATCH_API_KEY", self.config.api_key)

        self._client = httpx.Client(timeout=self.config.timeout)
        self._active_traces: Dict[str, "TraceContext"] = {}

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _request(self, method: str, path: str, data: Optional[Dict] = None) -> Dict:
        """
        发送请求（带重试机制）
        
        Args:
            method: HTTP 方法 (GET/POST/PUT/DELETE)
            path: API 路径
            data: 请求体数据
            
        Returns:
            API 响应数据
            
        Raises:
            ConnectionError: 网络连接失败
            AuthenticationError: 认证失败
            RateLimitError: 请求频率超限
            ServerError: 服务器错误
            TimeoutError: 超时
            APIError: 其他 API 错误
        """
        from .exceptions import (
            ConnectionError as AWConnectionError,
            AuthenticationError,
            APIError,
            RateLimitError,
            ServerError,
            TimeoutError as AWTimeoutError,
            is_retryable_error,
            get_retry_delay,
        )
        
        url = f"{self.config.api_url}{path}"
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if method == "GET":
                    resp = self._client.get(url, headers=self._get_headers())
                elif method == "POST":
                    resp = self._client.post(url, headers=self._get_headers(), json=data)
                elif method == "PUT":
                    resp = self._client.put(url, headers=self._get_headers(), json=data)
                elif method == "DELETE":
                    resp = self._client.delete(url, headers=self._get_headers())
                else:
                    raise ValueError(f"Unknown method: {method}")
                
                # 成功响应
                if resp.status_code < 400:
                    return resp.json()
                
                # 处理错误响应
                if resp.status_code == 401:
                    raise AuthenticationError(
                        message="Invalid API key",
                        request_id=resp.headers.get("x-request-id"),
                    )
                
                if resp.status_code == 404:
                    raise APIError(
                        message=f"Not found: {path}",
                        status_code=404,
                        request_id=resp.headers.get("x-request-id"),
                    )
                
                if resp.status_code == 400:
                    body = resp.text[:500]
                    raise APIError(
                        message=f"Bad request: {body}",
                        status_code=400,
                        request_id=resp.headers.get("x-request-id"),
                    )
                
                if resp.status_code == 429:
                    retry_after = resp.headers.get("retry-after")
                    raise RateLimitError(
                        message="Rate limit exceeded",
                        retry_after=int(retry_after) if retry_after else None,
                        request_id=resp.headers.get("x-request-id"),
                    )
                
                if resp.status_code >= 500:
                    raise ServerError(
                        message=f"Server error: {resp.status_code}",
                        status_code=resp.status_code,
                        request_id=resp.headers.get("x-request-id"),
                    )
                
                # 其他错误
                raise APIError(
                    message=f"API error: {resp.status_code}",
                    status_code=resp.status_code,
                    request_id=resp.headers.get("x-request-id"),
                )
                
            except httpx.TimeoutException as e:
                last_error = AWTimeoutError(
                    message=f"Request timeout after {self.config.timeout}s",
                    timeout_seconds=self.config.timeout,
                    operation=path,
                )
                
                # 是否重试
                if attempt < self.config.max_retries and self.config.retry_on_timeout:
                    delay = self.config.retry_delay * (self.config.retry_multiplier ** attempt)
                    time.sleep(delay)
                    continue
                raise last_error
                
            except httpx.ConnectError as e:
                last_error = AWConnectionError(
                    message=f"Failed to connect to {self.config.api_url}",
                    api_url=self.config.api_url,
                )
                
                # 是否重试
                if attempt < self.config.max_retries and self.config.retry_on_connection:
                    delay = self.config.retry_delay * (self.config.retry_multiplier ** attempt)
                    time.sleep(delay)
                    continue
                raise last_error
                
            except httpx.HTTPStatusError as e:
                # 已在上面处理，这里只是捕获
                raise
                
            except Exception as e:
                # 其他异常（如 RateLimitError, ServerError）
                if hasattr(e, 'code') and is_retryable_error(e):
                    last_error = e
                    
                    if attempt < self.config.max_retries:
                        delay = get_retry_delay(e) if isinstance(e, RateLimitError) else \
                                self.config.retry_delay * (self.config.retry_multiplier ** attempt)
                        time.sleep(delay)
                        continue
                raise
        
        # 所有重试失败
        if last_error:
            raise last_error
        
        raise AWConnectionError(message="Unknown error after retries")

    def health_check(self) -> Dict:
        """健康检查"""
        return self._request("GET", "/health")

    def create_trace(
        self,
        agent_id: str,
        agent_name: str,
        provider: str,
        model: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        prompt: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> "TraceContext":
        """创建 Trace"""
        data = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "provider": provider,
            "model": model,
            "session_id": session_id,
            "user_id": user_id,
            "prompt": prompt,
            "metadata": metadata or {},
        }

        result = self._request("POST", "/api/v1/trace", data)

        if "error" in result:
            raise Exception(f"Failed to create trace: {result['error']}")

        trace = TraceContext(
            trace_id=result["trace_id"],
            agent_id=agent_id,
            agent_name=agent_name,
            provider=provider,
            model=model,
            client=self,
        )

        self._active_traces[trace.trace_id] = trace
        return trace

    def get_trace(self, trace_id: str) -> Dict:
        """获取 Trace 详情"""
        return self._request("GET", f"/api/v1/trace/{trace_id}")

    def list_traces(
        self,
        page: int = 1,
        page_size: int = 20,
        agent_id: Optional[str] = None,
        provider: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict:
        """列出 Traces"""
        params = {"page": page, "page_size": page_size}
        if agent_id:
            params["agent_id"] = agent_id
        if provider:
            params["provider"] = provider
        if status:
            params["status"] = status

        path = "/api/v1/traces?" + "&".join(f"{k}={v}" for k, v in params.items())
        return self._request("GET", path)

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self._request("GET", "/stats")

    def get_cost_summary(self, provider: Optional[str] = None) -> Dict:
        """获取成本汇总"""
        path = "/api/v1/cost/summary"
        if provider:
            path += f"?provider={provider}"
        return self._request("GET", path)

    def trace(
        self,
        agent_name: str,
        model: str,
        provider: str = "openai",
        agent_id: Optional[str] = None,
        **kwargs,
    ) -> "TraceContext":
        """
        上下文管理器 - 自动追踪

        使用示例:
            with aw.trace("my_agent", model="gpt-4o") as t:
                result = llm_call()
                t.log_tokens(input=100, output=200)
        """
        agent_id = agent_id or f"agent_{uuid.uuid4().hex[:8]}"

        trace = self.create_trace(
            agent_id=agent_id,
            agent_name=agent_name,
            provider=provider,
            model=model,
            **kwargs,
        )

        return trace

    def close(self):
        """关闭客户端"""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class TraceContext:
    """
    Trace 上下文管理器

    自动管理 trace 的生命周期
    """

    def __init__(
        self,
        trace_id: str,
        agent_id: str,
        agent_name: str,
        provider: str,
        model: str,
        client: AgentWatch,
    ):
        self.trace_id = trace_id
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.provider = provider
        self.model = model
        self._client = client

        self._start_time = time.time()
        self._events: list = []
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._status = "running"

    def add_event(
        self,
        event_type: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: Optional[int] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """添加事件"""
        event_id = f"ev_{uuid.uuid4().hex[:8]}"
        latency = latency_ms or int((time.time() - self._start_time) * 1000)

        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens

        event = {
            "event_id": event_id,
            "event_type": event_type,
            "model": self.model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency,
            "content": content,
            "metadata": metadata or {},
        }

        result = self._client._request(
            "POST", f"/api/v1/trace/{self.trace_id}/event", event
        )

        self._events.append(event)
        return result

    def log_tokens(self, input: int, output: int, event_type: str = "response"):
        """快速记录 tokens"""
        return self.add_event(
            event_type=event_type,
            input_tokens=input,
            output_tokens=output,
        )

    def log_error(self, error_message: str):
        """记录错误"""
        self.add_event(event_type="error", content=error_message)
        self._status = "failed"

    def complete(self):
        """完成 trace"""
        duration_ms = int((time.time() - self._start_time) * 1000)

        data = {
            "status": "failed" if self._status == "failed" else "completed",
            "duration_ms": duration_ms,
        }

        self._client._request("PUT", f"/api/v1/trace/{self.trace_id}", data)
        self._status = "completed"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.log_error(str(exc_val))
        self.complete()
        return False  # 不抑制异常
