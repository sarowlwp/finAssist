// API 接口定义

const API_BASE_URL = 'http://localhost:8001/api';

// SSE 事件类型定义
interface StreamEvent {
  type: 'start' | 'progress' | 'agent_result' | 'fusion_result' | 'complete' | 'error';
  [key: string]: any;
}

// 流式回调函数类型
type StreamDataCallback = (data: StreamEvent) => void;
type StreamErrorCallback = (error: string) => void;

// 通用请求函数
async function apiRequest(url: string, options: RequestInit = {}) {
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${url}`, defaultOptions);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API 请求失败: ${response.status} ${response.statusText} - ${errorText}`);
    }

    return response.json();
  } catch (error) {
    console.error('API 请求错误:', error);
    throw error;
  }
}

// 公司概况类型定义
export interface CompanyProfile {
  success: boolean;
  ticker: string;
  company_name?: string;
  name?: string;
  country?: string;
  currency?: string;
  exchange?: string;
  industry?: string;
  market_cap?: number;
  marketCapitalization?: number;
  description?: string;
  website?: string;
  weburl?: string;
  ir_website?: string;
  earnings_url?: string;
  logo?: string;
  timestamp?: string;
  error?: string;
}

// 财务指标类型定义
export interface Financials {
  success: boolean;
  ticker: string;
  pe_ratio?: number;
  peRatio?: number;
  pb_ratio?: number;
  pbRatio?: number;
  ps_ratio?: number;
  psRatio?: number;
  roe?: number;
  roa?: number;
  profit_margin?: number;
  netMargin?: number;
  dividend_yield?: number;
  dividendYield?: number;
  debt_to_equity?: number;
  debtToEquity?: number;
  current_ratio?: number;
  currentRatio?: number;
  quick_ratio?: number;
  quickRatio?: number;
  revenue_growth?: number;
  revenueGrowth?: number;
  earnings_growth?: number;
  epsGrowth?: number;
  timestamp?: string;
  error?: string;
}

// 技术指标类型定义
export interface TechnicalIndicators {
  success: boolean;
  ticker: string;
  current_price?: number;
  rsi?: number;
  macd?: {
    macd: number;
    signal: number;
    histogram: number;
  };
  bollinger_bands?: {
    upper: number;
    middle: number;
    lower: number;
  };
  bollingerUpper?: number;
  bollingerMiddle?: number;
  bollingerLower?: number;
  rsi_signal?: string;
  timestamp?: string;
  error?: string;
}

// 基本面数据类型定义
export interface FundamentalsData {
  ticker: string;
  company_profile?: CompanyProfile;
  companyProfile?: CompanyProfile;
  financials?: Financials;
  technical_indicators?: TechnicalIndicators;
  technicalIndicators?: TechnicalIndicators;
  timestamp?: string;
  lastUpdated?: string;
  success?: boolean;
  message?: string;
}

// 投资组合管理
export const portfolioApi = {
  // 获取投资组合汇总信息
  getSummary: async () => {
    return apiRequest('/portfolio/summary');
  },

  // 获取投资组合列表
  getAll: async () => {
    return apiRequest('/portfolio');
  },

  // 添加投资组合项目
  add: async (item: any) => {
    return apiRequest('/portfolio', {
      method: 'POST',
      body: JSON.stringify(item),
    });
  },

  // 更新投资组合项目
  update: async (ticker: string, item: any) => {
    return apiRequest(`/portfolio/${ticker}`, {
      method: 'PUT',
      body: JSON.stringify(item),
    });
  },

  // 删除投资组合项目
  delete: async (ticker: string) => {
    return apiRequest(`/portfolio/${ticker}`, {
      method: 'DELETE',
    });
  },

  // 获取单只股票基本面数据
  getFundamentals: async (ticker: string): Promise<FundamentalsData> => {
    return apiRequest(`/portfolio/${ticker}/fundamentals`);
  },

  // 手动刷新股票基本面数据
  refreshFundamentals: async (ticker: string): Promise<FundamentalsData> => {
    return apiRequest(`/portfolio/${ticker}/fundamentals/refresh`, {
      method: 'POST',
    });
  },
};

// 分析服务
export const analysisApi = {
  // 分析单个股票
  analyzeStock: async (ticker: string) => {
    return apiRequest(`/analysis/${ticker}`);
  },

  // 分析投资组合
  analyzePortfolio: async (tickers: string[]) => {
    return apiRequest('/analysis/portfolio', {
      method: 'POST',
      body: JSON.stringify({ tickers }),
    });
  },

  // 启动异步分析任务
  startTickerAnalysis: async (ticker: string) => {
    return apiRequest('/analysis/ticker/start', {
      method: 'POST',
      body: JSON.stringify({ ticker }),
    });
  },

  // 获取分析任务列表
  getAnalysisTasks: async (ticker?: string, limit: number = 20) => {
    const queryParams = new URLSearchParams();
    if (ticker) queryParams.append('ticker', ticker);
    queryParams.append('limit', limit.toString());
    return apiRequest(`/analysis/tasks?${queryParams.toString()}`);
  },

  // 删除分析任务
  deleteTask: async (taskId: string) => {
    return apiRequest(`/analysis/tasks/${taskId}`, {
      method: 'DELETE',
    });
  },

  // 获取单个分析任务状态
  getAnalysisTask: async (taskId: string) => {
    return apiRequest(`/analysis/tasks/${taskId}`);
  },

  // Stream analysis
  analyzeTickerStream: (ticker: string, onData: StreamDataCallback, onError: StreamErrorCallback) => {
    const controller = new AbortController();
    const signal = controller.signal;

    // 立即启动异步操作
    (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/analysis/ticker/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ ticker }),
          signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        if (reader) {
          while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value);

            // 分割 SSE 消息
            const messages = buffer.split('\n\n');
            buffer = messages.pop() || '';

            for (const message of messages) {
              if (message.startsWith('data: ')) {
                try {
                  const data = JSON.parse(message.slice(6));
                  onData(data);
                } catch (e) {
                  console.error('Failed to parse SSE data:', e);
                }
              }
            }
          }
        }
      } catch (error) {
        if (!signal.aborted) {
          onError(error instanceof Error ? error.message : 'Unknown error');
        }
      }
    })();

    return () => controller.abort();
  },

  // 获取分析报告列表
  getReports: async (ticker?: string, limit: number = 20) => {
    const queryParams = new URLSearchParams();
    if (ticker) queryParams.append('ticker', ticker);
    queryParams.append('limit', limit.toString());
    return apiRequest(`/analysis/reports?${queryParams.toString()}`);
  },

  // 获取单个分析报告详情
  getReport: async (reportId: string) => {
    return apiRequest(`/analysis/reports/${reportId}`);
  },

  // 删除分析报告
  deleteReport: async (reportId: string) => {
    return apiRequest(`/analysis/reports/${reportId}`, {
      method: 'DELETE',
    });
  },
};

// Agents 管理
export const agentsApi = {
  // 获取所有可用的 Agents
  list: async () => {
    return apiRequest('/agents');
  },

  // 与特定 Agent 聊天
  chat: async (agentName: string, message: string) => {
    return apiRequest(`/agents/${agentName}/chat`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  },

  // 获取 Agent 状态
  getStatus: async (agentName: string) => {
    return apiRequest(`/agents/${agentName}/status`);
  },
};

// Export agentApi for backward compatibility
export const agentApi = {
  getAll: async () => {
    return apiRequest('/agents');
  },

  chat: async (agentName: string, message: string, config: any) => {
    return apiRequest(`/agents/${agentName}/chat`, {
      method: 'POST',
      body: JSON.stringify({ message, config }),
    });
  },

  getSkills: async (agentName: string) => {
    return apiRequest(`/agents/${agentName}/skills`);
  },

  createSkill: async (agentName: string, skill: any) => {
    return apiRequest(`/agents/${agentName}/skills`, {
      method: 'POST',
      body: JSON.stringify(skill),
    });
  },

  installFromGithub: async (agentName: string, url: string) => {
    return apiRequest(`/agents/${agentName}/skills/github`, {
      method: 'POST',
      body: JSON.stringify({ url }),
    });
  },

  uninstallSkill: async (agentName: string, skillName: string) => {
    return apiRequest(`/agents/${agentName}/skills/${skillName}`, {
      method: 'DELETE',
    });
  },

  createAgent: async (agent: any) => {
    return apiRequest('/agents', {
      method: 'POST',
      body: JSON.stringify(agent),
    });
  },

  deleteAgent: async (agentName: string) => {
    return apiRequest(`/agents/${agentName}`, {
      method: 'DELETE',
    });
  },
};

// 市场数据
export const marketApi = {
  // 获取实时市场数据
  getMarketData: async (tickers: string[]) => {
    return apiRequest('/market/data', {
      method: 'POST',
      body: JSON.stringify({ tickers }),
    });
  },

  // 获取股票报价
  getQuote: async (ticker: string) => {
    return apiRequest(`/market/quote/${ticker}`);
  },

  // 获取公司概况
  getProfile: async (ticker: string) => {
    return apiRequest(`/market/profile/${ticker}`);
  },

  // 获取市场新闻
  getNews: async (ticker: string) => {
    return apiRequest(`/market/news/${ticker}`);
  },
};

// 设置管理
export const settingsApi = {
  // 获取设置
  get: async () => {
    return apiRequest('/settings');
  },

  // 更新设置
  update: async (settings: any) => {
    return apiRequest('/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  },

  // 获取 API 密钥设置
  getApiKeys: async () => {
    return apiRequest('/settings/api-keys');
  },

  // 更新 API 密钥
  updateApiKeys: async (apiKeys: any) => {
    return apiRequest('/settings/api-keys', {
      method: 'PUT',
      body: JSON.stringify(apiKeys),
    });
  },

  // 获取用户自定义 Agents 设置
  getCustomAgents: async () => {
    return apiRequest('/settings/custom-agents');
  },

  // 更新用户自定义 Agents
  updateCustomAgents: async (customAgents: any) => {
    return apiRequest('/settings/custom-agents', {
      method: 'PUT',
      body: JSON.stringify(customAgents),
    });
  },

  // Investment style management
  updateInvestmentStyle: async (style: string) => {
    return apiRequest('/settings/investment-style', {
      method: 'PUT',
      body: JSON.stringify({ investment_style: style }),
    });
  },

  // Model config management
  updateModelConfig: async (config: any) => {
    return apiRequest('/settings/model-config', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  },

  // Agent model config
  getAgentModelConfig: async (agentName: string) => {
    return apiRequest(`/settings/agents/${agentName}/model-config`);
  },

  updateAgentModelConfig: async (agentName: string, config: any) => {
    return apiRequest(`/settings/agents/${agentName}/model-config`, {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  },

  // Agent skills
  getAgentSkills: async (agentName: string) => {
    return apiRequest(`/settings/agents/${agentName}/skills`);
  },
};

// 健康检查
export const healthApi = {
  // 检查服务健康状态
  check: async () => {
    return apiRequest('/health');
  },
};
