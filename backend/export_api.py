"""
AgentWatch 数据导出 API
Phase 2 功能扩展
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import datetime, timedelta
import csv
import json
import io

from models import AgentProvider, TraceStatus
from auth import get_current_user, UserResponse
from trace_service import TraceService

router = APIRouter(prefix="/api/v1/export", tags=["export"])


@router.get("/csv")
async def export_traces_csv(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    provider: Optional[str] = Query(None, description="Provider过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    agent_id: Optional[str] = Query(None, description="Agent ID过滤"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    导出 Traces 为 CSV 格式
    
    CSV 列:
    - trace_id, agent_name, provider, model, status
    - total_input_tokens, total_output_tokens, total_cost
    - duration_ms, created_at, completed_at, error_message
    """
    # 获取 traces
    traces = TraceService.list_traces(
        page=1,
        page_size=10000,  # 最大导出数量
        agent_id=agent_id,
        provider=provider,
        status=status,
        start_time=start_time,
        end_time=end_time
    )
    
    # 创建 CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入标题行
    writer.writerow([
        "trace_id", "agent_name", "provider", "model", "status",
        "input_tokens", "output_tokens", "total_tokens", "cost_usd",
        "duration_ms", "created_at", "completed_at", "error_message"
    ])
    
    # 写入数据行
    for trace in traces.traces:
        writer.writerow([
            trace.trace_id,
            trace.agent_name,
            trace.provider,
            trace.model,
            trace.status,
            trace.total_input_tokens,
            trace.total_output_tokens,
            trace.total_tokens,
            f"{trace.total_cost:.6f}",
            trace.duration_ms,
            trace.created_at.isoformat() if trace.created_at else "",
            trace.completed_at.isoformat() if trace.completed_at else "",
            trace.error_message or ""
        ])
    
    output.seek(0)
    
    # 生成文件名
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"agentwatch_traces_{timestamp}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/json")
async def export_traces_json(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    provider: Optional[str] = Query(None, description="Provider过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    agent_id: Optional[str] = Query(None, description="Agent ID过滤"),
    include_events: bool = Query(False, description="是否包含事件详情"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    导出 Traces 为 JSON 格式
    
    包含完整的 trace 数据和可选的事件详情
    """
    # 获取 traces
    traces = TraceService.list_traces(
        page=1,
        page_size=10000,
        agent_id=agent_id,
        provider=provider,
        status=status,
        start_time=start_time,
        end_time=end_time
    )
    
    # 构建导出数据
    export_data = {
        "export_info": {
            "timestamp": datetime.utcnow().isoformat(),
            "total_traces": traces.total,
            "filters": {
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "provider": provider,
                "status": status,
                "agent_id": agent_id
            }
        },
        "traces": []
    }
    
    for trace in traces.traces:
        trace_dict = {
            "trace_id": trace.trace_id,
            "agent_id": trace.agent_id,
            "agent_name": trace.agent_name,
            "provider": trace.provider,
            "model": trace.model,
            "status": trace.status,
            "session_id": trace.session_id,
            "user_id": trace.user_id,
            "prompt": trace.prompt,
            "total_input_tokens": trace.total_input_tokens,
            "total_output_tokens": trace.total_output_tokens,
            "total_tokens": trace.total_tokens,
            "total_cost": trace.total_cost,
            "duration_ms": trace.duration_ms,
            "created_at": trace.created_at.isoformat(),
            "updated_at": trace.updated_at.isoformat(),
            "completed_at": trace.completed_at.isoformat() if trace.completed_at else None,
            "error_message": trace.error_message,
            "metadata": trace.metadata
        }
        
        if include_events:
            trace_dict["events"] = [
                {
                    "event_id": e.event_id,
                    "timestamp": e.timestamp.isoformat(),
                    "event_type": e.event_type,
                    "agent_name": e.agent_name,
                    "model": e.model,
                    "input_tokens": e.input_tokens,
                    "output_tokens": e.output_tokens,
                    "latency_ms": e.latency_ms,
                    "content": e.content,
                    "metadata": e.metadata
                }
                for e in trace.events
            ]
        
        export_data["traces"].append(trace_dict)
    
    # 生成文件名
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"agentwatch_traces_{timestamp}.json"
    
    return StreamingResponse(
        iter([json.dumps(export_data, indent=2, ensure_ascii=False)]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/cost-summary")
async def export_cost_summary(
    period: str = Query("7d", description="统计周期: 1d, 7d, 30d, all"),
    provider: Optional[str] = Query(None, description="Provider过滤"),
    format: str = Query("json", description="导出格式: json, csv"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    导出成本汇总报告
    
    包含:
    - 各 Provider 成本对比
    - 各模型成本详情
    - 成本趋势分析
    """
    storage = get_storage()
    
    # 计算时间范围
    period_days = {"1d": 1, "7d": 7, "30d": 30, "all": None}.get(period, 7)
    
    if period_days:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=period_days)
    else:
        start_time = None
# 获取成本汇总
    cost_summary = TraceService.get_cost_summary(
        provider=provider,
        start_time=start_time,
        end_time=end_time
    )
    
    # 获取统计
    stats = TraceService.get_stats()
    
    # 构建报告
    report = {
        "period": period,
        "start_time": start_time.isoformat() if start_time else "all_time",
        "end_time": end_time.isoformat() if end_time else "now",
        "total_cost": stats.get("total_cost", 0),
        "total_traces": stats.get("total_traces", 0),
        "provider_breakdown": []
    }
    
    for summary in cost_summary:
        report["provider_breakdown"].append({
            "provider": summary.provider,
            "model": summary.model,
            "total_traces": summary.total_traces,
            "total_tokens": summary.total_tokens,
            "total_cost": summary.total_cost,
            "avg_latency_ms": summary.avg_latency_ms
        })
    
    # 添加 DeepSeek 成本对比分析
    deepseek_cost = 0
    openai_cost = 0
    for item in report["provider_breakdown"]:
        if item["provider"] == "deepseek":
            deepseek_cost += item["total_cost"]
        elif item["provider"] == "openai":
            openai_cost += item["total_cost"]
    
    if openai_cost > 0 and deepseek_cost > 0:
        report["cost_optimization"] = {
            "deepseek_vs_openai_ratio": openai_cost / deepseek_cost if deepseek_cost > 0 else 0,
            "potential_savings": f"${(openai_cost - deepseek_cost):.2f}",
            "recommendation": "使用 DeepSeek 可节省显著成本"
        }
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["Provider", "Model", "Traces", "Tokens", "Cost (USD)", "Avg Latency (ms)"])
        
        for item in report["provider_breakdown"]:
            writer.writerow([
                item["provider"],
                item["model"],
                item["total_traces"],
                item["total_tokens"],
                f"{item['total_cost']:.6f}",
                f"{item['avg_latency_ms']:.0f}"
            ])
        
        output.seek(0)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"agentwatch_cost_summary_{timestamp}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    # JSON 格式
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"agentwatch_cost_summary_{timestamp}.json"
    
    return StreamingResponse(
        iter([json.dumps(report, indent=2, ensure_ascii=False)]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/report")
async def export_full_report(
    team_id: Optional[str] = Query(None, description="团队ID"),
    project_id: Optional[str] = Query(None, description="项目ID"),
    period: str = Query("7d", description="统计周期"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    导出完整分析报告
    
    包含:
    - 执行摘要
    - 成本分析
    - 性能分析
    - Provider对比
    - 优化建议
    """
    storage = get_storage()
    
    # 计算时间范围
    period_days = {"1d": 1, "7d": 7, "30d": 30, "all": None}.get(period, 7)
    
    if period_days:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=period_days)
    else:
        start_time = None
# 获取数据
    stats = TraceService.get_stats()
    cost_summary = TraceService.get_cost_summary(start_time=start_time, end_time=end_time)
    traces = TraceService.list_traces(page=1, page_size=100, start_time=start_time, end_time=end_time)
    
    # 构建报告
    report = {
        "report_info": {
            "title": "AgentWatch Analysis Report",
            "generated_at": datetime.utcnow().isoformat(),
            "period": period,
            "team_id": team_id,
            "project_id": project_id
        },
        "executive_summary": {
            "total_traces": stats.get("total_traces", 0),
            "total_cost": stats.get("total_cost", 0),
            "success_rate": f"{(stats.get('completed_traces', 0) / max(stats.get('total_traces', 1), 1) * 100):.1f}%",
            "total_tokens": traces.traces[0].total_tokens if traces.traces else 0
        },
        "cost_analysis": {
            "by_provider": {},
            "by_model": {},
            "daily_trend": [],  # TODO: 实现每日趋势
            "optimization_potential": 0
        },
        "performance_analysis": {
            "avg_latency_ms": 0,
            "max_latency_ms": 0,
            "min_latency_ms": 0,
            "by_provider": {}
        },
        "provider_comparison": [],
        "optimization_recommendations": []
    }
    
    # 分析成本和性能
    latencies = []
    for trace in traces.traces:
        latencies.append(trace.duration_ms)
        
        provider = trace.provider
        model = trace.model
        
        # Provider 成本汇总
        if provider not in report["cost_analysis"]["by_provider"]:
            report["cost_analysis"]["by_provider"][provider] = {"cost": 0, "traces": 0}
        report["cost_analysis"]["by_provider"][provider]["cost"] += trace.total_cost
        report["cost_analysis"]["by_provider"][provider]["traces"] += 1
        
        # Model 成本汇总
        model_key = f"{provider}/{model}"
        if model_key not in report["cost_analysis"]["by_model"]:
            report["cost_analysis"]["by_model"][model_key] = {"cost": 0, "traces": 0}
        report["cost_analysis"]["by_model"][model_key]["cost"] += trace.total_cost
        report["cost_analysis"]["by_model"][model_key]["traces"] += 1
        
        # Provider 性能汇总
        if provider not in report["performance_analysis"]["by_provider"]:
            report["performance_analysis"]["by_provider"][provider] = {"latencies": [], "avg": 0}
        report["performance_analysis"]["by_provider"][provider]["latencies"].append(trace.duration_ms)
    
    # 计算平均延迟
    if latencies:
        report["performance_analysis"]["avg_latency_ms"] = sum(latencies) / len(latencies)
        report["performance_analysis"]["max_latency_ms"] = max(latencies)
        report["performance_analysis"]["min_latency_ms"] = min(latencies)
    
    for provider, data in report["performance_analysis"]["by_provider"].items():
        if data["latencies"]:
            data["avg"] = sum(data["latencies"]) / len(data["latencies"])
        del data["latencies"]  # 移除原始数据
    
    # Provider 对比
    for summary in cost_summary:
        report["provider_comparison"].append({
            "provider": summary.provider,
            "model": summary.model,
            "traces": summary.total_traces,
            "tokens": summary.total_tokens,
            "cost": summary.total_cost,
            "avg_latency_ms": summary.avg_latency_ms,
            "cost_per_1k_tokens": summary.total_cost / (summary.total_tokens / 1000) if summary.total_tokens > 0 else 0
        })
    
    # 优化建议
    deepseek_data = report["cost_analysis"]["by_provider"].get("deepseek", {"cost": 0, "traces": 0})
    openai_data = report["cost_analysis"]["by_provider"].get("openai", {"cost": 0, "traces": 0})
    
    if openai_data["cost"] > deepseek_data["cost"] * 10 and deepseek_data["traces"] < openai_data["traces"] * 0.1:
        report["optimization_recommendations"].append({
            "type": "cost",
            "priority": "high",
            "suggestion": "考虑将更多任务迁移到 DeepSeek",
            "potential_savings": f"${openai_data['cost'] * 0.9:.2f}/月",
            "details": "DeepSeek 成本约为 OpenAI 的 1/107，可显著降低运营成本"
        })
    
    if report["performance_analysis"]["avg_latency_ms"] > 5000:
        report["optimization_recommendations"].append({
            "type": "performance",
            "priority": "medium",
            "suggestion": "优化高延迟 Agent",
            "details": f"平均延迟 {report['performance_analysis']['avg_latency_ms']}ms，建议检查模型选择和提示词优化"
        })
    
    failed_rate = stats.get("failed_traces", 0) / max(stats.get("total_traces", 1), 1)
    if failed_rate > 0.1:
        report["optimization_recommendations"].append({
            "type": "reliability",
            "priority": "high",
            "suggestion": "降低失败率",
            "details": f"当前失败率 {failed_rate*100:.1f}%，建议添加重试机制和错误处理"
        })
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"agentwatch_report_{timestamp}.json"
    
    return StreamingResponse(
        iter([json.dumps(report, indent=2, ensure_ascii=False)]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )