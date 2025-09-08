import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from models import Course, CourseChunk
from sentence_transformers import SentenceTransformer

@dataclass
class SearchResults:
    """带有元数据的搜索结果容器"""
    documents: List[str]
    metadata: List[Dict[str, Any]]
    distances: List[float]
    error: Optional[str] = None
    
    @classmethod
    def from_chroma(cls, chroma_results: Dict) -> 'SearchResults':
        """从ChromaDB查询结果创建SearchResults"""
        return cls(
            documents=chroma_results['documents'][0] if chroma_results['documents'] else [],
            metadata=chroma_results['metadatas'][0] if chroma_results['metadatas'] else [],
            distances=chroma_results['distances'][0] if chroma_results['distances'] else []
        )
    
    @classmethod
    def empty(cls, error_msg: str) -> 'SearchResults':
        """创建带有错误消息的空结果"""
        return cls(documents=[], metadata=[], distances=[], error=error_msg)
    
    def is_empty(self) -> bool:
        """检查结果是否为空"""
        return len(self.documents) == 0

class VectorStore:
    """使用ChromaDB进行课程内容和元数据的向量存储"""
    
    def __init__(self, chroma_path: str, embedding_model: str, max_results: int = 5):
        self.max_results = max_results
        # 初始化ChromaDB客户端
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 设置句子变换器嵌入函数
        self.embedding_function = chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        
        # 为不同类型的数据创建集合
        self.course_catalog = self._create_collection("course_catalog")  # 课程标题/讲师
        self.course_content = self._create_collection("course_content")  # 实际课程材料
    
    def _create_collection(self, name: str):
        """创建或获取ChromaDB集合"""
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_function
        )
    
    def search(self, 
               query: str,
               course_name: Optional[str] = None,
               lesson_number: Optional[int] = None,
               limit: Optional[int] = None) -> SearchResults:
        """
        处理课程解析和内容搜索的主搜索接口。
        
        Args:
            query: 在课程内容中要搜索的内容
            course_name: 要过滤的可选课程名称/标题
            lesson_number: 要过滤的可选课程编号
            limit: 返回的最大结果数
            
        Returns:
            带有文档和元数据的SearchResults对象
        """
        # 第1步：如果提供了课程名称则解析
        course_title = None
        if course_name:
            course_title = self._resolve_course_name(course_name)
            if not course_title:
                return SearchResults.empty(f"No course found matching '{course_name}'")
        
        # 第2步：为内容搜索构建过滤器
        filter_dict = self._build_filter(course_title, lesson_number)
        
        # 第3步：搜索课程内容
        # 使用提供的限制或回退到配置的最大结果
        search_limit = limit if limit is not None else self.max_results
        
        try:
            results = self.course_content.query(
                query_texts=[query],
                n_results=search_limit,
                where=filter_dict
            )
            return SearchResults.from_chroma(results)
        except Exception as e:
            return SearchResults.empty(f"Search error: {str(e)}")
    
    def _resolve_course_name(self, course_name: str) -> Optional[str]:
        """使用向量搜索按名称查找最佳匹配课程"""
        try:
            results = self.course_catalog.query(
                query_texts=[course_name],
                n_results=1
            )
            
            if results['documents'][0] and results['metadatas'][0]:
                # 返回标题（现在是ID）
                return results['metadatas'][0][0]['title']
        except Exception as e:
            print(f"Error resolving course name: {e}")
        
        return None
    
    def _build_filter(self, course_title: Optional[str], lesson_number: Optional[int]) -> Optional[Dict]:
        """从搜索参数构建ChromaDB过滤器"""
        if not course_title and lesson_number is None:
            return None
            
        # 处理不同的过滤器组合
        if course_title and lesson_number is not None:
            return {"$and": [
                {"course_title": course_title},
                {"lesson_number": lesson_number}
            ]}
        
        if course_title:
            return {"course_title": course_title}
            
        return {"lesson_number": lesson_number}
    
    def add_course_metadata(self, course: Course):
        """将课程信息添加到目录中以进行语义搜索"""
        import json

        course_text = course.title
        
        # 构建课程元数据并序列化为JSON字符串
        lessons_metadata = []
        for lesson in course.lessons:
            lessons_metadata.append({
                "lesson_number": lesson.lesson_number,
                "lesson_title": lesson.title,
                "lesson_link": lesson.lesson_link
            })
        
        metadata = {
            "title": course.title if course.title is not None else "",
            "lessons_json": json.dumps(lessons_metadata),  # 序列化为JSON字符串
            "lesson_count": len(course.lessons)
        }
        
        # 只有当值不为None时才添加可选字段
        if course.instructor is not None:
            metadata["instructor"] = course.instructor
        if course.course_link is not None:
            metadata["course_link"] = course.course_link
            
        self.course_catalog.add(
            documents=[course_text],
            metadatas=[metadata],
            ids=[course.title]
        )
    
    def add_course_content(self, chunks: List[CourseChunk]):
        """将课程内容分块添加到向量存储中"""
        if not chunks:
            return
        
        documents = [chunk.content for chunk in chunks]
        metadatas = []
        for chunk in chunks:
            metadata = {
                "course_title": chunk.course_title if chunk.course_title is not None else "",
                "chunk_index": chunk.chunk_index if chunk.chunk_index is not None else 0
            }
            # 只有当lesson_number不为None时才添加
            if chunk.lesson_number is not None:
                metadata["lesson_number"] = chunk.lesson_number
            
            metadatas.append(metadata)
        
        # 使用标题和分块索引作为唯一ID
        ids = [f"{chunk.course_title.replace(' ', '_') if chunk.course_title else 'unknown'}_{chunk.chunk_index}" for chunk in chunks]
        
        self.course_content.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def clear_all_data(self):
        """清除两个集合中的所有数据"""
        try:
            self.client.delete_collection("course_catalog")
            self.client.delete_collection("course_content")
            # 重新创建集合
            self.course_catalog = self._create_collection("course_catalog")
            self.course_content = self._create_collection("course_content")
        except Exception as e:
            print(f"Error clearing data: {e}")
    
    def get_existing_course_titles(self) -> List[str]:
        """从向量存储中获取所有现有课程标题"""
        try:
            # 从目录中获取所有文档
            results = self.course_catalog.get()
            if results and 'ids' in results:
                return results['ids']
            return []
        except Exception as e:
            print(f"Error getting existing course titles: {e}")
            return []
    
    def get_course_count(self) -> int:
        """获取向量存储中课程的总数"""
        try:
            results = self.course_catalog.get()
            if results and 'ids' in results:
                return len(results['ids'])
            return 0
        except Exception as e:
            print(f"Error getting course count: {e}")
            return 0
    
    def get_all_courses_metadata(self) -> List[Dict[str, Any]]:
        """获取向量存储中所有课程的元数据"""
        import json
        try:
            results = self.course_catalog.get()
            if results and 'metadatas' in results:
                # 为每个课程解析课程JSON
                parsed_metadata = []
                for metadata in results['metadatas']:
                    course_meta = metadata.copy()
                    if 'lessons_json' in course_meta:
                        course_meta['lessons'] = json.loads(course_meta['lessons_json'])
                        del course_meta['lessons_json']  # 删除JSON字符串版本
                    parsed_metadata.append(course_meta)
                return parsed_metadata
            return []
        except Exception as e:
            print(f"Error getting courses metadata: {e}")
            return []

    def get_course_link(self, course_title: str) -> Optional[str]:
        """获取给定课程标题的课程链接"""
        try:
            # 通过ID获取课程（标题是ID）
            results = self.course_catalog.get(ids=[course_title])
            if results and 'metadatas' in results and results['metadatas']:
                metadata = results['metadatas'][0]
                return metadata.get('course_link')
            return None
        except Exception as e:
            print(f"Error getting course link: {e}")
            return None
    
    def get_lesson_link(self, course_title: str, lesson_number: int) -> Optional[str]:
        """获取给定课程标题和课程编号的课程链接"""
        import json
        try:
            # 通过ID获取课程（标题是ID）
            results = self.course_catalog.get(ids=[course_title])
            if results and 'metadatas' in results and results['metadatas']:
                metadata = results['metadatas'][0]
                lessons_json = metadata.get('lessons_json')
                if lessons_json:
                    lessons = json.loads(lessons_json)
                    # 查找匹配编号的课程
                    for lesson in lessons:
                        if lesson.get('lesson_number') == lesson_number:
                            return lesson.get('lesson_link')
            return None
        except Exception as e:
            print(f"Error getting lesson link: {e}")
    