// frontend/src/App.tsx
import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

const App: React.FC = () => {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chartRef.current) {
      const chart = echarts.init(chartRef.current);
      chart.setOption({
        animation: false,
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: {
          type: 'category',
          data: ['1月','2月','3月','4月','5月','6月','7月','8月'],
          axisLine: { lineStyle: { color: '#E5E7EB' } }
        },
        yAxis: {
          type: 'value',
          axisLine: { lineStyle: { color: '#E5E7EB' } },
          splitLine: { lineStyle: { color: '#E5E7EB' } }
        },
        series: [{
          data: [820, 932, 901, 934, 1290, 1330, 1320, 1450],
          type: 'line',
          smooth: true,
          itemStyle: { color: '#4CAF50' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(76,175,80,0.2)' },
                { offset: 1, color: 'rgba(76,175,80,0)' }
              ]
            }
          }
        }]
      });
    }
  }, []);

  return (
    <div className="flex flex-col h-screen bg-white font-sans">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b bg-white">
        <div className="flex items-center space-x-4">
          <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
            <i className="fas fa-robot text-white"></i>
          </div>
          <div>
            <h1 className="text-lg font-medium">UMe Bot</h1>
            <p className="text-sm text-gray-500">09:00 AM</p>
          </div>
        </div>
        <button className="px-4 py-2 bg-primary text-white rounded-lg">
          查看详情 <i className="fas fa-arrow-right ml-2"></i>
        </button>
      </header>

      {/* Main */}
      <main className="flex-1 p-6 bg-white overflow-auto">
        {/* Data Cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {/* 卡片示例 */}
          <div className="bg-white rounded-lg p-4 shadow">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
              <span>总访问量</span>
              <i
                className="fas fa-question-circle text-gray-400 cursor-help"
                title="24小时内访问网站的总人次，包括新访客和老访客"
              ></i>
            </div>
            <div className="text-2xl font-semibold">942,876</div>
            <div className="text-sm text-green-500 mt-1">↑ 7.15%</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
              <span>活跃用户</span>
              <i
                className="fas fa-question-circle text-gray-400 cursor-help"
                title="当日至少进行过一次有效互动的独立用户数"
              ></i>
            </div>
            <div className="text-2xl font-semibold">2,143</div>
            <div className="text-sm text-green-500 mt-1">↑ 8.3%</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
              <span>转化率</span>
              <i
                className="fas fa-question-circle text-gray-400 cursor-help"
                title="完成目标行为的用户占总访问用户的百分比，包括注册、购买等"
              ></i>
            </div>
            <div className="text-2xl font-semibold">15.8%</div>
            <div className="text-sm text-green-500 mt-1">↑ 2.1%</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
              <span>平均停留时间</span>
              <i
                className="fas fa-question-circle text-gray-400 cursor-help"
                title="用户在网站的平均访问时长，反映内容吸引力和用户粘性"
              ></i>
            </div>
            <div className="text-2xl font-semibold">14:30</div>
            <div className="text-sm text-red-500 mt-1">↓ 1.2%</div>
          </div>
        </div>

        {/* Chart */}
        <div className="bg-white rounded-lg p-4 shadow">
          <h2 className="text-sm text-gray-600 mb-2">数据趋势</h2>
          <div ref={chartRef} style={{ width: '100%', height: '300px' }}></div>
        </div>

        {/* Chat */}
        <div className="mt-6 bg-gray-50 rounded-lg p-4 shadow">
          <div className="h-64 overflow-y-auto mb-4 space-y-4">
            {/* Bot Message */}
            <div className="flex items-start">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center mr-3">
                <i className="fas fa-robot text-white"></i>
              </div>
              <div className="bg-white rounded-lg p-3 shadow-sm max-w-2xl">
                <p className="text-gray-800">你好！我是 UMe 数据助手，很高兴为你服务。</p>
              </div>
            </div>
            {/* User Message */}
            <div className="flex items-start justify-end">
              <div className="bg-primary bg-opacity-10 rounded-lg p-3 shadow-sm max-w-2xl">
                <p className="text-gray-800">我想看看今天的数据分析报告</p>
              </div>
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center ml-3">
                <i className="fas fa-user text-gray-500"></i>
              </div>
            </div>
          </div>
          <div className="flex items-center bg-white rounded-lg border p-2">
            <input
              type="text"
              className="flex-1 px-3 py-2 text-sm border-none focus:outline-none"
              placeholder="请输入您的问题..."
            />
            <button className="px-4 py-2 bg-primary text-white rounded-lg ml-2 whitespace-nowrap">
              发送 <i className="fas fa-paper-plane ml-1"></i>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
