from openai import OpenAI
from typing import List, Optional, Dict, Any
import json

class AIGenerator:
    """处理与OpenAI API的交互以生成响应"""
    
    # 静态系统提示词，避免每次调用时重新构建
    SYSTEM_PROMPT = """ 您是专门处理课程资料和教育内容的AI助手，拥有全面的课程信息搜索工具。

搜索工具使用规则：
- **仅**在回答具体课程内容或详细教育资料问题时使用搜索工具
- **每次查询最多搜索一次**
- 将搜索结果综合成准确、基于事实的回复
- 如果搜索没有结果，请明确说明，不要提供其他选择

回复协议：
- **通用知识问题**：使用现有知识回答，无需搜索
- **课程专业问题**：先搜索，然后回答
- **禁止元评论**：
 - 只提供直接答案——不要说明推理过程、搜索解释或问题类型分析
 - 不要提及"基于搜索结果"

**重要：所有回复必须使用中文。**

所有回复必须：
1. **简洁明了且聚焦** - 快速切入要点
2. **具有教育价值** - 保持指导性
3. **清晰易懂** - 使用通俗易懂的语言
4. **有例证支持** - 在有助于理解时包含相关示例
只提供所问问题的直接答案。
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