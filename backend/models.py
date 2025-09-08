from typing import List, Dict, Optional
from pydantic import BaseModel

class Lesson(BaseModel):
    """表示课程中的一课"""
    lesson_number: int  # 顺序课程编号（1, 2, 3等）
    title: str         # 课程标题
    lesson_link: Optional[str] = None  # 课程的URL链接

class Course(BaseModel):
    """表示包含课程的完整课程"""
    title: str                 # 完整课程标题（用作唯一标识符）
    course_link: Optional[str] = None  # 课程的URL链接
    instructor: Optional[str] = None  # 课程讲师姓名（可选元数据）
    lessons: List[Lesson] = [] # 此课程中的课程列表

class CourseChunk(BaseModel):
    """表示用于向量存储的课程文本分块"""
    content: str                        # 实际文本内容
    course_title: str                   # 此分块属于哪个课程
    lesson_number: Optional[int] = None # 此分块来自哪一课
    chunk_index: int                    # 此分块在文档中的位置