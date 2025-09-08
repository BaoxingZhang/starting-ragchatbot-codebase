from typing import Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod
from vector_store import VectorStore, SearchResults


class Tool(ABC):
    """所有工具的抽象基类"""
    
    @abstractmethod
    def get_tool_definition(self) -> Dict[str, Any]:
        """返回此工具的Anthropic工具定义"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """使用给定参数执行工具"""
        pass


class CourseSearchTool(Tool):
    """用于搜索课程内容和语义课程名称匹配的工具"""
    
    def __init__(self, vector_store: VectorStore):
        self.store = vector_store
        self.last_sources = []  # 跟踪上次搜索的源
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """返回此工具的Anthropic工具定义"""
        return {
            "name": "search_course_content",
            "description": "Search course materials with smart course name matching and lesson filtering",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string", 
                        "description": "What to search for in the course content"
                    },
                    "course_name": {
                        "type": "string",
                        "description": "Course title (partial matches work, e.g. 'MCP', 'Introduction')"
                    },
                    "lesson_number": {
                        "type": "integer",
                        "description": "Specific lesson number to search within (e.g. 1, 2, 3)"
                    }
                },
                "required": ["query"]
            }
        }
    
    def execute(self, query: str, course_name: Optional[str] = None, lesson_number: Optional[int] = None) -> str:
        """
        使用给定参数执行搜索工具。
        
        Args:
            query: 要搜索的内容
            course_name: 可选课程过滤器
            lesson_number: 可选课程过滤器
            
        Returns:
            格式化的搜索结果或错误消息
        """
        
        # 使用向量存储的统一搜索接口
        results = self.store.search(
            query=query,
            course_name=course_name,
            lesson_number=lesson_number
        )
        
        # 处理错误
        if results.error:
            return results.error
        
        # 处理空结果
        if results.is_empty():
            filter_info = ""
            if course_name:
                filter_info += f" in course '{course_name}'"
            if lesson_number:
                filter_info += f" in lesson {lesson_number}"
            return f"No relevant content found{filter_info}."
        
        # 格式化并返回结果
        return self._format_results(results)
    
    def _format_results(self, results: SearchResults) -> str:
        """使用课程和课程上下文格式化搜索结果"""
        formatted = []
        sources = []  # 为UI跟踪源
        
        for doc, meta in zip(results.documents, results.metadata):
            course_title = meta.get('course_title', 'unknown')
            lesson_num = meta.get('lesson_number')
            
            # 构建上下文标头
            header = f"[{course_title}"
            if lesson_num is not None:
                header += f" - Lesson {lesson_num}"
            header += "]"
            
            # 为UI跟踪源，如果可用则带有可点击链接
            source_text = course_title
            if lesson_num is not None:
                source_text += f" - Lesson {lesson_num}"
                
            # 尝试获取课程链接以作为可点击源
            if lesson_num is not None:
                lesson_link = self.store.get_lesson_link(course_title, lesson_num)
                if lesson_link:
                    # 创建在新选项卡中打开的HTML锚点标签
                    source = f'<a href="{lesson_link}" target="_blank">{source_text}</a>'
                else:
                    source = source_text
            else:
                source = source_text
                
            sources.append(source)
            
            formatted.append(f"{header}\n{doc}")
        
        # 存储源以供检索
        self.last_sources = sources
        
        return "\n\n".join(formatted)

class ToolManager:
    """管理AI的可用工具"""
    
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, tool: Tool):
        """注册实现Tool接口的任何工具"""
        tool_def = tool.get_tool_definition()
        tool_name = tool_def.get("name")
        if not tool_name:
            raise ValueError("Tool must have a 'name' in its definition")
        self.tools[tool_name] = tool

    
    def get_tool_definitions(self) -> list:
        """获取所有用于Anthropic工具调用的工具定义"""
        return [tool.get_tool_definition() for tool in self.tools.values()]
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """按名称使用给定参数执行工具"""
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' not found"
        
        return self.tools[tool_name].execute(**kwargs)
    
    def get_last_sources(self) -> list:
        """从上一次搜索操作获取源"""
        # 检查所有工具的last_sources属性
        for tool in self.tools.values():
            if hasattr(tool, 'last_sources') and tool.last_sources:
                return tool.last_sources
        return []

    def reset_sources(self):
        """从所有跟踪源的工具中重置源"""
        for tool in self.tools.values():
            if hasattr(tool, 'last_sources'):
                tool.last_sources = []