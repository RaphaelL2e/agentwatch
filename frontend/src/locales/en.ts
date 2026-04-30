export const en = {
  // 通用
  common: {
    dashboard: 'Dashboard',
    costs: 'Costs',
    optimize: 'Optimize',
    charts: 'Charts',
    export: 'Export',
    settings: 'Settings',
    logout: 'Logout',
    login: 'Login',
    register: 'Register',
    loading: 'Loading...',
    backToDashboard: 'Back to Dashboard',
    github: 'GitHub',
    language: 'Language',
    english: 'English',
    chinese: 'Chinese',
  },
  
  // 导航标题
  brand: {
    name: 'AgentWatch',
    version: 'v0.8.0',
    subtitle: 'AI Agent Security Monitoring Platform',
  },
  
  // 登录页面
  login: {
    title: 'Login',
    email: 'Email',
    password: 'Password',
    emailPlaceholder: 'your@email.com',
    passwordPlaceholder: '••••••••',
    submit: 'Login',
    submitting: 'Logging in...',
    error: 'Login failed, please check email and password',
    noAccount: 'Don\'t have an account?',
    registerLink: 'Register',
    features: {
      savings: '107x Cost Savings',
      realtime: 'Real-time Monitoring',
      security: 'Secure Authentication',
    },
  },
  
  // 注册页面
  register: {
    title: 'Register',
    email: 'Email',
    name: 'Username',
    organization: 'Organization/Company',
    password: 'Password',
    confirmPassword: 'Confirm Password',
    emailPlaceholder: 'your@email.com',
    namePlaceholder: 'Your name',
    orgPlaceholder: 'Company name',
    passwordPlaceholder: 'At least 8 characters, include letters and numbers',
    confirmPasswordPlaceholder: 'Enter password again',
    passwordHint: 'Password must include letters and numbers, at least 8 characters',
    submit: 'Register',
    submitting: 'Registering...',
    error: 'Registration failed, please try again',
    passwordMismatch: 'Passwords do not match',
    passwordTooShort: 'Password must be at least 8 characters',
    hasAccount: 'Already have an account?',
    loginLink: 'Login',
    benefits: {
      title: 'After registration you will get',
      realtimeDashboard: 'Real-time AI Agent Monitoring Dashboard',
      costComparison: 'DeepSeek 107x Cost Comparison Analysis',
      apiKey: 'Auto-create API Key for your projects',
      alerts: 'Budget monitoring and alert notifications',
    },
  },
  
  // Dashboard
  dashboard: {
    totalTraces: 'Total Traces',
    completed: 'Completed',
    running: 'Running',
    totalCost: 'Total Cost',
    healthy: 'healthy',
    live: 'Live',
    version: 'Version',
    uptime: 'Uptime',
    recentTraces: 'Recent Traces',
    total: 'total',
    quickActions: 'Quick Actions',
    createTestTrace: 'Create Test Trace',
    costComparison: 'Cost Comparison',
    refreshDashboard: 'Refresh Dashboard',
    traceDetails: 'Click to view details',
    noTraces: 'No traces yet',
  },
  
  // 成本对比
  costs: {
    title: 'Cost Comparison',
    subtitle: 'Compare costs across different LLM providers for 1000 input + 500 output tokens',
    deepseekTip: 'DeepSeek is 107x cheaper than GPT-4o!',
    deepseekTipDesc: 'Same quality at 1% of the cost. AgentWatch helps you discover these savings.',
    model: 'Model',
    inputPerK: 'Input (per 1K)',
    outputPerK: 'Output (per 1K)',
    exampleCost: 'Example Cost',
    vsGPT4o: 'vs GPT-4o',
    cheapest: 'Cheapest',
    cheaper: 'x cheaper',
    more: 'x more',
    recommendations: 'Recommendations',
    bestValue: 'Best Value: DeepSeek',
    bestValueDesc: 'For most tasks, DeepSeek provides excellent quality at a fraction of the cost. Perfect for high-volume agent workflows.',
    fastCheap: 'Fast & Cheap: Gemini Flash',
    fastCheapDesc: 'Gemini 1.5 Flash offers great speed and low cost. Good for real-time applications.',
    complexTasks: 'Complex Tasks: GPT-4o / Claude 3.5 Sonnet',
    complexTasksDesc: 'For complex reasoning, code generation, or nuanced tasks, premium models are worth it. Use AgentWatch to track when the extra cost is justified.',
    yourActualCosts: 'Your Actual Costs',
    yourActualCostsDesc: 'Based on your traces tracked by AgentWatch',
  },
  
  // Footer
  footer: {
    copyright: 'AgentWatch © 2026',
    slogan: 'Track, Debug, and Optimize Your AI Agents',
  },
}

export type Language = typeof en