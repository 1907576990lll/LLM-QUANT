# 前端无法调用后端服务 - 故障排除指南

## 问题描述
前端界面显示错误："抱歉，处理您的请求时遇到了问题：Load failed。请确保股票分析服务正在运行（端口5000）。"

## 问题原因
1. **CORS配置缺失**：后端Flask服务缺少跨域资源共享(CORS)配置
2. **Python环境问题**：conda环境激活后，python命令仍指向系统Python而不是conda环境中的Python
3. **依赖包缺失**：缺少flask-cors包

## 解决方案

### 1. 安装必要的依赖包
```bash
conda activate python12
pip install flask-cors
```

### 2. 修复后端服务CORS配置
在 `策略推荐/main_service.py` 中添加了CORS配置：
```python
from flask_cors import CORS

# 配置CORS，允许前端跨域访问
CORS(app, origins=['http://localhost:8000', 'http://127.0.0.1:8000'], supports_credentials=True)
```

### 3. 使用正确的Python路径启动服务
```bash
# 使用完整路径启动后端服务
/Users/mac/miniconda3/envs/python12/bin/python main_service.py
```

### 4. 使用修复后的启动脚本
```bash
./start_fixed.sh
```

## 验证步骤

### 1. 检查服务状态
```bash
# 检查端口监听状态
netstat -an | grep 5000

# 检查进程状态
ps aux | grep main_service.py
```

### 2. 测试API连接
```bash
# 使用curl测试
curl -s http://localhost:5000/explore -X POST -H "Content-Type: application/json" -d '{"input":"测试"}'
```

### 3. 使用调试工具
访问 `http://localhost:8000/debug.html` 进行API连接测试

## 常见问题

### Q: 为什么conda activate后python命令仍指向系统Python？
A: 这是macOS上的常见问题。使用完整路径 `/Users/mac/miniconda3/envs/python12/bin/python` 来确保使用正确的Python环境。

### Q: 如何确认CORS配置生效？
A: 在浏览器开发者工具中查看Network标签，确认请求没有CORS错误。

### Q: 前端仍然无法连接怎么办？
A: 
1. 确认后端服务正在运行：`ps aux | grep main_service.py`
2. 确认端口正在监听：`netstat -an | grep 5000`
3. 使用调试页面测试：`http://localhost:8000/debug.html`
4. 检查浏览器控制台错误信息

## 启动命令总结

### 手动启动
```bash
# 启动后端服务
cd 策略推荐
/Users/mac/miniconda3/envs/python12/bin/python main_service.py &

# 启动前端服务
cd ..
python3 -m http.server 8000 &
```

### 使用脚本启动
```bash
./start_fixed.sh
```

## 服务地址
- 前端界面：http://localhost:8000
- 后端API：http://localhost:5000
- 调试工具：http://localhost:8000/debug.html
