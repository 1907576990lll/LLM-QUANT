# AI助手 - 智能对话前端应用

一个现代化的AI对话前端界面，支持图文混排的智能交互。

## 功能特性

### 🎨 现代化UI设计
- 渐变背景和毛玻璃效果
- 响应式设计，支持桌面和移动端
- 流畅的动画和交互效果
- 美观的消息气泡设计

### 💬 智能对话功能
- 支持文字和图片混合输入
- 实时打字指示器
- 智能AI响应模拟
- 多轮对话支持
- **股票策略分析** - 集成后端API进行股票分析

### 📱 用户体验
- 自动调整输入框高度
- 支持Enter键发送消息
- 聊天历史本地存储
- 多会话管理

### 🖼️ 图片处理
- 支持图片上传和预览
- 图片与文字混排显示
- 自动图片压缩和优化

## 文件结构

```
ai-chat-app/
├── index.html          # 主页面文件
├── styles.css          # 样式文件
├── script.js           # JavaScript逻辑
└── README.md           # 项目说明
```

## 使用方法

### 🚀 快速启动（推荐）
```bash
# 一键启动完整系统（前端+后端）
./start_all.sh
```

### 🔧 分步启动

1. **启动后端股票分析服务**
   ```bash
   cd 策略推荐
   python3 main_service.py
   ```

2. **启动前端Web服务**
   ```bash
   # 使用Python
   python3 -m http.server 8000
   
   # 使用Node.js
   npx serve .
   
   # 使用PHP
   php -S localhost:8000
   ```

3. **开始对话**
   - 在浏览器中打开 http://localhost:8000
   - 输入股票相关问题，如："请帮我分析哪只股票次日涨幅可能超过5%"
   - AI将调用后端API进行分析并展示结果
   - 支持图片上传和普通对话

### 🧪 API测试
在浏览器控制台中运行：
```javascript
testAPI()  // 测试后端API连接
```

## 技术栈

- **HTML5**: 语义化标签和现代特性
- **CSS3**: Flexbox布局、渐变、动画、响应式设计
- **JavaScript ES6+**: 异步处理、本地存储、DOM操作
- **Font Awesome**: 图标库

## 主要功能模块

### 1. 消息管理
- 用户消息和AI消息的区分显示
- 消息时间戳记录
- 消息历史持久化

### 2. 图片处理
- 文件选择和预览
- Base64编码存储
- 图片显示优化

### 3. 聊天历史
- 多会话管理
- 会话标题自动生成
- 历史记录切换

### 4. UI交互
- 自动滚动到最新消息
- 打字指示器动画
- 输入框自适应高度

## 自定义配置

### 修改AI响应
在 `script.js` 中的 `generateAIResponse` 函数中修改响应逻辑：

```javascript
const responses = [
    "自定义响应1",
    "自定义响应2",
    // 添加更多响应
];
```

### 修改样式主题
在 `styles.css` 中修改颜色变量：

```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --text-color: #333;
    --bg-color: #f8f9fa;
}
```

### 连接真实AI API
替换 `generateAIResponse` 函数中的模拟响应：

```javascript
async function generateAIResponse(chat, userMessage) {
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: userMessage.text,
                images: userMessage.images
            })
        });
        
        const data = await response.json();
        // 处理AI响应
    } catch (error) {
        console.error('API调用失败:', error);
    }
}
```

## 浏览器兼容性

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## 开发计划

- [ ] 支持语音输入
- [ ] 代码高亮显示
- [ ] 消息搜索功能
- [ ] 导出聊天记录
- [ ] 主题切换
- [ ] 多语言支持

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 许可证

MIT License
