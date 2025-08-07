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

// WebSocket connection
let ws: WebSocket | null = null;

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
}> = ({ message, onChartPointClick, onMetricClick }) => {
  const isUser = message.type === 'user';
  const [showDetails, setShowDetails] = useState(false);
  const [detailData, setDetailData] = useState<any>(null);
  const bubbleClass = `rounded-2xl px-5 py-3 ${
    isUser ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-800'
  }`;

  const renderData = () => {
    if (!message.data) return null;

    const { type, content, display_type } = message.data;
    const displayType = display_type || type;

    // 日报展示
    if (displayType === 'daily_report') {
      const report = content as DailyReport;
      return (
        <div className="mt-4 space-y-4">
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-5">
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
            <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-5">
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
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
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
                icon={<DollarSign className="w-5 h-5 text-indigo-500" />}
                onClick={() => onMetricClick?.('aov')}
              />
            </div>
          )}
        </div>
      );
    }

    // 指标卡片展示
    if (displayType === 'metrics_cards') {
      const metrics = content.metrics as Metrics;
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

    // 图表展示
    if (displayType === 'chart') {
      const chartData = content.chart || content;
      return (
        <div className="mt-4 bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <ChartView data={chartData} onPointClick={onChartPointClick} />
        </div>
      );
    }

    // 预测展示
    if (displayType === 'forecast') {
      const forecastData = content.chart_data || content.chart || content;
      return (
        <div className="mt-4 bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <div className="mb-4">
            <h4 className="font-semibold text-lg text-gray-800">📈 销售预测</h4>
            {content.forecast && (
              <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">预测总额</span>
                  <div className="font-semibold">${content.forecast.total_forecast?.toLocaleString()}</div>
                </div>
                <div>
                  <span className="text-gray-500">日均预测</span>
                  <div className="font-semibold">${content.forecast.avg_daily_forecast?.toFixed(2)}</div>
                </div>
                <div>
                  <span className="text-gray-500">预测天数</span>
                  <div className="font-semibold">{content.forecast.forecast_days}天</div>
                </div>
                <div>
                  <span className="text-gray-500">预测方法</span>
                  <div className="font-semibold">{content.method || '移动平均'}</div>
                </div>
              </div>
            )}
          </div>
          <ForecastChart data={forecastData} />
        </div>
      );
    }

    // 因果分析展示
    if (displayType === 'causal_analysis') {
      return (
        <div className="mt-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-5">
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

  return (
    <>
      <div className={`message-container flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
        <div className={`flex items-start max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
          <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
            isUser ? 'bg-blue-500 ml-3' : 'bg-gray-700 mr-3'
          }`}>
            {isUser ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-white" />}
          </div>

          <div className="flex-1">
            {isUser ? (
              <div className={bubbleClass}>{message.content}</div>
            ) : (
              <MarkdownMessage content={message.content} className={bubbleClass} />
            )}
            {renderData()}
          </div>
        </div>
      </div>

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

// Main App Component
export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

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
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('连接出错，请刷新页面重试');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // 自动重连
        setTimeout(() => {
          if (!isConnected) {
            connectWebSocket();
          }
        }, 3000);
      };
    } catch (error) {
      console.error('Failed to connect:', error);
      setConnectionError('无法连接到服务器');
    }
  }, [sessionId, isConnected]);

  useEffect(() => {
    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

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
      // 处理详细数据
      console.log('Received details:', data.data);
    }
  };

  const sendMessage = () => {
    if (!inputValue.trim() || !ws || ws.readyState !== WebSocket.OPEN) return;

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    ws.send(JSON.stringify({
      type: 'chat',
      message: inputValue
    }));

    setInputValue('');
  };

  const handleQuickAction = (query: string) => {
    setInputValue(query);
    setTimeout(() => {
      sendMessage();
    }, 100);
  };

  const handleChartPointClick = (params: any) => {
    console.log('Chart point clicked:', params);
    // 可以发送请求获取该数据点的详细信息
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'get_details',
        detail_type: 'data_point',
        params: {
          date: params.name,
          value: params.value
        }
      }));
    }
  };

  const handleMetricClick = (metric: string) => {
    console.log('Metric clicked:', metric);
    // 可以发送请求获取该指标的详细信息
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'get_details',
        detail_type: 'metric_detail',
        params: {
          metric_name: metric
        }
      }));
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-800">UMe 智能数据助手</h1>
                <p className="text-xs text-gray-500">实时数据分析 · 智能预测 · 业务洞察</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className={`flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                isConnected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}>
                <div className={`w-2 h-2 rounded-full mr-2 ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                }`} />
                {isConnected ? '已连接' : connectionError ? '连接失败' : '连接中...'}
              </div>
              <span className="text-sm text-gray-500">
                {format(new Date(), 'HH:mm', { locale: zhCN })}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Connection Error */}
      {connectionError && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-3">
          <div className="flex items-center">
            <span className="text-sm text-red-700">{connectionError}</span>
            <button
              onClick={connectWebSocket}
              className="ml-auto text-sm text-red-600 hover:text-red-700 font-medium"
            >
              重新连接
            </button>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      {messages.length === 0 && (
        <div className="bg-white border-b px-6 py-5">
          <div className="max-w-5xl mx-auto">
            <p className="text-sm font-medium text-gray-600 mb-4">快速开始</p>
            <div className="flex flex-wrap gap-3">
              {quickActions.map((action, idx) => (
                <button
                  key={idx}
                  onClick={() => handleQuickAction(action.query)}
                  className="flex items-center px-4 py-2.5 bg-white border border-gray-200 hover:border-blue-300 hover:bg-blue-50 rounded-xl text-sm font-medium transition-all group"
                >
                  <span className="mr-2 group-hover:scale-110 transition-transform">{action.icon}</span>
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-5xl mx-auto">
          {messages.map(message => (
            <MessageBubble
              key={message.id}
              message={message}
              onChartPointClick={handleChartPointClick}
              onMetricClick={handleMetricClick}
            />
          ))}

          {isLoading && (
            <div className="flex items-center space-x-3 text-gray-500 mb-4">
              <Loader className="w-5 h-5 animate-spin" />
              <span className="text-sm">正在分析数据...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border-t px-6 py-4">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center space-x-4">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="输入你的问题，例如：分析本周销售趋势..."
              className="flex-1 px-5 py-3 bg-gray-50 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
              disabled={!isConnected}
            />
            <button
              onClick={sendMessage}
              disabled={!isConnected || !inputValue.trim()}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl hover:from-blue-600 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium flex items-center space-x-2"
            >
              <Send className="w-5 h-5" />
              <span>发送</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}