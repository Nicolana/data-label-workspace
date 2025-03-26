# 对话微调数据管理平台

一个用于管理和导出对话数据的现代化 Web 应用，专为大语言模型微调数据准备而设计。

## 功能特点

- 📝 创建、编辑和管理多轮对话
- 🔄 支持多种角色消息（系统、用户、助手）
- 📊 Markdown 编辑器提供丰富的文本格式化能力
- 💾 导出单个或批量对话为标准 JSONL 格式
- 🎨 现代化 UI 设计，提供流畅的用户体验
- 🔍 直观的对话预览和管理界面

## 技术栈

- 前端: Vue 3 + Vite
- UI 框架: Element Plus
- Markdown 编辑: md-editor-v3
- API 服务: FastAPI (Python)
- 数据存储: SQLite

## 快速开始

### 安装依赖

```bash
# 安装后端依赖
pip install fastapi uvicorn sqlalchemy

# 安装前端依赖
cd web
npm install
```

### 启动应用

```bash
# 启动后端服务
python main.py

# 启动前端开发服务器 (在另一个终端)
cd web
npm run dev
```

默认情况下，前端将在 http://localhost:5173 运行，后端 API 将在 http://localhost:8000 运行。

## 使用方法

### 创建新对话

1. 点击左侧面板中的"新增对话"按钮
2. 填写对话标题
3. 编辑默认生成的系统、用户和助手消息
4. 可根据需要添加更多消息
5. 点击"确认"保存对话

### 编辑对话

1. 从左侧列表中选择一个对话
2. 点击"编辑"按钮
3. 修改内容并保存

### 导出数据

- **单个导出**: 点击对话详情页面中的"导出 JSONL"按钮
- **批量导出**: 
  - 在列表中选择多个对话（使用复选框）
  - 点击"批量导出"按钮
  - 或使用顶部导航栏中的批量导出按钮导出所有对话

导出的 JSONL 文件符合大多数 AI 训练平台的数据格式要求，每行包含一个完整对话。

## 对话格式

导出的对话遵循以下 JSON 格式:

```json
{
  "title": "对话标题",
  "messages": [
    {
      "role": "system",
      "content": "系统指令内容..."
    },
    {
      "role": "user",
      "content": "用户消息内容..."
    },
    {
      "role": "assistant",
      "content": "助手回复内容..."
    }
    // 更多消息...
  ]
}
```

## 开发说明

### 目录结构

```
├── main.py           # 后端入口及 API 实现
├── conversations.db  # SQLite 数据库
└── web/              # 前端项目
    ├── src/          # 源代码
    │   ├── components/  # Vue 组件
    │   ├── App.vue      # 主应用组件
    │   └── main.js      # 入口文件
    ├── package.json     # 依赖配置
    └── vite.config.js   # Vite 配置
```

### API 端点

- `GET /conversations` - 获取所有对话列表
- `GET /conversations/{id}` - 获取特定对话详情
- `POST /conversations` - 创建新对话
- `PUT /conversations/{id}` - 更新对话
- `DELETE /conversations/{id}` - 删除对话
- `GET /conversations/{id}/export` - 导出对话为 JSONL 格式

## 贡献与反馈

欢迎通过 Issues 和 Pull Requests 提供反馈和贡献。

## 许可

MIT
