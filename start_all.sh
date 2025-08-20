#!/bin/bash

echo "🚀 启动AI助手完整系统..."
echo "📁 项目目录: $(pwd)"
echo ""

# 检查Python是否可用
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请安装Python"
    exit 1
fi

# 检查策略推荐目录是否存在
if [ ! -d "策略推荐" ]; then
    echo "❌ 未找到策略推荐目录"
    exit 1
fi

echo "🔧 启动后端股票分析服务..."
cd "策略推荐"

# 检查必要的文件是否存在
if [ ! -f "main_service.py" ]; then
    echo "❌ 未找到main_service.py文件"
    exit 1
fi

# 启动后端服务
echo "🌐 后端服务地址: http://localhost:5000"
python3 main_service.py &
BACKEND_PID=$!

# 等待后端服务启动
echo "⏳ 等待后端服务启动..."
sleep 3

# 检查后端服务是否启动成功
if curl -s http://localhost:5000 > /dev/null 2>&1; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

cd ..

echo ""
echo "🌐 启动前端Web服务..."
echo "📱 前端地址: http://localhost:8000"

# 启动前端服务
python3 -m http.server 8000 &
FRONTEND_PID=$!

echo ""
echo "🎉 系统启动完成！"
echo "📊 股票分析API: http://localhost:5000"
echo "🌐 前端界面: http://localhost:8000"
echo ""
echo "💡 使用说明："
echo "1. 在浏览器中打开 http://localhost:8000"
echo "2. 输入股票相关问题，如：'请帮我分析哪只股票次日涨幅可能超过5%'"
echo "3. AI将调用后端API进行分析并展示结果"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap 'echo ""; echo "🛑 正在停止服务..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo "✅ 服务已停止"; exit 0' INT

# 保持脚本运行
wait
