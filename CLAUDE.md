# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此存储库中工作时提供指导。

## 用户偏好设置

**重要：用户的母语是中文，请始终使用中文与用户交流和回复。**

## 开发命令

### 安装和配置
```bash
# 安装依赖
uv sync

# 设置环境变量（复制 .env.example 到 .env 并配置 OpenAI 设置）
cp .env.example .env
```

### 运行应用程序
```bash
# 快速启动（推荐）
chmod +x run.sh
./run.sh

# 手动启动
cd backend && uv run uvicorn app:app --reload --port 8000
```

### 开发调试
```bash
# 使用热重载运行后端
cd backend && uv run uvicorn app:app --reload --port 8000

# 访问应用程序
# Web 界面: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

## 架构概述

这是一个基于检索增强生成（RAG）的课程资料系统，构建技术栈：

### 后端架构
- **FastAPI** 应用程序，同时提供 API 和静态前端服务
- **ChromaDB** 向量存储，使用 sentence-transformers 嵌入模型
- **OpenAI API** 用于 AI 生成（可配置模型和基础 URL）
- **模块化架构** 清晰分离关注点：

#### 核心组件 (backend/)
- `app.py` - FastAPI 应用程序、CORS 设置和 API 端点
- `rag_system.py` - 主要协调器，协调所有组件
- `vector_store.py` - ChromaDB 包装器，带有 SearchResults 抽象
- `document_processor.py` - 文本分块和课程文档解析
- `ai_generator.py` - OpenAI API 集成，可配置基础 URL
- `session_manager.py` - 对话历史管理
- `search_tools.py` - 增强搜索能力的工具系统
- `models.py` - Pydantic 模型（Course, Lesson, CourseChunk）
- `config.py` - 环境变量配置管理

#### 数据模型
- **Course**: 表示包含课程的完整课程
- **Lesson**: 课程内的单个课程
- **CourseChunk**: 用于向量存储的文本块，带有元数据

### 前端架构
- **原生 JavaScript** SPA，使用 async/await API 调用
- **CSS Grid/Flexbox** 响应式设计
- **基于会话** 的对话管理
- 文件：`index.html`, `script.js`, `style.css`

### 关键架构模式
- **基于组件的后端** 通过 RAGSystem 进行依赖注入
- **工具系统** 可扩展的搜索能力
- **会话管理** 对话上下文管理
- **向量 + 元数据搜索** 结合语义和结构化查询
- **分块文档处理** 可配置大小/重叠

## 配置

`.env` 中的环境变量：
- `OPENAI_API_KEY` - OpenAI API 访问所需
- `OPENAI_BASE_URL` - API 基础 URL（默认：https://api.openai.com/v1，可自定义为其他 OpenAI 兼容 API）
- `OPENAI_MODEL` - 要使用的模型（默认：gpt-4，可以是 gpt-3.5-turbo、gpt-4 等）

`backend/config.py` 中的配置常量：
- `CHUNK_SIZE`: 每个块 800 字符
- `CHUNK_OVERLAP`: 块之间 100 字符重叠
- `MAX_RESULTS`: 返回 5 个搜索结果
- `MAX_HISTORY`: 记住 2 条对话消息
- `EMBEDDING_MODEL`: "all-MiniLM-L6-v2" (sentence-transformers)
- `OPENAI_MODEL`: "gpt-4"（通过环境变量可配置）

## 数据流程

1. 放置在 `docs/` 中的文档在启动时加载
2. `DocumentProcessor` 将文档分块为 `CourseChunk` 对象
3. `VectorStore` 在 ChromaDB 中存储嵌入和元数据
4. 用户查询通过 `search_tools.py` 触发语义搜索
5. 检索的块为 OpenAI API 生成提供上下文
6. `SessionManager` 维护对话历史
7. 前端显示带有来源归属的结果

## 开发注意事项

- **热重载**: 后端在开发时使用 `--reload` 标志运行
- **CORS 已启用**: 前端可以从任何主机运行
- **静态文件**: 前端直接由 FastAPI 提供服务
- **无缓存头**: 开发静态文件服务防止缓存
- **文档加载**: 从 `../docs` 文件夹自动启动加载
- **错误处理**: 具有正确状态码的 HTTP 异常

## 数据库

- **ChromaDB**: `./chroma_db/` 中的持久向量数据库
- **集合**: 课程元数据和内容块的独立存储
- **嵌入**: 使用 sentence-transformers 模型生成
- **元数据搜索**: 与向量相似度结合以增强结果

# 重要指令提醒
按要求执行任务；不多不少。
除非绝对必要实现您的目标，否则永远不要创建文件。
始终优先编辑现有文件而不是创建新文件。
永远不要主动创建文档文件（*.md）或 README 文件。只有在用户明确请求时才创建文档文件。