import warnings
warnings.filterwarnings("ignore", message="resource_tracker: There appear to be.*")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

from config import config
from rag_system import RAGSystem

# 初始化 FastAPI 应用
app = FastAPI(title="Course Materials RAG System", root_path="")

# 为代理添加可信主机中间件
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# 为代理启用带有正确设置的 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 初始化 RAG 系统
rag_system = RAGSystem(config)

# 用于请求/响应的 Pydantic 模型
class QueryRequest(BaseModel):
    """课程查询请求模型"""
    query: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    """课程查询响应模型"""
    answer: str
    sources: List[str]
    session_id: str

class CourseStats(BaseModel):
    """课程统计响应模型"""
    total_courses: int
    course_titles: List[str]

# API 端点

@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """处理查询并返回带有来源的响应"""
    try:
        # 如果未提供则创建会话
        session_id = request.session_id
        if not session_id:
            session_id = rag_system.session_manager.create_session()
        
        # 使用 RAG 系统处理查询
        answer, sources = rag_system.query(request.query, session_id)
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/courses", response_model=CourseStats)
async def get_course_stats():
    """获取课程分析和统计信息"""
    try:
        analytics = rag_system.get_course_analytics()
        return CourseStats(
            total_courses=analytics["total_courses"],
            course_titles=analytics["course_titles"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """启动时加载初始文档"""
    docs_path = "../docs"
    if os.path.exists(docs_path):
        print("Loading initial documents...")
        try:
            courses, chunks = rag_system.add_course_folder(docs_path, clear_existing=False)
            print(f"Loaded {courses} courses with {chunks} chunks")
        except Exception as e:
            print(f"Error loading documents: {e}")

# 为开发环境定制的静态文件处理器，带有无缓存头
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path


class DevStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if isinstance(response, FileResponse):
            # 为开发环境添加无缓存头
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response
    
    
# 为前端提供静态文件服务
app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")