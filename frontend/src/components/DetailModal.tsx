import React, { useState } from 'react';
import { X, Download, Share2, Maximize2 } from 'lucide-react';
import { TableView } from './TableView';
import { ChartView } from './ChartView';
import { AnalysisView } from './AnalysisView';

interface DetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  data: any;
  type: 'table' | 'chart' | 'analysis' | 'mixed';
}

export const DetailModal: React.FC<DetailModalProps> = ({
  isOpen,
  onClose,
  title,
  data,
  type
}) => {
  const [activeTab, setActiveTab] = useState(0);

  if (!isOpen) return null;

  const renderContent = () => {
    switch (type) {
      case 'table':
        return <TableView data={data} />;
      case 'chart':
        return <ChartView data={data} height="500px" />;
      case 'analysis':
        return <AnalysisView data={data} />;
      case 'mixed':
        return (
          <div className="space-y-6">
            {data.chart && <ChartView data={data.chart} height="400px" />}
            {data.table && <TableView data={data.table} />}
            {data.analysis && <AnalysisView data={data.analysis} />}
          </div>
        );
      default:
        return <div className="text-center text-gray-500 py-8">暂无数据</div>;
    }
  };

  const handleShare = () => {
    // 实现分享功能
    console.log('Share clicked');
  };

  const handleDownload = () => {
    // 实现下载功能
    const dataStr = JSON.stringify(data, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${title.replace(/\s+/g, '_')}_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* 背景遮罩 */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* 模态框 */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden transform transition-all">
          {/* 头部 */}
          <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-blue-50 to-indigo-50">
            <h2 className="text-xl font-bold text-gray-900">{title}</h2>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleShare}
                className="p-2 hover:bg-white rounded-lg transition-colors"
                title="分享"
              >
                <Share2 className="w-5 h-5 text-gray-600" />
              </button>
              <button
                onClick={handleDownload}
                className="p-2 hover:bg-white rounded-lg transition-colors"
                title="下载"
              >
                <Download className="w-5 h-5 text-gray-600" />
              </button>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white rounded-lg transition-colors"
                title="关闭"
              >
                <X className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>

          {/* 内容区域 */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-100px)]">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  );
};