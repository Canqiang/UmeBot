// ============== src/types/index.ts ==============
export interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: string;
  data?: MessageData;
  metadata?: Record<string, any>;
}

export interface MessageData {
  type: 'daily_report' | 'metrics_cards' | 'chart' | 'table' | 'causal_analysis' | 'forecast';
  content: any;
  display_type?: string;
}

export interface DailyReport {
  date: string;
  highlights: string[];
  trends: Record<string, number>;
  insights: string[];
  metrics?: Metrics;
}

export interface Metrics {
  total_revenue: number;
  total_orders: number;
  unique_customers: number;
  item_count: number;
  new_users: number;
  avg_order_value: number;
  conversion_rate?: number;
  changes?: MetricChanges;
}

export interface MetricChanges {
  total_revenue?: number;
  order_count?: number;
  unique_customers?: number;
  conversion_rate?: number;
}

export interface ChartData {
  type: 'line' | 'bar' | 'pie' | 'scatter' | 'mixed';
  title?: string;
  series: ChartSeries[];
  xAxis?: AxisConfig;
  yAxis?: AxisConfig;
  options?: Record<string, any>;
}

export interface ChartSeries {
  name: string;
  data: any[];
  type?: string;
  smooth?: boolean;
  areaStyle?: any;
  color?: string;
}

export interface AxisConfig {
  type: 'category' | 'value' | 'time';
  data?: any[];
  name?: string;
}

export interface TableData {
  columns: TableColumn[];
  rows: Record<string, any>[];
  total?: number;
  page?: number;
  pageSize?: number;
}

export interface TableColumn {
  key: string;
  title: string;
  type?: 'string' | 'number' | 'currency' | 'percentage' | 'date' | 'datetime';
  width?: number;
  sortable?: boolean;
  filterable?: boolean;
}

export interface CausalEffect {
  factor: string;
  effect: number;
  confidence_interval: [number, number];
  significant: boolean;
  sample_size?: number;
}

export interface InteractionEffect {
  factors: string[];
  interaction_effect: number;
  combined_effect?: number;
}

export interface ForecastData {
  dates: string[];
  values: number[];
  confidence_lower?: number[];
  confidence_upper?: number[];
  method?: string;
  summary?: ForecastSummary;
  chart_data?: ChartData;
}

export interface ForecastSummary {
  total_forecast: number;
  avg_daily_forecast: number;
  max_daily_forecast: number;
  min_daily_forecast: number;
  forecast_days: number;
}

export interface AnalysisResult {
  period: {
    start: string;
    end: string;
  };
  causal_effects?: CausalEffect[];
  interactions?: InteractionEffect[];
  heterogeneity?: Record<string, any>;
  forecast?: ForecastData;
  recommendations?: string[];
}

export interface QueryIntent {
  query: string;
  intent_type: string;
  entities: Record<string, any>;
  needs_data: boolean;
  time_range?: TimeRange;
  metrics?: string[];
}

export interface TimeRange {
  type: 'relative' | 'absolute';
  value?: string;
  start?: string;
  end?: string;
}

export interface WebSocketMessage {
  type: string;
  message?: string;
  data?: any;
  timestamp?: string;
  error?: string;
}

export interface Session {
  id: string;
  created_at: string;
  messages: Message[];
  context: Record<string, any>;
}




