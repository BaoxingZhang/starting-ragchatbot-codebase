import os
from dataclasses import dataclass
from dotenv import load_dotenv

# 从 .env 文件加载环境变量
load_dotenv()

@dataclass
class Config:
    """RAG 系统的配置设置"""
    # OpenAI API 设置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # 嵌入模型设置
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # 文档处理设置
    CHUNK_SIZE: int = 800       # 用于向量存储的文本块大小
    CHUNK_OVERLAP: int = 100     # 块之间重叠的字符数
    MAX_RESULTS: int = 50        # 返回的最大搜索结果数
    MAX_HISTORY: int = 2         # 要记住的对话消息数量
    
    # 数据库路径
    CHROMA_PATH: str = "./chroma_db"  # ChromaDB 存储位置

config = Config()


