# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import time

# 初始化 Flask 应用
app = Flask(__name__)

# 配置CORS，允许前端跨域访问
CORS(app, origins=['http://localhost:8000', 'http://127.0.0.1:8000'], supports_credentials=True)

@app.route('/explore', methods=['POST'])
def explore_stock_strategy():
    try:
        print("收到API请求...")
        
        # 1. 获取请求数据
        data = request.get_json()
        target = data.get("input")
        if not target:
            return jsonify({"error": "缺少 'input' 参数"}), 400

        print(f"输入内容: {target}")
        
        # 2. 模拟处理时间
        time.sleep(1)
        
        # 3. 返回测试结果
        result = {
            "k线可视化数据": [],
            "复合指标探索": "测试复合指标",
            "推荐指标": ["测试指标1", "测试指标2"],
            "测试标签": {
                "code": "print('test')",
                "text": "这是一个测试标签"
            }
        }

        print("返回结果...")
        return jsonify(result), 200

    except Exception as e:
        print(f"错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "服务正常运行"}), 200

if __name__ == '__main__':
    print("启动简化测试服务...")
    app.run(host='0.0.0.0', port=5001, debug=True)
