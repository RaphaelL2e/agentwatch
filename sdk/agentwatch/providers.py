"""
AgentWatch SDK Provider 支持
各 AI 提供商的 Token 计算和适配
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TokenUsage:
    """Token 使用量"""

    input_tokens: int
    output_tokens: int
    total_tokens: int

    @classmethod
    def from_openai(cls, response: Any) -> "TokenUsage":
        """从 OpenAI 响应提取"""
        usage = response.usage
        return cls(
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
        )

    @classmethod
    def from_anthropic(cls, response: Any) -> "TokenUsage":
        """从 Anthropic 响应提取"""
        usage = response.usage
        return cls(
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.input_tokens + usage.output_tokens,
        )

    @classmethod
    def from_dict(cls, data: Dict) -> "TokenUsage":
        """从字典提取"""
        return cls(
            input_tokens=data.get("input_tokens", data.get("prompt_tokens", 0)),
            output_tokens=data.get("output_tokens", data.get("completion_tokens", 0)),
            total_tokens=data.get("total_tokens", 0),
        )


# Provider 成本配置 (USD per 1K tokens)
PROVIDER_COSTS: Dict[str, Dict[str, Dict[str, float]]] = {
    "openai": {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "o1": {"input": 0.015, "output": 0.06},
        "o1-mini": {"input": 0.003, "output": 0.012},
    },
    "anthropic": {
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        "claude-3.5-sonnet": {"input": 0.003, "output": 0.015},
        "claude-4.7": {"input": 0.003, "output": 0.015},
    },
    "deepseek": {
        "deepseek-chat": {"input": 0.00007, "output": 0.00014},
        "deepseek-coder": {"input": 0.00007, "output": 0.00014},
        "deepseek-v4": {"input": 0.00014, "output": 0.00028},
    },
    "google": {
        "gemini-pro": {"input": 0.00025, "output": 0.0005},
        "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
        "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    },
}


def calculate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """
    计算 Token 成本

    Args:
        provider: 提供商名称
        model: 模型名称
        input_tokens: 输入 tokens
        output_tokens: 输出 tokens

    Returns:
        成本 (USD)
    """
    provider_lower = provider.lower()
    model_lower = model.lower()

    # 查找成本配置
    provider_costs = PROVIDER_COSTS.get(provider_lower, {})

    # 尝试匹配模型
    model_costs = None
    for model_key, costs in provider_costs.items():
        if model_key in model_lower or model_lower in model_key:
            model_costs = costs
            break

    # 使用默认成本
    if not model_costs:
        model_costs = {"input": 0.001, "output": 0.002}

    # 计算成本
    input_cost = (input_tokens / 1000) * model_costs["input"]
    output_cost = (output_tokens / 1000) * model_costs["output"]

    return input_cost + output_cost


def extract_tokens(response: Any, provider: str) -> TokenUsage:
    """
    从响应中提取 Token 使用量

    Args:
        response: AI 提供商的响应对象
        provider: 提供商名称

    Returns:
        TokenUsage 对象
    """
    provider_lower = provider.lower()

    if provider_lower == "openai":
        return TokenUsage.from_openai(response)
    elif provider_lower == "anthropic":
        return TokenUsage.from_anthropic(response)
    elif isinstance(response, dict):
        return TokenUsage.from_dict(response)
    else:
        # 尝试通用提取
        if hasattr(response, "usage"):
            return TokenUsage.from_openai(response)
        return TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0)


class ProviderAdapter:
    """
    Provider适配器基类

    用于适配不同的 AI 提供商
    """

    provider_name: str = "unknown"

    def extract_tokens(self, response: Any) -> TokenUsage:
        """提取 tokens"""
        raise NotImplementedError

    def calculate_cost(self, model: str, tokens: TokenUsage) -> float:
        """计算成本"""
        return calculate_cost(
            self.provider_name,
            model,
            tokens.input_tokens,
            tokens.output_tokens,
        )


class OpenAIAdapter(ProviderAdapter):
    """OpenAI 适配器"""

    provider_name = "openai"

    def extract_tokens(self, response: Any) -> TokenUsage:
        return TokenUsage.from_openai(response)


class AnthropicAdapter(ProviderAdapter):
    """Anthropic 适配器"""

    provider_name = "anthropic"

    def extract_tokens(self, response: Any) -> TokenUsage:
        return TokenUsage.from_anthropic(response)


class DeepSeekAdapter(ProviderAdapter):
    """DeepSeek 适配器"""

    provider_name = "deepseek"

    def extract_tokens(self, response: Any) -> TokenUsage:
        # DeepSeek 使用 OpenAI 格式
        if hasattr(response, "usage"):
            return TokenUsage.from_openai(response)
        return TokenUsage.from_dict(response)


class GoogleAdapter(ProviderAdapter):
    """Google Gemini 适配器"""

    provider_name = "google"

    def extract_tokens(self, response: Any) -> TokenUsage:
        # Gemini 使用不同格式
        if hasattr(response, "usage_metadata"):
            metadata = response.usage_metadata
            return TokenUsage(
                input_tokens=metadata.prompt_token_count,
                output_tokens=metadata.candidates_token_count,
                total_tokens=metadata.total_token_count,
            )
        return TokenUsage.from_dict(response)


# Provider适配器映射
PROVIDER_ADAPTERS: Dict[str, ProviderAdapter] = {
    "openai": OpenAIAdapter(),
    "anthropic": AnthropicAdapter(),
    "deepseek": DeepSeekAdapter(),
    "google": GoogleAdapter(),
}


def get_adapter(provider: str) -> ProviderAdapter:
    """获取 Provider 适配器"""
    provider_lower = provider.lower()
    return PROVIDER_ADAPTERS.get(provider_lower, ProviderAdapter())
