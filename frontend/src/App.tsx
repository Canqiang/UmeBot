// frontend/src/App.tsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Send, Bot, User, TrendingUp, TrendingDown, DollarSign,
  Users, Package, ShoppingBag, UserPlus, ChevronDown,
  Loader, Calendar, BarChart3, Activity, Zap
} from 'lucide-react';
import { ChartView } from './components/ChartView';
import { ForecastChart } from './components/ForecastChart';
import { DetailModal } from './components/DetailModal';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { MarkdownMessage } from './components/MarkdownMessage';

// Types
interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: string;
  data?: any;
}

interface Metrics {
  total_revenue: number;
  total_orders: number;
  unique_customers: number;
  item_count?: number;
  new_users?: number;
  avg_order_value: number;
  changes?: {
    total_revenue?: number;
    order_count?: number;
    unique_customers?: number;
  };
}

interface DailyReport {
  date: string;
  highlights: string[];
  trends: Record<string, number>;
  insights: string[];
  metrics?: Metrics;
}

// 快速操作按钮
const quickActions = [
  { label: '📊 今日报表', query: '我想看看今天的数据分析报告', icon: <BarChart3 className="w-4 h-4" /> },
  { label: '📈 销售预测', query: '预测未来7天的销售额', icon: <Activity className="w-4 h-4" /> },
  { label: '💰 营收分析', query: '分析本周的营收情况', icon: <DollarSign className="w-4 h-4" /> },
  { label: '👥 客户洞察', query: '显示客户分群分析', icon: <Users className="w-4 h-4" /> },
  { label: '🎯 因果分析', query: '分析促销活动的效果', icon: <Zap className="w-4 h-4" /> }
];

// Components
const MetricCard: React.FC<{
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  onClick?: () => void;
}> = ({ title, value, change, icon, onClick }) => {
  const isPositive = change && change > 0;

  return (
    <div
      className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition-all cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-gray-600">{title}</span>
        <div className="p-2 bg-gray-50 rounded-lg">{icon}</div>
      </div>
      <div className="text-2xl font-bold text-gray-900 mb-2">{value}</div>
      {change !== undefined && change !== 0 && (
        <div className={`flex items-center text-sm font-medium ${
          isPositive ? 'text-green-600' : 'text-red-600'
        }`}>
          {isPositive ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
          {isPositive ? '+' : ''}{change.toFixed(1)}%
        </div>
      )}
    </div>
  );
};

const MessageBubble: React.FC<{
  message: Message;
  onChartPointClick?: (params: any) => void;
  onMetricClick?: (metric: string) => void;
  scrollToBottom?: () => void;
}> = ({ message, onChartPointClick, onMetricClick, scrollToBottom }) => {
  const isUser = message.type === 'user';
  const [showDetails, setShowDetails] = useState(false);
  const [detailData, setDetailData] = useState<any>(null);

  const renderData = () => {
    if (!message.data) return null;

    const { type, content, display_type } = message.data;
    const displayType = display_type || type;

    // 日报展示 - 在气泡内
    if (displayType === 'daily_report') {
      const report = content as DailyReport;
      return (
        <>
          <div className="mt-4 space-y-4">
            <div className="bg-white/50 rounded-xl p-5">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold text-lg text-gray-800">📊 数据概览</h4>
                <span className="text-sm text-gray-500">
                  {format(new Date(report.date), 'yyyy年MM月dd日', { locale: zhCN })}
                </span>
              </div>
              <div className="space-y-2">
                {report.highlights.map((highlight, idx) => (
                  <div key={idx} className="flex items-start">
                    <span className="text-blue-500 mr-2">•</span>
                    <span className="text-sm text-gray-700">{highlight}</span>
                  </div>
                ))}
              </div>
            </div>

            {report.insights && report.insights.length > 0 && (
              <div className="bg-white/50 rounded-xl p-5">
                <h4 className="font-semibold text-lg text-gray-800 mb-3">💡 关键洞察</h4>
                <ul className="space-y-2">
                  {report.insights.map((insight, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-purple-500 mr-2">→</span>
                      <span className="text-sm text-gray-700">{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {report.metrics && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <MetricCard
                  title="总营收"
                  value={`$${(report.metrics.total_revenue ?? 0).toLocaleString()}`}
                  change={report.trends?.total_revenue}
                  icon={<DollarSign className="w-5 h-5 text-blue-500" />}
                  onClick={() => onMetricClick?.('revenue')}
                />
                <MetricCard
                  title="订单数"
                  value={(report.metrics.total_orders ?? 0).toLocaleString()}
                  change={report.trends?.order_count}
                  icon={<Package className="w-5 h-5 text-green-500" />}
                  onClick={() => onMetricClick?.('orders')}
                />
                <MetricCard
                  title="客户数"
                  value={(report.metrics.unique_customers ?? 0).toLocaleString()}
                  change={report.trends?.unique_customers}
                  icon={<Users className="w-5 h-5 text-purple-500" />}
                  onClick={() => onMetricClick?.('customers')}
                />
                <MetricCard
                  title="商品数"
                  value={(report.metrics.item_count ?? 0).toLocaleString()}
                  icon={<ShoppingBag className="w-5 h-5 text-orange-500" />}
                  onClick={() => onMetricClick?.('items')}
                />
                <MetricCard
                  title="新用户"
                  value={(report.metrics.new_users ?? 0).toLocaleString()}
                  icon={<UserPlus className="w-5 h-5 text-pink-500" />}
                  onClick={() => onMetricClick?.('new_users')}
                />
                <MetricCard
                  title="客单价"
                  value={`$${(report.metrics.avg_order_value ?? 0).toFixed(2)}`}
                  change={report.trends?.avg_order_value}
                  icon={<DollarSign className="w-5 h-5 text-indigo-500" />}
                  onClick={() => onMetricClick?.('aov')}
                />
              </div>
            )}
          </div>
        </>
      );
    }

    // 指标卡片展示 - 在气泡内
    if (displayType === 'metrics_cards') {
      const metrics = content.metrics || content;
      return (
        <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-4">
          <MetricCard
            title="总营收"
            value={`$${(metrics.total_revenue ?? 0).toLocaleString()}`}
            change={metrics.changes?.total_revenue}
            icon={<DollarSign className="w-5 h-5 text-blue-500" />}
            onClick={() => onMetricClick?.('revenue')}
          />
          <MetricCard
            title="订单数"
            value={(metrics.total_orders ?? 0).toLocaleString()}
            change={metrics.changes?.order_count}
            icon={<Package className="w-5 h-5 text-green-500" />}
            onClick={() => onMetricClick?.('orders')}
          />
          <MetricCard
            title="客户数"
            value={(metrics.unique_customers ?? 0).toLocaleString()}
            change={metrics.changes?.unique_customers}
            icon={<Users className="w-5 h-5 text-purple-500" />}
            onClick={() => onMetricClick?.('customers')}
          />
          <MetricCard
            title="商品数"
            value={(metrics.item_count ?? 0).toLocaleString()}
            icon={<ShoppingBag className="w-5 h-5 text-orange-500" />}
            onClick={() => onMetricClick?.('items')}
          />
          <MetricCard
            title="新用户"
            value={(metrics.new_users ?? 0).toLocaleString()}
            icon={<UserPlus className="w-5 h-5 text-pink-500" />}
            onClick={() => onMetricClick?.('new_users')}
          />
          <MetricCard
            title="客单价"
            value={`$${(metrics.avg_order_value ?? 0).toFixed(2)}`}
            icon={<DollarSign className="w-5 h-5 text-indigo-500" />}
            onClick={() => onMetricClick?.('aov')}
          />
        </div>
      );
    }

    // 图表展示 - 在气泡内
    if (displayType === 'chart') {
      const chartData = content.chart || content;
      return (
        <div className="mt-4 bg-white/50 rounded-xl p-5">
          <ChartView data={chartData} onPointClick={onChartPointClick} />
        </div>
      );
    }

    // 预测展示 - 完全在气泡内
    if (displayType === 'forecast') {
      const forecastData = content.chart_data || content.chart || content;

      return (
        <div className="mt-4 bg-white/50 rounded-xl p-5">
          <div className="mb-4">
            <h4 className="font-semibold text-lg text-gray-800">📈 销售预测</h4>
            {content.forecast && (
              <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">预测总额</span>
                  <div className="font-semibold text-gray-800">${content.forecast.total_forecast?.toLocaleString()}</div>
                </div>
                <div>
                  <span className="text-gray-600">日均预测</span>
                  <div className="font-semibold text-gray-800">${content.forecast.avg_daily_forecast?.toFixed(2)}</div>
                </div>
                <div>
                  <span className="text-gray-600">预测天数</span>
                  <div className="font-semibold text-gray-800">{content.forecast.forecast_days}天</div>
                </div>
                <div>
                  <span className="text-gray-600">预测方法</span>
                  <div className="font-semibold text-gray-800">{content.method || '移动平均'}</div>
                </div>
              </div>
            )}
          </div>
          {/* 图表容器 */}
          <div className="w-full">
            <ForecastChart
              data={forecastData}
              height="350px"
              onRender={() => {
                setTimeout(() => {
                  if (scrollToBottom) {
                    scrollToBottom();
                  }
                }, 100);
              }}
            />
          </div>
        </div>
      );
    }

    // 因果分析展示 - 在气泡内
    if (displayType === 'causal_analysis') {
      return (
        <div className="mt-4 bg-white/50 rounded-xl p-5">
          <h4 className="font-semibold text-lg text-gray-800 mb-3">🎯 因果分析结果</h4>
          <div className="space-y-2 text-sm text-gray-700">
            <p>分析已完成，发现以下关键因素对销售的影响：</p>
            <ul className="space-y-1 ml-4">
              <li>• 促销活动效果显著</li>
              <li>• 周末销售额提升明显</li>
              <li>• 天气因素有一定影响</li>
            </ul>
          </div>
          <button
            onClick={() => {
              setDetailData(content);
              setShowDetails(true);
            }}
            className="mt-4 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
          >
            查看详细分析 →
          </button>
        </div>
      );
    }

    return null;
  };

  // 用户消息样式
  if (isUser) {
    return (
      <div className="flex justify-end mb-6">
        <div className="flex items-start max-w-[70%] flex-row-reverse">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center ml-3">
            <User className="w-5 h-5 text-white" />
          </div>
          <div className="bg-blue-500 text-white rounded-2xl px-5 py-3">
            {message.content}
          </div>
        </div>
      </div>
    );
  }

  // 机器人消息样式 - 所有内容都在气泡内
  return (
    <>
      <div className="flex justify-start mb-6">
        <div className="flex items-start max-w-[85%]">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center mr-3">
            <Bot className="w-5 h-5 text-white" />
          </div>

          {/* 消息气泡 - 包含文字和数据 */}
          <div className="bg-gray-100 rounded-2xl px-5 py-3 flex-1">
            {/* 文字内容 */}
            <MarkdownMessage content={message.content} />

            {/* 数据内容 - 在同一个气泡内 */}
            {renderData()}
          </div>
        </div>
      </div>

      {/* 详情弹窗 */}
      {showDetails && detailData && (
        <DetailModal
          isOpen={showDetails}
          onClose={() => setShowDetails(false)}
          title="详细分析"
          data={detailData}
          type="analysis"
        />
      )}
    </>
  );
};

// Main App Component - 使用固定布局防止溢出
export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const hasConnected = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // WebSocket连接
  const connectWebSocket = useCallback(() => {
    const wsUrl = `ws://localhost:8000/ws/${sessionId}`;

    try {
      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('连接出错，请刷新页面重试');
      };

      socket.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        if (hasConnected.current) {
          setTimeout(() => {
            connectWebSocket();
          }, 3000);
        }
      };
    } catch (error) {
      console.error('Failed to connect:', error);
      setConnectionError('无法连接到服务器');
    }
  }, [sessionId]);

  useEffect(() => {
    if (!hasConnected.current) {
      connectWebSocket();
      hasConnected.current = true;
    }

    return () => {
      hasConnected.current = false;
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket]);

  const handleWebSocketMessage = (data: any) => {
    if (data.type === 'bot_message') {
      const newMessage: Message = {
        id: `bot_${Date.now()}`,
        type: 'bot',
        content: data.message,
        timestamp: data.timestamp,
        data: data.data
      };
      setMessages(prev => [...prev, newMessage]);
      setIsLoading(false);
    } else if (data.type === 'error') {
      setConnectionError(data.message);
      setIsLoading(false);
    } else if (data.type === 'data_details') {
      console.log('Received details:', data.data);
    }
  };

  const sendMessage = () => {
    if (!inputValue.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    wsRef.current.send(JSON.stringify({
      type: 'chat',
      message: inputValue
    }));

    setInputValue('');
    inputRef.current?.focus();
  };

  const handleQuickAction = (query: string) => {
    setInputValue(query);
    setTimeout(() => {
      sendMessage();
    }, 10);
  };

  const handleChartPointClick = (params: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'chart_interaction',
        data: params
      }));
    }
  };

  const handleMetricClick = (metric: string) => {
    const queries: Record<string, string> = {
      revenue: '显示收入详情',
      orders: '显示订单详情',
      customers: '显示客户详情',
      items: '显示商品详情',
      new_users: '显示新用户详情',
      aov: '分析客单价趋势'
    };

    const query = queries[metric];
    if (query) {
      setInputValue(query);
      setTimeout(() => sendMessage(), 10);
    }
  };

  return (
    // 使用 fixed 定位防止页面溢出
    <div className="fixed inset-0 flex flex-col bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Header - 固定高度 */}
      <header className="flex-shrink-0 bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              UMe 数据助手
            </h1>
            <div className="flex items-center space-x-4">
              <div className={`flex items-center space-x-2 ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-600' : 'bg-red-600'} animate-pulse`} />
                <span className="text-sm">{isConnected ? '已连接' : '未连接'}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Messages Container - 可滚动区域 */}
      <main className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-5xl mx-auto">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <Bot className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-700 mb-2">欢迎使用 UMe 数据助手</h2>
              <p className="text-gray-500 mb-8">我可以帮您分析销售数据、预测趋势、寻找业务洞察</p>

              {/* Quick Actions */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 max-w-3xl mx-auto">
                {quickActions.map((action, index) => (
                  <button
                    key={index}
                    onClick={() => handleQuickAction(action.query)}
                    className="flex items-center justify-center space-x-2 px-4 py-3 bg-white rounded-lg shadow-sm hover:shadow-md transition-all border border-gray-100 hover:border-blue-200"
                  >
                    {action.icon}
                    <span className="text-sm font-medium text-gray-700">{action.label}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  onChartPointClick={handleChartPointClick}
                  onMetricClick={handleMetricClick}
                  scrollToBottom={scrollToBottom}
                />
              ))}

              {/* Loading indicator */}
              {isLoading && (
                <div className="flex justify-start mb-6">
                  <div className="flex items-start max-w-[85%]">
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center mr-3">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div className="bg-gray-100 rounded-2xl px-5 py-3">
                      <div className="flex items-center space-x-2">
                        <Loader className="w-4 h-4 animate-spin text-gray-600" />
                        <span className="text-gray-600">正在思考...</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* 滚动锚点 */}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </main>

      {/* Input Area - 固定在底部 */}
      <footer className="flex-shrink-0 bg-white border-t shadow-lg">
        <div className="max-w-5xl mx-auto px-4 py-4">
          {connectionError && (
            <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
              {connectionError}
            </div>
          )}

          <div className="flex items-center space-x-3">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="输入您的问题..."
              className="flex-1 px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={!isConnected || isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={!isConnected || isLoading || !inputValue.trim()}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                isConnected && !isLoading && inputValue.trim()
                  ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:from-blue-600 hover:to-purple-600 shadow-md hover:shadow-lg'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}