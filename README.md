# 课程资料 RAG 系统

基于检索增强生成（RAG）技术的课程资料问答系统，使用语义搜索和 AI 生成技术来回答课程相关问题。

## 项目概述

这是一个全栈 Web 应用程序，用户可以查询课程资料并获得智能的、上下文感知的回答。系统使用 ChromaDB 进行向量存储，使用兼容 OpenAI 的 API 进行 AI 生成，并提供 Web 界面进行交互。

## 系统要求

- Python 3.13 或更高版本
- uv（Python 包管理器）
- OpenAI API 密钥或兼容的 API 端点
- **Windows 用户**: 建议使用 Git Bash 运行应用命令 - [下载 Git for Windows](https://git-scm.com/downloads/win)

## 安装步骤

1. **安装 uv**（如果尚未安装）
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **安装 Python 依赖**
   ```bash
   uv sync
   ```

3. **设置环境变量**
   
   在根目录创建 `.env` 文件：
   ```bash
   OPENAI_API_KEY=你的openai_api_key
   OPENAI_BASE_URL=https://api.openai.com/v1  # 可选：自定义 API 端点
   OPENAI_MODEL=gpt-4  # 可选：指定使用的模型
   ```

## 运行应用程序

### 快速启动

使用提供的启动脚本：
```bash
chmod +x run.sh
./run.sh
```

### 手动启动

```bash
cd backend
uv run uvicorn app:app --reload --port 8000
```

应用程序将在以下地址可用：
- Web 界面：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`

## 功能特性

- 📚 智能课程资料问答
- 🔍 语义搜索与向量检索
- 💬 对话上下文管理
- 🌐 响应式 Web 界面
- 🔧 可配置 OpenAI 兼容 API
- 📝 自动文档处理和分块

## 技术架构

### 后端技术栈
- **FastAPI**: Web 框架和 API 服务
- **ChromaDB**: 向量数据库
- **sentence-transformers**: 文本嵌入模型
- **OpenAI API**: AI 生成服务

### 前端技术栈
- **原生 JavaScript**: 单页应用
- **CSS Grid/Flexbox**: 响应式布局
- **异步 API 调用**: 现代 Web 技术

## 项目结构

```
├── backend/              # 后端代码
│   ├── app.py           # FastAPI 应用入口
│   ├── rag_system.py    # RAG 系统协调器
│   ├── ai_generator.py  # AI 生成集成
│   └── ...              # 其他模块
├── frontend/            # 前端资源
│   ├── index.html       # 主页面
│   ├── script.js        # JavaScript 代码
│   └── style.css        # 样式文件
├── docs/                # 课程文档存放目录
└── .env                 # 环境配置文件
```

## 使用说明

1. 将课程资料放入 `docs/` 目录
2. 启动应用程序
3. 在 Web 界面中输入问题
4. 系统将基于课程资料生成答案

## 配置选项

可以通过修改 `backend/config.py` 调整以下参数：
- 文档分块大小
- 搜索结果数量
- 对话历史长度
- 嵌入模型选择

## 故障排除

如果遇到问题，请检查：
- Python 版本是否符合要求
- 环境变量是否正确设置
- API 密钥是否有效
- 网络连接是否正常

## 许可证

此项目仅供学习和研究使用。