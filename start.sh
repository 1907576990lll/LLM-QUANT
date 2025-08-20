#!/bin/bash

echo "🚀 启动AI助手聊天应用..."
echo "📁 项目目录: $(pwd)"
echo "🌐 服务器地址: http://localhost:8000"
echo ""

# 检查Python是否可用
if command -v python3 &> /dev/null; then
    echo "✅ 使用Python3启动服务器..."
    python3 -m http.server 8000
elif command -v python &> /dev/null; then
    echo "✅ 使用Python启动服务器..."
    python -m http.server 8000
else
    echo "❌ 未找到Python，请安装Python或使用其他方法启动服务器"
    echo ""
    echo "其他启动方法："
    echo "1. 使用Node.js: npx serve ."
    echo "2. 使用PHP: php -S localhost:8000"
    echo "3. 直接打开index.html文件"
    exit 1
fi
