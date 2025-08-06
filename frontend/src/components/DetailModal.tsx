import React, { useState, useEffect } from 'react';
import { X, Download, Filter, Search, ChevronLeft, ChevronRight, BarChart3, LineChart, PieChart, TrendingUp, Info } from 'lucide-react';
import * as echarts from 'echarts';

interface DetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  data: any;
  type: 'table' | 'chart' | 'analysis';
}

export const DetailModal: React.FC<DetailModalProps> = ({ isOpen, onClose, title, data, type }) => {
  if (!isOpen) return null;

  const renderContent = () => {
    switch (type) {
      case 'table':
        return <TableView data={data} />;
      case 'chart':
        return <ChartView data={data} />;
      case 'analysis':
        return <AnalysisView data={data} />;
      default:
        return <div>No data available</div>;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-100px)]">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};