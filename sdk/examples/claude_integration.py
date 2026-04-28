"""
AgentWatch SDK - Claude API 真实集成示例
展示如何监控 Anthropic Claude API 调用

环境要求:
  pip install anthropic
  export ANTHROPIC_API_KEY=your_api_key
"""

import os
import time
from agentwatch import AgentWatch, trace_agent

# 尝试导入 Anthropic SDK
try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("⚠️  anthropic not installed. Run: pip install anthropic")


# ============================================
# 示例 1: Claude 基础调用监控
# ============================================

def example_claude_basic():
    """监控 Claude API 基础调用"""
    if not HAS_ANTHROPIC:
        print("Skipping: anthropic SDK not installed")
        return
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set. Skipping real API call.")
        print("   Demo mode: simulating Claude call...")
        _simulate_claude_call()
        return
    
    aw = AgentWatch(api_url="http://localhost:8000")
    client = Anthropic(api_key=api_key)
    
    print("\n=== Claude API 真实调用监控 ===")
    
    with aw.trace("claude_agent", model="claude-3-haiku-20240307", provider="anthropic") as trace:
        start_time = time.time()
        
        # 真实 API 调用
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            messages=[{"role": "user", "content": "What is AI in one sentence?"}]
        )
        
        elapsed = time.time() - start_time
        
        # 记录实际 Token 使用
        trace.log_tokens(
            input=response.usage.input_tokens,
            output=response.usage.output_tokens
        )
        
        # 添加事件
        trace.add_event("api_call", 
            latency_ms=elapsed * 1000,
            model=response.model,
            stop_reason=response.stop_reason
        )
        
        print(f"✅ Response: {response.content[0].text}")
        print(f"📊 Tokens: {response.usage.input_tokens} in + {response.usage.output_tokens} out")
        print(f"⏱️  Latency: {elapsed:.2f}s")
        print(f"💰 Cost: ${trace.calculate_cost():.6f}")
    
    aw.close()


def _simulate_claude_call():
    """模拟 Claude 调用（无 API Key 时）"""
    aw = AgentWatch()
    
    with aw.trace("claude_demo", model="claude-3-haiku-20240307", provider="anthropic") as trace:
        # Claude Haiku 典型用量
        trace.log_tokens(input=15, output=30)
        trace.add_event("api_call", latency_ms=450, model="claude-3-haiku")
    
    print(f"📊 Simulated: 15 input + 30 output tokens")
    print(f"💰 Cost: ${trace.calculate_cost():.6f}")
    aw.close()


# ============================================
# 示例 2: Claude 多轮对话监控
# ============================================

def example_claude_conversation():
    """监控 Claude 多轮对话"""
    if not HAS_ANTHROPIC or not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️  API key not available, skipping multi-turn example")
        return
    
    aw = AgentWatch()
    client = Anthropic()
    
    print("\n=== Claude 多轮对话监控 ===")
    
    conversation = [
        {"role": "user", "content": "Name 3 AI companies"},
    ]
    
    total_cost = 0
    
    for turn in range(2):
        with aw.trace(f"claude_turn_{turn}", model="claude-3-haiku-20240307") as trace:
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=50,
                messages=conversation
            )
            
            trace.log_tokens(
                input=response.usage.input_tokens,
                output=response.usage.output_tokens
            )
            
            # 添加到对话历史
            conversation.append({"role": "assistant", "content": response.content[0].text})
            if turn < 1:
                conversation.append({"role": "user", "content": "Which one is most valuable?"})
            
            cost = trace.calculate_cost()
            total_cost += cost
            
            print(f"Turn {turn}: {response.content[0].text[:50]}...")
            print(f"  Cost: ${cost:.6f}")
    
    print(f"\n💰 Total conversation cost: ${total_cost:.6f}")
    aw.close()


# ============================================
# 示例 3: Claude vs DeepSeek 成本对比
# ============================================

def example_claude_vs_deepseek():
    """Claude vs DeepSeek 成本对比"""
    aw = AgentWatch()
    
    print("\n=== Claude vs DeepSeek 成本对比 ===")
    print("(相同 Token 数量，对比成本差异)")
    
    tokens_input = 1000
    tokens_output = 500
    
    # Claude Haiku
    with aw.trace("claude_haiku", model="claude-3-haiku-20240307", provider="anthropic") as t1:
        t1.log_tokens(input=tokens_input, output=tokens_output)
        claude_cost = t1.calculate_cost()
    
    # DeepSeek V3
    with aw.trace("deepseek_v3", model="deepseek-chat", provider="deepseek") as t2:
        t2.log_tokens(input=tokens_input, output=tokens_output)
        deepseek_cost = t2.calculate_cost()
    
    print(f"Claude Haiku: ${claude_cost:.4f}")
    print(f"DeepSeek V3:  ${deepseek_cost:.4f}")
    print(f"省钱倍数: {claude_cost / deepseek_cost:.1f}x")
    
    savings_percent = (claude_cost - deepseek_cost) / claude_cost * 100
    print(f"省钱比例: {savings_percent:.1f}%")
    
    aw.close()


# ============================================
# 示例 4: Claude Code Agent 监控
# ============================================

@trace_agent("claude_code_agent", model="claude-3-5-sonnet-20241022", provider="anthropic")
def analyze_code(code: str, question: str):
    """监控代码分析 Agent"""
    if not HAS_ANTHROPIC or not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️  API key not available")
        return {"analysis": "Demo mode - no real call", "usage": {"prompt_tokens": 100, "completion_tokens": 50}}
    
    client = Anthropic()
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=200,
        system="You are a code analyzer. Analyze the given code and answer the question.",
        messages=[{"role": "user", "content": f"Code:\n{code}\n\nQuestion: {question}"}]
    )
    
    return {
        "analysis": response.content[0].text,
        "usage": {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens
        }
    }


def example_code_agent():
    """代码分析 Agent 示例"""
    code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''
    
    result = analyze_code(code, "What is the time complexity of this function?")
    print(f"\n=== Code Agent Result ===")
    print(f"Analysis: {result['analysis'][:100]}...")
    print(f"Tokens: {result['usage']['prompt_tokens']} + {result['usage']['completion_tokens']}")


# ============================================
# 示例 5: Claude 流式响应监控
# ============================================

def example_claude_streaming():
    """监控 Claude 流式响应"""
    if not HAS_ANTHROPIC or not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️  API key not available, skipping streaming example")
        return
    
    aw = AgentWatch()
    client = Anthropic()
    
    print("\n=== Claude 流式响应监控 ===")
    
    with aw.trace("claude_stream", model="claude-3-haiku-20240307") as trace:
        start_time = time.time()
        
        input_tokens = 0
        output_tokens = 0
        
        with client.messages.stream(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            messages=[{"role": "user", "content": "Write a haiku about coding"}]
        ) as stream:
            for text in stream.text_stream:
                print(f"  {text}", end="", flush=True)
                output_tokens += 1  # 粗略估算
            
            # 获取最终统计
            final = stream.get_final_message()
            input_tokens = final.usage.input_tokens
            output_tokens = final.usage.output_tokens
        
        elapsed = time.time() - start_time
        trace.log_tokens(input=input_tokens, output=output_tokens)
        trace.add_event("stream_complete", latency_ms=elapsed * 1000)
        
        print(f"\n\n✅ Streaming completed")
        print(f"📊 Tokens: {input_tokens} + {output_tokens}")
        print(f"⏱️  Time: {elapsed:.2f}s")
    
    aw.close()


# ============================================
# 主函数
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("AgentWatch SDK - Claude Integration Examples")
    print("=" * 60)
    
    print("\n[Example 1] Claude Basic Call")
    example_claude_basic()
    
    print("\n[Example 2] Claude Multi-turn Conversation")
    example_claude_conversation()
    
    print("\n[Example 3] Claude vs DeepSeek Cost Comparison")
    example_claude_vs_deepseek()
    
    print("\n[Example 4] Claude Code Agent")
    example_code_agent()
    
    print("\n[Example 5] Claude Streaming")
    example_claude_streaming()
    
    print("\n" + "=" * 60)
    print("All Claude examples completed!")
    print("=" * 60)