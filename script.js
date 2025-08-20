// 全局变量
let currentChatId = null;
let chatHistory = [];
let isTyping = false;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    loadChatHistory();
    autoResizeTextarea();
    initTheme();
    startNewChat();
});

// 自动调整文本框高度
function autoResizeTextarea() {
    const textarea = document.getElementById('messageInput');
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
}

// 开始新对话
function startNewChat() {
    currentChatId = Date.now().toString();
    const chatTitle = `新对话 ${new Date().toLocaleString()}`;
    
    chatHistory.unshift({
        id: currentChatId,
        title: chatTitle,
        messages: [],
        timestamp: new Date()
    });
    
    updateChatHistoryUI();
    clearChatMessages();
    updateChatTitle(chatTitle);
    saveChatHistory();
}

// 发送消息
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    const imageInput = document.getElementById('imageInput');
    
    if (!message && !imageInput.files.length) return;
    
    const currentChat = chatHistory.find(chat => chat.id === currentChatId);
    if (!currentChat) return;
    
    const userMessage = {
        id: Date.now().toString(),
        type: 'user',
        text: message,
        timestamp: new Date(),
        images: []
    };
    
    if (imageInput.files.length > 0) {
        for (let file of imageInput.files) {
            const imageUrl = await readFileAsDataURL(file);
            userMessage.images.push(imageUrl);
        }
        imageInput.value = '';
    }
    
    currentChat.messages.push(userMessage);
    addMessageToUI(userMessage);
    
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    if (currentChat.messages.length === 1) {
        currentChat.title = message.substring(0, 30) + (message.length > 30 ? '...' : '');
        updateChatHistoryUI();
    }
    
    showTypingIndicator();
    
    setTimeout(() => {
        generateAIResponse(currentChat, userMessage);
    }, 1000);
    
    saveChatHistory();
}

// 处理图片上传
function handleImageUpload(event) {
    const files = event.target.files;
    if (files.length > 0) {
        console.log('图片已选择:', files.length, '个文件');
    }
}

// 将文件读取为Data URL
function readFileAsDataURL(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = e => resolve(e.target.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// 生成AI响应
async function generateAIResponse(chat, userMessage) {
    hideTypingIndicator();
    
    try {
        // 检查是否是股票相关的问题
        const stockKeywords = ['股票', '涨幅', '分析', '策略', '投资', '市场', '交易', '指标', '模式'];
        const isStockQuestion = stockKeywords.some(keyword => 
            userMessage.text.includes(keyword)
        );
        
        if (isStockQuestion) {
            // 调用股票策略API
            const response = await fetch('http://localhost:5001/explore', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    input: userMessage.text
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                const aiMessage = {
                    id: Date.now().toString(),
                    type: 'assistant',
                    text: formatStockResponse(result),
                    timestamp: new Date(),
                    images: [],
                    data: result // 保存原始数据用于后续展示
                };
                
                chat.messages.push(aiMessage);
                addMessageToUI(aiMessage);
                
                // 如果有可视化数据，显示图表
                if (result['k线可视化数据'] && result['k线可视化数据'].length > 0) {
                    setTimeout(() => {
                        showStockChart(result['k线可视化数据']);
                    }, 500);
                }
            } else {
                throw new Error(`API请求失败: ${response.status}`);
            }
        } else {
            // 普通对话响应
            const responses = [
                "我理解你的问题。让我来帮你分析一下...",
                "这是一个很有趣的问题！根据我的理解...",
                "我看到了你上传的图片，让我为你分析一下内容...",
                "基于你提供的信息，我的建议是...",
                "这个问题可以从几个角度来考虑..."
            ];
            
            let responseText = responses[Math.floor(Math.random() * responses.length)];
            
            if (userMessage.images.length > 0) {
                responseText = "我看到了你上传的图片！" + responseText;
            }
            
            if (userMessage.text.toLowerCase().includes('你好') || userMessage.text.toLowerCase().includes('hello')) {
                responseText = "你好！很高兴见到你。我是你的AI助手，有什么可以帮助你的吗？";
            }
            
            if (userMessage.text.toLowerCase().includes('代码') || userMessage.text.toLowerCase().includes('编程')) {
                responseText = "关于编程问题，我可以为你提供代码示例和解释。请告诉我具体需要什么帮助？";
            }
            
            const aiMessage = {
                id: Date.now().toString(),
                type: 'assistant',
                text: responseText,
                timestamp: new Date(),
                images: []
            };
            
            chat.messages.push(aiMessage);
            addMessageToUI(aiMessage);
        }
        
        saveChatHistory();
        
    } catch (error) {
        console.error('API调用失败:', error);
        
        // 显示错误消息
        const errorMessage = {
            id: Date.now().toString(),
            type: 'assistant',
            text: `抱歉，处理您的请求时遇到了问题：${error.message}。请确保股票分析服务正在运行（端口5001）。`,
            timestamp: new Date(),
            images: []
        };
        
        chat.messages.push(errorMessage);
        addMessageToUI(errorMessage);
        saveChatHistory();
    }
}

// 格式化股票分析响应
function formatStockResponse(result) {
    let response = "📊 **股票策略分析结果**\n\n";
    
    // 复合指标探索
    if (result['复合指标探索']) {
        response += `🔍 **复合指标探索**: ${result['复合指标探索']}\n\n`;
    }
    
    // 推荐指标
    if (result['推荐指标'] && result['推荐指标'].length > 0) {
        response += "📈 **推荐指标**:\n";
        result['推荐指标'].forEach((item, index) => {
            response += `${index + 1}. ${item}\n`;
        });
        response += "\n";
    }
    
    // 标签解释
    const tagExplanations = [];
    Object.keys(result).forEach(key => {
        if (key !== 'k线可视化数据' && key !== '复合指标探索' && key !== '推荐指标') {
            tagExplanations.push(`**${key}**: ${result[key]}`);
        }
    });
    
    if (tagExplanations.length > 0) {
        response += "🏷️ **指标解释**:\n";
        tagExplanations.forEach(explanation => {
            response += `• ${explanation}\n`;
        });
        response += "\n";
    }
    
    // 数据统计
    if (result['k线可视化数据'] && result['k线可视化数据'].length > 0) {
        response += `📊 **分析数据**: 共分析了 ${result['k线可视化数据'].length} 条记录\n`;
        response += "💡 提示：点击下方按钮查看详细图表分析";
    }
    
    return response;
}

// 显示股票图表
function showStockChart(data) {
    // 创建图表容器
    const chartContainer = document.createElement('div');
    chartContainer.className = 'stock-chart-container';
    chartContainer.innerHTML = `
        <div class="chart-header">
            <h4>📊 股票策略可视化分析</h4>
            <button class="close-chart-btn" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="chart-content">
            <div class="data-table">
                <table>
                    <thead>
                        <tr>
                            <th>日期</th>
                            <th>目标值</th>
                            <th>AI探索</th>
                            <th>主要指标</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.slice(0, 10).map(item => `
                            <tr>
                                <td>${item.date || 'N/A'}</td>
                                <td>${item.target || 'N/A'}</td>
                                <td>${item.AI_explore || 'N/A'}</td>
                                <td>${Object.keys(item).filter(key => 
                                    key !== 'date' && key !== 'target' && key !== 'AI_explore'
                                ).slice(0, 3).join(', ')}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div class="chart-summary">
                <p>📈 数据概览：共 ${data.length} 条记录</p>
                <p>🎯 分析目标：识别股票涨幅模式</p>
            </div>
        </div>
    `;
    
    // 添加到聊天区域
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.appendChild(chartContainer);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 添加消息到UI
function addMessageToUI(message) {
    const chatMessages = document.getElementById('chatMessages');
    
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.type}`;
    messageDiv.id = `message-${message.id}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = message.type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    if (message.text) {
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = message.text;
        content.appendChild(textDiv);
    }
    
    if (message.images && message.images.length > 0) {
        message.images.forEach(imageUrl => {
            const img = document.createElement('img');
            img.src = imageUrl;
            img.className = 'message-image';
            img.alt = '上传的图片';
            content.appendChild(img);
        });
    }
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = message.timestamp.toLocaleTimeString();
    content.appendChild(timeDiv);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 显示打字指示器
function showTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    indicator.style.display = 'flex';
    isTyping = true;
    
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 隐藏打字指示器
function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    indicator.style.display = 'none';
    isTyping = false;
}

// 清空聊天消息
function clearChatMessages() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">
                <i class="fas fa-robot"></i>
            </div>
            <h3>欢迎使用AI助手</h3>
            <p>我可以帮助你回答问题、分析图片、编写代码等。请开始你的对话吧！</p>
        </div>
    `;
}

// 更新聊天历史UI
function updateChatHistoryUI() {
    const chatHistoryDiv = document.getElementById('chatHistory');
    chatHistoryDiv.innerHTML = '';
    
    chatHistory.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.className = `chat-item ${chat.id === currentChatId ? 'active' : ''}`;
        chatItem.onclick = () => loadChat(chat.id);
        
        const title = document.createElement('div');
        title.className = 'chat-item-title';
        title.textContent = chat.title;
        
        const preview = document.createElement('div');
        preview.className = 'chat-item-preview';
        preview.textContent = chat.messages.length > 0 
            ? chat.messages[chat.messages.length - 1].text.substring(0, 50) + '...'
            : '新对话';
        
        chatItem.appendChild(title);
        chatItem.appendChild(preview);
        chatHistoryDiv.appendChild(chatItem);
    });
}

// 加载聊天
function loadChat(chatId) {
    currentChatId = chatId;
    const chat = chatHistory.find(c => c.id === chatId);
    if (!chat) return;
    
    clearChatMessages();
    
    chat.messages.forEach(message => {
        addMessageToUI(message);
    });
    
    updateChatHistoryUI();
    updateChatTitle(chat.title);
}

// 处理键盘事件
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// 保存聊天历史到本地存储
function saveChatHistory() {
    localStorage.setItem('aiChatHistory', JSON.stringify(chatHistory));
}

// 从本地存储加载聊天历史
function loadChatHistory() {
    const saved = localStorage.getItem('aiChatHistory');
    if (saved) {
        chatHistory = JSON.parse(saved);
        chatHistory.forEach(chat => {
            chat.timestamp = new Date(chat.timestamp);
            chat.messages.forEach(message => {
                message.timestamp = new Date(message.timestamp);
            });
        });
    }
}

// 导出聊天记录
function exportChat() {
    const currentChat = chatHistory.find(chat => chat.id === currentChatId);
    if (!currentChat || currentChat.messages.length === 0) {
        showNotification('提示', '没有可导出的聊天记录', 'info');
        return;
    }
    
    const chatData = {
        title: currentChat.title,
        messages: currentChat.messages,
        exportTime: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-${currentChat.title}-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    showNotification('成功', '聊天记录已导出', 'success');
}

// 清空所有聊天记录
function clearAllChats() {
    if (confirm('确定要清空所有聊天记录吗？此操作不可恢复。')) {
        chatHistory = [];
        localStorage.removeItem('aiChatHistory');
        startNewChat();
        showNotification('成功', '所有聊天记录已清空', 'success');
    }
}

// 切换主题
function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const icon = document.querySelector('.action-btn[onclick="toggleTheme()"] i');
    icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    
    showNotification('主题切换', `已切换到${newTheme === 'dark' ? '深色' : '浅色'}主题`, 'info');
}

// 切换侧边栏
function toggleSidebar() {
    const container = document.querySelector('.container');
    container.classList.toggle('sidebar-hidden');
    
    const icon = document.querySelector('.header-btn[onclick="toggleSidebar()"] i');
    if (container.classList.contains('sidebar-hidden')) {
        icon.className = 'fas fa-chevron-right';
    } else {
        icon.className = 'fas fa-bars';
    }
}

// 全屏模式
function fullscreen() {
    const container = document.querySelector('.container');
    container.classList.toggle('fullscreen');
    
    const icon = document.querySelector('.header-btn[onclick="fullscreen()"] i');
    if (container.classList.contains('fullscreen')) {
        icon.className = 'fas fa-compress';
    } else {
        icon.className = 'fas fa-expand';
    }
}

// 语音输入相关变量
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

// 开始语音输入
function startVoiceInput() {
    const modal = document.getElementById('voiceModal');
    modal.style.display = 'flex';
}

// 关闭语音模态框
function closeVoiceModal() {
    const modal = document.getElementById('voiceModal');
    modal.style.display = 'none';
    stopVoiceRecording();
}

// 切换语音录音
async function toggleVoiceRecording() {
    if (isRecording) {
        stopVoiceRecording();
    } else {
        await startVoiceRecording();
    }
}

// 开始语音录音
async function startVoiceRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            // 这里可以添加语音转文字的逻辑
            console.log('录音完成:', audioBlob);
            showNotification('录音完成', '语音已录制，暂不支持转文字功能', 'info');
        };
        
        mediaRecorder.start();
        isRecording = true;
        
        // 更新UI状态
        document.getElementById('voiceToggleBtn').classList.add('recording');
        document.getElementById('voiceVisualizer').classList.add('recording');
        document.getElementById('voiceStatus').textContent = '正在录音...';
        
    } catch (error) {
        console.error('录音失败:', error);
        showNotification('错误', '无法访问麦克风', 'error');
    }
}

// 停止语音录音
function stopVoiceRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        isRecording = false;
        
        // 更新UI状态
        document.getElementById('voiceToggleBtn').classList.remove('recording');
        document.getElementById('voiceVisualizer').classList.remove('recording');
        document.getElementById('voiceStatus').textContent = '录音已停止';
    }
}

// 显示通知
function showNotification(title, message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-title">${title}</div>
        <div class="notification-message">${message}</div>
    `;
    
    document.body.appendChild(notification);
    
    // 显示动画
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // 自动隐藏
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 更新聊天标题
function updateChatTitle(title) {
    const titleElement = document.getElementById('currentChatTitle');
    if (titleElement) {
        titleElement.textContent = title;
    }
}

// 初始化主题
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
    
    const icon = document.querySelector('.action-btn[onclick="toggleTheme()"] i');
    if (icon) {
        icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}
