import React from 'react';
import { TrendingUp, TrendingDown, AlertCircle, CheckCircle, Target, Zap } from 'lucide-react';

interface AnalysisViewProps {
  data: any;
}

export const AnalysisView: React.FC<AnalysisViewProps> = ({ data }) => {
  // 因果效应数据
  const causalEffects = data.causal_effects || [];
  const interactions = data.interactions || [];
  const recommendations = data.recommendations || [];
  const forecast = data.forecast || null;

  return (
    <div className="space-y-6">
      {/* 因果效应分析 */}
      {causalEffects.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center mb-4">
            <Zap className="w-5 h-5 text-purple-500 mr-2" />
            <h3 className="text-lg font-semibold text-gray-800">因果效应分析</h3>
          </div>

          <div className="space-y-4">
            {causalEffects.map((effect: any, index: number) => (
              <div key={index} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-700">{effect.factor}</span>
                  <span className={`text-sm font-semibold ${
                    effect.significant ? 'text-green-600' : 'text-gray-500'
                  }`}>
                    {effect.significant ? '显著' : '不显著'}
                  </span>
                </div>

                <div className="flex items-center space-x-4 text-sm">
                  <div>
                    <span className="text-gray-500">效应值: </span>
                    <span className="font-medium">
                      {effect.effect > 0 ? '+' : ''}{effect.effect.toFixed(2)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">置信区间: </span>
                    <span className="font-medium">
                      [{effect.confidence_interval[0].toFixed(2)}, {effect.confidence_interval[1].toFixed(2)}]
                    </span>
                  </div>
                  {effect.sample_size && (
                    <div>
                      <span className="text-gray-500">样本量: </span>
                      <span className="font-medium">{effect.sample_size.toLocaleString()}</span>
                    </div>
                  )}
                </div>

                {/* 效应值可视化 */}
                <div className="mt-3">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        effect.effect > 0 ? 'bg-green-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.min(Math.abs(effect.effect), 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 交互效应 */}
      {interactions.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center mb-4">
            <Target className="w-5 h-5 text-blue-500 mr-2" />
            <h3 className="text-lg font-semibold text-gray-800">交互效应</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {interactions.map((interaction: any, index: number) => (
              <div key={index} className="bg-blue-50 rounded-lg p-4">
                <div className="font-medium text-gray-700 mb-2">
                  {interaction.factors.join(' × ')}
                </div>
                <div className="text-2xl font-bold text-blue-600">
                  {interaction.interaction_effect > 0 ? '+' : ''}
                  {interaction.interaction_effect.toFixed(1)}%
                </div>
                {interaction.combined_effect && (
                  <div className="text-sm text-gray-500 mt-1">
                    综合效应: {interaction.combined_effect.toFixed(1)}%
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 预测结果 */}
      {forecast && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center mb-4">
            <TrendingUp className="w-5 h-5 text-green-500 mr-2" />
            <h3 className="text-lg font-semibold text-gray-800">销售预测</h3>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-sm text-gray-500 mb-1">预测总额</div>
              <div className="text-xl font-bold text-gray-800">
                ${forecast.total_forecast?.toLocaleString()}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500 mb-1">日均预测</div>
              <div className="text-xl font-bold text-gray-800">
                ${forecast.avg_daily_forecast?.toFixed(0)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500 mb-1">最高预测</div>
              <div className="text-xl font-bold text-green-600">
                ${forecast.max_daily_forecast?.toFixed(0)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500 mb-1">最低预测</div>
              <div className="text-xl font-bold text-red-600">
                ${forecast.min_daily_forecast?.toFixed(0)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 建议和行动方案 */}
      {recommendations.length > 0 && (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-6">
          <div className="flex items-center mb-4">
            <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-800">行动建议</h3>
          </div>

          <div className="space-y-3">
            {recommendations.map((rec: string, index: number) => (
              <div key={index} className="flex items-start">
                <span className="flex-shrink-0 w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-xs font-bold mr-3">
                  {index + 1}
                </span>
                <p className="text-gray-700 flex-1">{rec}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 警告信息 */}
      {data.warnings && data.warnings.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
          <div className="flex items-center mb-2">
            <AlertCircle className="w-5 h-5 text-yellow-600 mr-2" />
            <h4 className="font-semibold text-yellow-800">注意事项</h4>
          </div>
          <ul className="space-y-1 text-sm text-yellow-700">
            {data.warnings.map((warning: string, index: number) => (
              <li key={index}>• {warning}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};