import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Bot, User, TrendingUp, TrendingDown, DollarSign, Users, Package, ShoppingBag, UserPlus, ChevronDown, Loader } from 'lucide-react';
import { ChartView } from './components/ChartView';
import { DetailModal } from './components/DetailModal';


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
}

// WebSocket connection
let ws: WebSocket | null = null;

// Components
const MetricCard: React.FC<{
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
}> = ({ title, value, change, icon }) => {
  const isPositive = change && change > 0;

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-600">{title}</span>
        {icon}
      </div>
      <div className="text-2xl font-semibold mb-1">{value}</div>
      {change !== undefined && (
        <div className={`flex items-center text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
          {isPositive ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
          {Math.abs(change).toFixed(1)}%
        </div>
      )}
    </div>
  );
};

const MessageBubble: React.FC<{ message: Message; onChartPointClick?: (params: any) => void }> = ({ message, onChartPointClick }) => {
  const isUser = message.type === 'user';
  const [showDetails, setShowDetails] = useState(false);

  const renderData = () => {
    if (!message.data) return null;

    const { type, content, display_type } = message.data;
    const displayType = display_type || type;

    if (displayType === 'daily_report') {
      const report = content as DailyReport;
      return (
        <div className="mt-4 space-y-4">
          <div className="bg-white border rounded-lg p-4">
            <h4 className="font-semibold mb-3">📊 今日数据概览</h4>
            <div className="space-y-2">
              {report.highlights.map((highlight, idx) => (
                <div key={idx} className="text-sm">{highlight}</div>
              ))}
            </div>
          </div>

          {report.insights && report.insights.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-semibold text-blue-900 mb-2">💡 关键洞察</h4>
              <ul className="space-y-1">
                {report.insights.map((insight, idx) => (
                  <li key={idx} className="text-sm text-blue-800">{insight}</li>
                ))}
              </ul>
            </div>
          )}

          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-blue-600 text-sm hover:text-blue-700 flex items-center"
          >
            查看详细数据 <ChevronDown className={`w-4 h-4 ml-1 transform ${showDetails ? 'rotate-180' : ''}`} />
          </button>
        </div>
      );
    }

    if (displayType === 'metrics_cards') {
      const metrics = content.metrics as Metrics;
      return (
        <div className="mt-4 grid grid-cols-3 gap-4">
          <MetricCard
            title="总营收"
            value={`$${(metrics.total_revenue ?? 0).toLocaleString()}`}
            change={metrics.changes?.total_revenue}
            icon={<DollarSign className="w-4 h-4 text-gray-400" />}
          />
          <MetricCard
            title="订单数"
            value={(metrics.total_orders ?? 0).toLocaleString()}
            change={metrics.changes?.order_count}
            icon={<Package className="w-4 h-4 text-gray-400" />}
          />
          <MetricCard
            title="客户数"
            value={(metrics.unique_customers ?? 0).toLocaleString()}
            change={metrics.changes?.unique_customers}
            icon={<Users className="w-4 h-4 text-gray-400" />}
          />
          <MetricCard
            title="商品数"
            value={(metrics.item_count ?? 0).toLocaleString()}
            change={0}
            icon={<ShoppingBag className="w-4 h-4 text-gray-400" />}
          />
          <MetricCard
            title="新用户"
            value={(metrics.new_users ?? 0).toLocaleString()}
            change={0}
            icon={<UserPlus className="w-4 h-4 text-gray-400" />}
          />
          <MetricCard
            title="客单价"
            value={`$${(metrics.avg_order_value ?? 0).toFixed(2)}`}
            change={0}
            icon={<DollarSign className="w-4 h-4 text-gray-400" />}
          />
        </div>
      );
    }

    if (displayType === 'causal_analysis') {
      return (
        <div className="mt-4 bg-white border rounded-lg p-4">
          <h4 className="font-semibold mb-3">🎯 因果分析结果</h4>
          <div className="space-y-2 text-sm">
            <p>分析已完成，点击查看详细报告</p>
          </div>
          <button
            onClick={() => setShowDetails(true)}
            className="mt-3 text-blue-600 text-sm hover:text-blue-700"
          >
            查看完整分析 →
          </button>
        </div>
      );
    }

    if (displayType === 'chart') {
      const chart = content.chart;
      if (Array.isArray(chart)) {
        return (
          <div className="mt-4">
            <ForecastChart data={chart} />
          </div>
        );
      }
      return (
        <div className="mt-4">
          <ChartView data={chart} />
        </div>
      );
    }

    if (displayType === 'forecast') {
      const chart = content.chart || content;
      return (
        <div className="mt-4">

          <ChartView data={content.chart} onPointClick={onChartPointClick} />

        </div>
      );
    }

    return null;
  };

  return (
    <div className={`message-container flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div className={`flex items-start max-w-[70%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div className={`flex-shrink-0 w-10 h-10 rounded flex items-center justify-center ${
          isUser ? 'bg-blue-100 ml-3' : 'bg-gray-100 mr-3'
        }`}>
          {isUser ? <User className="w-5 h-5 text-blue-600" /> : <Bot className="w-5 h-5 text-gray-600" />}
        </div>

        <div>
          <div className={`rounded-lg px-4 py-3 ${
            isUser 
              ? 'bg-blue-50 text-blue-900 rounded-tr-none' 
              : 'bg-white border border-gray-200 rounded-tl-none'
          }`}>
            <p className="whitespace-pre-wrap">{message.content}</p>
            {renderData()}
          </div>
          <div className={`text-xs text-gray-500 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
            {new Date(message.timestamp).toLocaleTimeString('zh-CN', {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Component
export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [detailModal, setDetailModal] = useState<{ title: string; data: any; type: 'table' | 'chart' | 'analysis' } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const baseUrl = import.meta.env.VITE_API_WS_URL;
      if (!baseUrl) {
        console.error('VITE_API_WS_URL is not set');
        setConnectionError('WebSocket URL not configured');
        return;
      }

      ws = new WebSocket(`${baseUrl}/ws/chat/${sessionId}`);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'bot_message') {
          const newMessage: Message = {
            id: `msg_${Date.now()}`,
            type: 'bot',
            content: data.message,
            timestamp: data.timestamp,
            data: data.data
          };
          setMessages(prev => [...prev, newMessage]);
          setIsLoading(false);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
        setConnectionError('WebSocket connection failed. Retrying...');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setConnectionError('WebSocket disconnected. Reconnecting...');
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [sessionId]);

  const sendMessage = useCallback(() => {
    if (!inputValue.trim() || !ws || ws.readyState !== WebSocket.OPEN) return;

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
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
    inputRef.current?.focus();
  }, [inputValue]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleChartPointClick = (params: any) => {
    setDetailModal({
      title: `${params.seriesName ?? ''}${params.name ? ' - ' + params.name : ''}`,
      data: {
        columns: [
          { key: 'series', title: 'Series' },
          { key: 'category', title: 'Category' },
          { key: 'value', title: 'Value', type: 'number' }
        ],
        rows: [
          {
            series: params.seriesName,
            category: params.name,
            value: Array.isArray(params.value) ? params.value[1] ?? params.value[0] : params.value
          }
        ]
      },
      type: 'table'
    });
  };

  // Quick actions
  const quickActions = [
    { label: '📊 查看日报', query: '我想看看今天的数据分析报告' },
    { label: '📈 销售预测', query: '预测未来7天的销售趋势' },
    { label: '🎯 因果分析', query: '分析最近促销活动的效果' },
    { label: '💡 业务建议', query: '基于数据给我一些业务建议' }
  ];

  const handleQuickAction = (query: string) => {
    setInputValue(query);
    setTimeout(() => {
      sendMessage();
    }, 100);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4 shadow-lg">
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <div className="flex items-center space-x-3">
            <Bot className="w-8 h-8" />
            <div>
              <h1 className="text-xl font-semibold">UMe Bot</h1>
              <p className="text-sm text-blue-100">智能数据助手</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            } bg-opacity-20`}>
              <div className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-400' : 'bg-red-400'
              }`} />
              <span className="text-sm">
                {isConnected ? '已连接' : connectionError ? '连接失败' : '连接中...'}
              </span>
            </div>
            <span className="text-sm">
              {new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        </div>
      </header>

      {connectionError && (
        <div className="bg-red-100 text-red-700 text-center py-2">
          {connectionError}
        </div>
      )}

      {/* Quick Actions */}
      {messages.length === 0 && (
        <div className="bg-white border-b px-6 py-4">
          <div className="max-w-4xl mx-auto">
            <p className="text-sm text-gray-600 mb-3">快速开始：</p>
            <div className="flex flex-wrap gap-2">
              {quickActions.map((action, idx) => (
                <button
                  key={idx}
                  onClick={() => handleQuickAction(action.query)}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm transition-colors"
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-4xl mx-auto">
          {messages.map(message => (
            <MessageBubble key={message.id} message={message} onChartPointClick={handleChartPointClick} />
          ))}

          {isLoading && (
            <div className="flex items-center space-x-2 text-gray-500 mb-4">
              <Loader className="w-4 h-4 animate-spin" />
              <span className="text-sm">正在分析...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border-t px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center space-x-4">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="请输入您的问题..."
              className="flex-1 px-4 py-3 bg-gray-50 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={!isConnected}
            />
            <button
              onClick={sendMessage}
              disabled={!isConnected || !inputValue.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors"
            >
              <span>发送</span>
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
      {detailModal && (
        <DetailModal
          isOpen={true}
          onClose={() => setDetailModal(null)}
          title={detailModal.title}
          data={detailModal.data}
          type={detailModal.type}
        />
      )}
    </div>
  );
}