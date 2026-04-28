"""
AgentWatch SDK - DeepSeek API 真实集成示例
展示如何监控 DeepSeek API 调用和成本优化

环境要求:
  pip install openai  # DeepSeek 使用 OpenAI兼容接口
  export DEEPSEEK_API_KEY=your_api_key
"""

import os
import time
from agentwatch import AgentWatch, trace_agent

# DeepSeek 使用 OpenAI SDK（兼容接口）
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("⚠️  openai not installed. Run: pip install openai")


# DeepSeek API 配置
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"


# ============================================
# 示例 1: DeepSeek 基础调用监控
# ============================================

def example_deepseek_basic():
    """监控 DeepSeek API 基础调用"""
    if not HAS_OPENAI:
        print("Skipping: openai SDK not installed")
        return
    
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("⚠️  DEEPSEEK_API_KEY not set. Skipping real API call.")
        print("   Demo mode: simulating DeepSeek call...")
        _simulate_deepseek_call()
        return
    
    aw = AgentWatch(api_url="http://localhost:8000")
    client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
    
    print("\n=== DeepSeek API 真实调用监控 ===")
    
    with aw.trace("deepseek_agent", model="deepseek-chat", provider="deepseek") as trace:
        start_time = time.time()
        
        # 真实 API 调用
        response = client.chat.completions.create(
            model="deepseek-chat",
            max_tokens=100,
            messages=[{"role": "user", "content": "What is AI in one sentence?"}]
        )
        
        elapsed = time.time() - start_time
        
        # 记录实际 Token 使用
        usage = response.usage
        trace.log_tokens(input=usage.prompt_tokens, output=usage.completion_tokens)
        
        # 添加事件
        trace.add_event("api_call",
            latency_ms=elapsed * 1000,
            model=response.model,
            finish_reason=response.choices[0].finish_reason
        )
        
        print(f"✅ Response: {response.choices[0].message.content}")
        print(f"📊 Tokens: {usage.prompt_tokens} in + {usage.completion_tokens} out")
        print(f"⏱️  Latency: {elapsed:.2f}s")
        print(f"💰 Cost: ${trace.calculate_cost():.6f}")
    
    aw.close()


def _simulate_deepseek_call():
    """模拟 DeepSeek 调用（无 API Key 时）"""
    aw = AgentWatch()
    
    with aw.trace("deepseek_demo", model="deepseek-chat", provider="deepseek") as trace:
        # DeepSeek 典型用量
        trace.log_tokens(input=15, output=30)
        trace.add_event("api_call", latency_ms=350, model="deepseek-chat")
    
    print(f"📊 Simulated: 15 input + 30 output tokens")
    print(f"💰 Cost: ${trace.calculate_cost():.6f}")
    aw.close()


# ============================================
# 示例 2: DeepSeek V3 vs GPT-4o 成本对比
# ============================================

def example_deepseek_vs_gpt4o():
    """DeepSeek V3 vs GPT-4o 成本对比 - AgentWatch 核心卖点"""
    aw = AgentWatch()
    
    print("\n=== DeepSeek vs GPT-4o 成本对比 ===")
    print("🔥 AgentWatch 核心发现: DeepSeek 成本仅 GPT-4o 的 1/107！")
    
    # 相同任务量
    tokens_input = 10000
    tokens_output = 5000
    
    # GPT-4o
    with aw.trace("gpt4o", model="gpt-4o", provider="openai") as t1:
        t1.log_tokens(input=tokens_input, output=tokens_output)
        gpt4o_cost = t1.calculate_cost()
    
    # DeepSeek V3
    with aw.trace("deepseek_v3", model="deepseek-chat", provider="deepseek") as t2:
        t2.log_tokens(input=tokens_input, output=tokens_output)
        deepseek_cost = t2.calculate_cost()
    
    print(f"\n📊 Token 使用: {tokens_input} input + {tokens_output} output")
    print(f"GPT-4o cost:   ${gpt4o_cost:.2f}")
    print(f"DeepSeek cost: ${deepseek_cost:.4f}")
    
    savings_ratio = gpt4o_cost / deepseek_cost
    print(f"\n🚀 省钱倍数: {savings_ratio:.1f}x 更便宜！")
    
    savings_percent = (gpt4o_cost - deepseek_cost) / gpt4o_cost * 100
    print(f"💰 省钱比例: {savings_percent:.1f}%")
    
    # 月度成本对比（假设每月 1M tokens）
    monthly_tokens = 1_000_000
    gpt4o_monthly = gpt4o_cost * (monthly_tokens / (tokens_input + tokens_output))
    deepseek_monthly = deepseek_cost * (monthly_tokens / (tokens_input + tokens_output))
    
    print(f"\n📈 月度预估（1M tokens）:")
    print(f"GPT-4o:   ${gpt4o_monthly:.2f}/月")
    print(f"DeepSeek: ${deepseek_monthly:.2f}/月")
    print(f"每月节省: ${gpt4o_monthly - deepseek_monthly:.2f}")
    
    aw.close()


# ============================================
# 示例 3: DeepSeek 多轮对话监控
# ============================================

def example_deepseek_conversation():
    """监控 DeepSeek 多轮对话"""
    if not HAS_OPENAI or not os.environ.get("DEEPSEEK_API_KEY"):
        print("⚠️  API key not available, skipping multi-turn example")
        return
    
    aw = AgentWatch()
    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url=DEEPSEEK_BASE_URL
    )
    
    print("\n=== DeepSeek 多轮对话监控 ===")
    
    messages = [{"role": "user", "content": "What are the top 3 AI models?"}]
    total_cost = 0
    
    for turn in range(2):
        with aw.trace(f"deepseek_turn_{turn}", model="deepseek-chat", provider="deepseek") as trace:
            response = client.chat.completions.create(
                model="deepseek-chat",
                max_tokens=100,
                messages=messages
            )
            
            usage = response.usage
            trace.log_tokens(input=usage.prompt_tokens, output=usage.completion_tokens)
            
            # 添加到对话历史
            messages.append({"role": "assistant", "content": response.choices[0].message.content})
            if turn < 1:
                messages.append({"role": "user", "content": "Which one is cheapest?"})
            
            cost = trace.calculate_cost()
            total_cost += cost
            
            print(f"Turn {turn}: {response.choices[0].message.content[:50]}...")
            print(f"  Cost: ${cost:.6f}")
    
    print(f"\n💰 Total conversation cost: ${total_cost:.6f}")
    aw.close()


# ============================================
# 示例 4: DeepSeek Reasoner (R1) 监控
# ============================================

def example_deepseek_reasoner():
    """监控 DeepSeek R1 (Reasoner) - 推理增强模型"""
    if not HAS_OPENAI or not os.environ.get("DEEPSEEK_API_KEY"):
        print("⚠️  API key not available")
        _simulate_reasoner()
        return
    
    aw = AgentWatch()
    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url=DEEPSEEK_BASE_URL
    )
    
    print("\n=== DeepSeek R1 (Reasoner) 监控 ===")
    
    with aw.trace("deepseek_r1", model="deepseek-reasoner", provider="deepseek") as trace:
        start_time = time.time()
        
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[{"role": "user", "content": "Solve: What is 15 * 17 + 23?"}]
        )
        
        elapsed = time.time() - start_time
        usage = response.usage
        
        trace.log_tokens(input=usage.prompt_tokens, output=usage.completion_tokens)
        trace.add_event("reasoning_complete", latency_ms=elapsed * 1000)
        
        # DeepSeek R1 有特殊的 reasoning tokens
        print(f"✅ Answer: {response.choices[0].message.content}")
        print(f"📊 Tokens: {usage.prompt_tokens} + {usage.completion_tokens}")
        print(f"⏱️  Time: {elapsed:.2f}s")
        print(f"💰 Cost: ${trace.calculate_cost():.6f}")
    
    aw.close()


def _simulate_reasoner():
    """模拟 Reasoner 调用"""
    aw = AgentWatch()
    with aw.trace("deepseek_r1_demo", model="deepseek-reasoner", provider="deepseek") as trace:
        # Reasoner 通常有更多 reasoning tokens
        trace.log_tokens(input=50, output=200)
    print("📊 Simulated: 50 input + 200 output (including reasoning)")
    aw.close()


# ============================================
# 示例 5: 批量 Agent 调用 + 成本统计
# ============================================

@trace_agent("batch_agent", model="deepseek-chat", provider="deepseek")
def process_task(task: str):
    """批量处理任务"""
    if not HAS_OPENAI or not os.environ.get("DEEPSEEK_API_KEY"):
        return {"result": f"Demo: {task}", "usage": {"prompt_tokens": 20, "completion_tokens": 30}}
    
    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url=DEEPSEEK_BASE_URL
    )
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=50,
        messages=[{"role": "user", "content": task}]
    )
    
    return {
        "result": response.choices[0].message.content,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens
        }
    }


def example_batch_processing():
    """批量任务处理 + 成本统计"""
    print("\n=== 批量 Agent 调用 ===")
    
    tasks = [
        "Summarize: AI is transforming industries",
        "Translate 'hello' to Chinese",
        "What is 2 + 2?",
        "List 3 programming languages",
        "Define 'machine learning'",
    ]
    
    aw = AgentWatch()
    
    for i, task in enumerate(tasks):
        result = process_task(task)
        print(f"Task {i+1}: {result['result'][:40]}...")
    
    # 获取统计
    stats = aw.get_stats()
    print(f"\n📊 总计: {stats['total_traces']} traces")
    print(f"💰 总成本: ${stats['total_cost']:.6f}")
    
    aw.close()


# ============================================
# 示例 6: 企业级成本监控 Dashboard
# ============================================

def example_enterprise_dashboard():
    """企业级成本监控 Dashboard"""
    aw = AgentWatch()
    
    print("\n=== 企业级成本监控 Dashboard ===")
    
    # 模拟企业一天的 API 使用
    scenarios = [
        ("客服机器人", "gpt-4o-mini", "openai", 5000, 10000),
        ("代码助手", "claude-3-haiku", "anthropic", 3000, 2000),
        ("数据分析", "deepseek-chat", "deepseek", 10000, 5000),
        ("文档生成", "gemini-1.5-flash", "google", 8000, 6000),
    ]
    
    total_cost = 0
    by_provider = {}
    
    for name, model, provider, input_t, output_t in scenarios:
        with aw.trace(name, model=model, provider=provider) as trace:
            trace.log_tokens(input=input_t, output=output_t)
            cost = trace.calculate_cost()
            total_cost += cost
            
            if provider not in by_provider:
                by_provider[provider] = 0
            by_provider[provider] += cost
            
            print(f"{name}: {input_t}+{output_t} tokens = ${cost:.4f}")
    
    print(f"\n📊 企业日报:")
    print(f"总成本: ${total_cost:.2f}")
    print(f"\n按 Provider:")
    for p, c in sorted(by_provider.items(), key=lambda x: -x[1]):
        print(f"  {p}: ${c:.4f} ({c/total_cost*100:.1f}%)")
    
    # 计算切换到 DeepSeek 的潜在节省
    print(f"\n💡 优化建议:")
    print(f"如果全部切换到 DeepSeek:")
    
    deepseek_cost = 0
    for _, model, provider, input_t, output_t in scenarios:
        with aw.trace(f"{provider}_to_deepseek", model="deepseek-chat", provider="deepseek") as trace:
            trace.log_tokens(input=input_t, output=output_t)
            deepseek_cost += trace.calculate_cost()
    
    savings = total_cost - deepseek_cost
    print(f"  原成本: ${total_cost:.2f}")
    print(f"  DeepSeek: ${deepseek_cost:.2f}")
    print(f"  每天节省: ${savings:.2f}")
    print(f"  每月节省: ${savings * 30:.2f}")
    print(f"  每年节省: ${savings * 365:.2f}")
    
    aw.close()


# ============================================
# 主函数
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("AgentWatch SDK - DeepSeek Integration Examples")
    print("=" * 60)
    
    print("\n[Example 1] DeepSeek Basic Call")
    example_deepseek_basic()
    
    print("\n[Example 2] DeepSeek vs GPT-4o Cost Comparison")
    example_deepseek_vs_gpt4o()
    
    print("\n[Example 3] DeepSeek Multi-turn Conversation")
    example_deepseek_conversation()
    
    print("\n[Example 4] DeepSeek Reasoner (R1)")
    example_deepseek_reasoner()
    
    print("\n[Example 5] Batch Processing")
    example_batch_processing()
    
    print("\n[Example 6] Enterprise Cost Dashboard")
    example_enterprise_dashboard()
    
    print("\n" + "=" * 60)
    print("All DeepSeek examples completed!")
    print("=" * 60)