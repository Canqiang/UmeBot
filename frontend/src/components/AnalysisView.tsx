import React from 'react';
import { TrendingUp, Info } from 'lucide-react';

// ============== AnalysisView Component ==============
interface AnalysisViewProps {
  data: {
    causal_effects?: Array<{
      factor: string;
      effect: number;
      confidence_interval: [number, number];
      significant: boolean;
    }>;
    interactions?: Array<{
      factors: string[];
      interaction_effect: number;
    }>;
    forecast?: {
      dates: string[];
      values: number[];
      confidence_lower?: number[];
      confidence_upper?: number[];
    };
    recommendations?: string[];
  };
}

export const AnalysisView: React.FC<AnalysisViewProps> = ({ data }) => {
  return (
    <div className="space-y-6">
      {/* Causal Effects */}
      {data.causal_effects && (
        <div className="bg-white border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
            因果效应分析
          </h3>
          <div className="space-y-4">
            {data.causal_effects.map((effect, idx) => (
              <div key={idx} className="border-l-4 border-blue-500 pl-4 py-2">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{effect.factor}</span>
                  <span className={`text-lg font-bold ${effect.effect > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {effect.effect > 0 ? '+' : ''}{effect.effect.toFixed(2)}
                  </span>
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  95% 置信区间: [{effect.confidence_interval[0].toFixed(2)}, {effect.confidence_interval[1].toFixed(2)}]
                  {effect.significant && <span className="ml-2 text-green-600">✓ 显著</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Interactions */}
      {data.interactions && data.interactions.length > 0 && (
        <div className="bg-gray-50 border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">交互效应</h3>
          <div className="grid grid-cols-2 gap-4">
            {data.interactions.map((interaction, idx) => (
              <div key={idx} className="bg-white p-4 rounded-lg">
                <div className="text-sm text-gray-600">{interaction.factors.join(' × ')}</div>
                <div className="text-xl font-bold mt-1">
                  {interaction.interaction_effect.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {data.recommendations && data.recommendations.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 text-blue-900">
            <Info className="w-5 h-5 inline mr-2" />
            行动建议
          </h3>
          <ul className="space-y-2">
            {data.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span className="text-gray-700">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
