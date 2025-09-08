// API 基础 URL - 使用相对路径以便从任何主机工作
const API_URL = '/api';

// 全局状态
let currentSessionId = null;

// DOM 元素
let chatMessages, chatInput, sendButton, totalCourses, courseTitles;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 页面加载后获取 DOM 元素
    chatMessages = document.getElementById('chatMessages');
    chatInput = document.getElementById('chatInput');
    sendButton = document.getElementById('sendButton');
    totalCourses = document.getElementById('totalCourses');
    courseTitles = document.getElementById('courseTitles');
    
    setupEventListeners();
    createNewSession();
    loadCourseStats();
});

// 事件监听器
function setupEventListeners() {
    // 聊天功能
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    
    // 建议问题
    document.querySelectorAll('.suggested-item').forEach(button => {
        button.addEventListener('click', (e) => {
            const question = e.target.getAttribute('data-question');
            chatInput.value = question;
            sendMessage();
        });
    });
}


// 聊天功能
async function sendMessage() {
    const query = chatInput.value.trim();
    if (!query) return;

    // 禁用输入
    chatInput.value = '';
    chatInput.disabled = true;
    sendButton.disabled = true;

    // 添加用户消息
    addMessage(query, 'user');

    // 添加加载消息 - 为其创建唯一容器
    const loadingMessage = createLoadingMessage();
    chatMessages.appendChild(loadingMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                session_id: currentSessionId
            })
        });

        if (!response.ok) throw new Error('查询失败');

        const data = await response.json();
        
        // 如果是新会话则更新会话 ID
        if (!currentSessionId) {
            currentSessionId = data.session_id;
        }

        // 用响应替换加载消息
        loadingMessage.remove();
        addMessage(data.answer, 'assistant', data.sources);

    } catch (error) {
        // 用错误信息替换加载消息
        loadingMessage.remove();
        addMessage(`错误：${error.message}`, 'assistant');
    } finally {
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();
    }
}

function createLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="loading">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    return messageDiv;
}

function addMessage(content, type, sources = null, isWelcome = false) {
    const messageId = Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}${isWelcome ? ' welcome-message' : ''}`;
    messageDiv.id = `message-${messageId}`;
    
    // 为助手消息将 markdown 转换为 HTML
    const displayContent = type === 'assistant' ? marked.parse(content) : escapeHtml(content);
    
    let html = `<div class="message-content">${displayContent}</div>`;
    
    if (sources && sources.length > 0) {
        // 用分隔符连接来源，允许 HTML 内容渲染
        const sourcesHtml = sources.map(source => `<span class="source-item">${source}</span>`).join('<span class="source-separator">, </span>');
        html += `
            <details class="sources-collapsible">
                <summary class="sources-header">来源</summary>
                <div class="sources-content">${sourcesHtml}</div>
            </details>
        `;
    }
    
    messageDiv.innerHTML = html;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageId;
}

// 为用户消息转义 HTML 的辅助函数
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 已删除 removeMessage 函数 - 由于我们以不同方式处理加载，不再需要

async function createNewSession() {
    currentSessionId = null;
    chatMessages.innerHTML = '';
    addMessage('欢迎使用课程资料智能助手！我可以帮助您回答关于课程、课时和具体内容的问题。您想了解什么？', 'assistant', null, true);
}

// 加载课程统计信息
async function loadCourseStats() {
    try {
        console.log('Loading course stats...');
        const response = await fetch(`${API_URL}/courses`);
        if (!response.ok) throw new Error('加载课程统计失败');
        
        const data = await response.json();
        console.log('Course data received:', data);
        
        // 在 UI 中更新统计信息
        if (totalCourses) {
            totalCourses.textContent = data.total_courses;
        }
        
        // 更新课程标题
        if (courseTitles) {
            if (data.course_titles && data.course_titles.length > 0) {
                courseTitles.innerHTML = data.course_titles
                    .map(title => `<div class="course-title-item">${title}</div>`)
                    .join('');
            } else {
                courseTitles.innerHTML = '<span class="no-courses">暂无可用课程</span>';
            }
        }
        
    } catch (error) {
        console.error('Error loading course stats:', error);
        // 出错时设置默认值
        if (totalCourses) {
            totalCourses.textContent = '0';
        }
        if (courseTitles) {
            courseTitles.innerHTML = '<span class="error">加载课程失败</span>';
        }
    }
}