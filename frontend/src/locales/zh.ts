import { Language } from './en'

export const zh: Language = {
  // 通用
  common: {
    dashboard: '仪表盘',
    costs: '成本',
    optimize: '优化',
    charts: '图表',
    export: '导出',
    settings: '设置',
    logout: '退出',
    login: '登录',
    register: '注册',
    loading: '加载中...',
    backToDashboard: '返回仪表盘',
    github: 'GitHub',
    language: '语言',
    english: '英文',
    chinese: '中文',
  },
  
  // 导航标题
  brand: {
    name: 'AgentWatch',
    version: 'v0.8.0',
    subtitle: 'AI Agent 安全监控平台',
  },
  
  // 登录页面
  login: {
    title: '登录账号',
    email: '邮箱',
    password: '密码',
    emailPlaceholder: 'your@email.com',
    passwordPlaceholder: '••••••••',
    submit: '登录',
    submitting: '登录中...',
    error: '登录失败，请检查邮箱和密码',
    noAccount: '还没有账号？',
    registerLink: '注册',
    features: {
      savings: '107倍成本节省',
      realtime: '实时监控',
      security: '安全认证',
    },
  },
  
  // 注册页面
  register: {
    title: '注册新账号',
    email: '邮箱',
    name: '用户名',
    organization: '组织/公司',
    password: '密码',
    confirmPassword: '确认密码',
    emailPlaceholder: 'your@email.com',
    namePlaceholder: '你的名字',
    orgPlaceholder: '公司名称',
    passwordPlaceholder: '至少8位，包含字母和数字',
    confirmPasswordPlaceholder: '再次输入密码',
    passwordHint: '密码需包含字母和数字，至少8位',
    submit: '注册',
    submitting: '注册中...',
    error: '注册失败，请稍后重试',
    passwordMismatch: '两次输入的密码不一致',
    passwordTooShort: '密码长度至少8位',
    hasAccount: '已有账号？',
    loginLink: '登录',
    benefits: {
      title: '注册后你将获得',
      realtimeDashboard: '实时 AI Agent 监控仪表盘',
      costComparison: 'DeepSeek 107倍成本对比分析',
      apiKey: '自动创建 API Key，集成到你的项目',
      alerts: '预算监控和告警通知',
    },
  },
  
  // Dashboard
  dashboard: {
    totalTraces: '总追踪数',
    completed: '已完成',
    running: '运行中',
    totalCost: '总成本',
    healthy: '健康',
    live: '实时',
    version: '版本',
    uptime: '运行时间',
    recentTraces: '最近追踪',
    total: '总计',
    quickActions: '快捷操作',
    createTestTrace: '创建测试追踪',
    costComparison: '成本对比',
    refreshDashboard: '刷新仪表盘',
    traceDetails: '点击查看详情',
    noTraces: '暂无追踪记录',
  },
  
  // 成本对比
  costs: {
    title: '成本对比',
    subtitle: '对比不同 LLM 提供商的成本（1000 输入 + 500 输出 tokens）',
    deepseekTip: 'DeepSeek 成本仅为 GPT-4o 的 1/107！',
    deepseekTipDesc: '同等质量，1% 的成本。AgentWatch 帮你发现这些节省机会。',
    model: '模型',
    inputPerK: '输入成本 (每1K)',
    outputPerK: '输出成本 (每1K)',
    exampleCost: '示例成本',
    vsGPT4o: '对比 GPT-4o',
    cheapest: '最便宜',
    cheaper: '倍更便宜',
    more: '倍更贵',
    recommendations: '使用建议',
    bestValue: '最佳性价比: DeepSeek',
    bestValueDesc: '对于大多数任务，DeepSeek 以极低的成本提供卓越的质量。适合高频率 Agent 工作流。',
    fastCheap: '快速且便宜: Gemini Flash',
    fastCheapDesc: 'Gemini 1.5 Flash 提供出色的速度和低成本。适合实时应用。',
    complexTasks: '复杂任务: GPT-4o / Claude 3.5 Sonnet',
    complexTasksDesc: '对于复杂推理、代码生成或精细任务，高级模型值得投入。使用 AgentWatch 追踪何时值得额外成本。',
    yourActualCosts: '你的实际成本',
    yourActualCostsDesc: '基于 AgentWatch 追踪的数据',
  },
  
  // Footer
  footer: {
    copyright: 'AgentWatch © 2026',
    slogan: '追踪、调试和优化你的 AI Agents',
  },
}