from openai import OpenAI
from typing import List, Optional, Dict, Any
import json

class AIGenerator:
    """处理与OpenAI API的交互以生成响应"""
    
    # 静态系统提示词，避免每次调用时重新构建
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to a comprehensive search tool for course information.

Search Tool Usage:
- Use the search tool **only** for questions about specific course content or detailed educational materials
- **One search per query maximum**
- Synthesize search results into accurate, fact-based responses
- If search yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Search first, then answer
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, search explanations, or question-type analysis
 - Do not mention "based on the search results"


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        
        # 预构建基础API参数
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        生成AI响应，支持可选的工具使用和对话上下文。
        
        Args:
            query: 用户的问题或请求
            conversation_history: 用于上下文的历史消息
            tools: AI可以使用的可用工具
            tool_manager: 执行工具的管理器
            
        Returns:
            生成的响应字符串
        """
        
        # 构建包含系统消息的消息列表
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        
        # 如果有可用的对话历史，则添加
        if conversation_history:
            messages.append({"role": "system", "content": f"Previous conversation:\n{conversation_history}"})
        
        # 添加用户查询
        messages.append({"role": "user", "content": query})
        
        # 准备API调用参数
        api_params = {
            **self.base_params,
            "messages": messages
        }
        
        # 如果有可用工具则添加
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = "auto"
        
        # 从OpenAI获取响应
        response = self.client.chat.completions.create(**api_params)
        
        # 如果需要则处理工具执行
        if response.choices[0].message.tool_calls and tool_manager:
            return self._handle_tool_execution(response, api_params, tool_manager)
        
        # 返回直接响应
        return response.choices[0].message.content
    
    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        处理工具调用的执行并获取后续响应。
        
        Args:
            initial_response: 包含工具使用请求的响应
            base_params: 基础API参数
            tool_manager: 执行工具的管理器
            
        Returns:
            工具执行后的最终响应文本
        """
        # 从现有消息开始
        messages = base_params["messages"].copy()
        
        # 添加AI的工具使用响应
        messages.append({
            "role": "assistant",
            "content": initial_response.choices[0].message.content,
            "tool_calls": initial_response.choices[0].message.tool_calls
        })
        
        # 执行所有工具调用并收集结果
        for tool_call in initial_response.choices[0].message.tool_calls:
            # 解析工具参数
            tool_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
            
            # 执行工具
            tool_result = tool_manager.execute_tool(
                tool_call.function.name,
                **tool_args
            )
            
            # 将工具结果添加到消息中
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(tool_result)
            })
        
        # 准备不包含工具的最终API调用
        final_params = {
            **self.base_params,
            "messages": messages
        }
        
        # 获取最终响应
        final_response = self.client.chat.completions.create(**final_params)
        return final_response.choices[0].message.content