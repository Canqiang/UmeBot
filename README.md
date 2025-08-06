## 📁 项目结构总览

```
ume-bot/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── main.py            # FastAPI主应用（WebSocket + REST API）
│   │   ├── chat_manager.py    # 聊天会话管理（对话历史、上下文）
│   │   ├── llm_service.py     # LLM服务（意图识别、响应生成）
│   │   ├── analysis_service.py # 数据分析服务（因果分析、预测）
│   │   ├── database.py        # 数据库连接管理
│   │   ├── fixed_causal_inference.py       
│   │   ├── config.py          # 配置管理
│   │   └── models.py          # 数据模型定义
│   ├── requirements.txt       # Python依赖
│   ├── run.py                 # 启动脚本
│   ├── test_connection.py     # 测试脚本
│   └── .env                   # 环境变量
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── App.tsx            # 主聊天界面组件
│   │   ├── components/        # UI组件
│   │   │   ├── DetailModal.tsx
│   │   │   ├── ChartView.tsx
│   │   │   └── TableView.tsx
│   │   ├── services/          # API和WebSocket服务
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   ├── hooks/             # 自定义React Hooks
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useChat.ts
│   │   │   └── useAnalysis.ts
│   │   ├── types/             # TypeScript类型定义
│   │   │   └── index.ts
│   │   └── utils/             # 工具函数
│   │       ├── format.ts
│   │       ├── chartHelpers.ts
│   │       └── dataProcessor.ts
│   ├── package.json           # Node依赖
│   └── vite.config.ts         # Vite配置
│
├── docker-compose.yml         # Docker部署配置
├── start.sh                   # Linux/Mac启动脚本
├── start.bat                  # Windows启动脚本
└── README.md                  # 项目文档
```

## 🚀 快速启动指南

### 方式1: 使用启动脚本（推荐）

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```batch
start.bat
```

### 方式2: 手动启动

**后端:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

**前端:**
```bash
cd frontend
npm install
npm run dev
```

### 方式3: Docker Compose
```bash
docker-compose up -d
```

## 🌟 核心功能

### 1. **智能对话系统**
- ✅ 基于GPT-3.5的自然语言理解
- ✅ 多轮对话上下文管理
- ✅ 意图识别和实体提取
- ✅ WebSocket实时通信

### 2. **数据分析展示**
- ✅ 实时数据概览卡片
- ✅ 交互式图表（ECharts）
- ✅ 可排序/筛选的数据表格
- ✅ 详情弹窗查看

### 3. **因果分析**
- ✅ 促销效果分析
- ✅ 天气影响分析
- ✅ 节假日效应分析
- ✅ 交互效应和异质性分析

### 4. **销售预测**
- ✅ 7-15天销售预测
- ✅ 置信区间展示
- ✅ Prophet/多项式回归模型

### 5. **智能推荐**
- ✅ 基于分析结果的行动建议
- ✅ 优先级排序
- ✅ 预期效果评估

## 💬 使用示例

### 基础查询
- "我想看看今天的数据分析报告"
- "显示本周的销售趋势"
- "昨天的营收是多少？"

### 因果分析
- "分析最近促销活动的效果"
- "天气对销售有什么影响？"
- "周末效应有多大？"

### 预测查询
- "预测未来7天的销售额"
- "下周的销售趋势如何？"
- "需要准备多少库存？"

### 业务建议
- "如何提升销售额？"
- "给我一些营销建议"
- "哪些产品需要重点关注？"

## 🔧 配置说明

### 环境变量（.env）
```env
# OpenAI配置
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai-proxy.org/v1
OPENAI_MODEL=gpt-3.5-turbo

# ClickHouse配置
CLICKHOUSE_HOST=clickhouse-0-0.umetea.net
CLICKHOUSE_PORT=443
CLICKHOUSE_DB=dw
CLICKHOUSE_USER=ml_ume
CLICKHOUSE_PASSWORD=your-password
```

## 📊 数据流程

1. **用户输入** → WebSocket → 后端
2. **意图识别** → LLM解析用户意图
3. **数据获取** → 根据意图查询ClickHouse
4. **分析处理** → 因果分析/预测/聚合
5. **响应生成** → LLM生成自然语言回复
6. **结果展示** → 前端渲染图表/表格

## 🎯 技术亮点

- **前后端分离架构**：React + FastAPI
- **实时通信**：WebSocket双向通信
- **智能交互**：GPT驱动的自然语言理解
- **专业分析**：EconML因果推断 + Prophet预测
- **响应式设计**：TailwindCSS + 移动端适配
- **类型安全**：TypeScript全栈类型定义
- **容器化部署**：Docker Compose一键部署

## 📝 注意事项

1. 确保ClickHouse数据库连接正常
2. OpenAI API密钥需要有效
3. Python 3.10+ 和 Node.js 18+ 环境
4. 首次运行会自动安装依赖
5. 默认端口：前端3000，后端8000

## 🔗 访问地址

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs