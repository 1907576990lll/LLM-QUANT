# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import requests
import json

# 1. 配置服务地址
BASE_URL = "http://localhost:5001"
ENDPOINT = "/explore"

# 2. 构造请求数据
payload = {
    "input": "请帮我分析哪只股票次日涨幅可能超过5%，并找出背后的模式和指标组合"
}

# 3. 发送 POST 请求
try:
    print("正在发送请求...")
    response = requests.post(
        BASE_URL + ENDPOINT,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8')
    )

    # 4. 处理响应
    if response.status_code == 200:
        result = response.json()
        print("\n✅ 请求成功！返回结果示例（前2条数据）：")
        print(json.dumps(result, indent=2, ensure_ascii=False)[:2000], "...")
    else:
        print(f"❌ 请求失败，状态码：{response.status_code}")
        print("错误信息：", response.text)

except requests.exceptions.ConnectionError:
    print("❌ 连接失败，请确保 Flask 服务已运行（python app.py）")
except Exception as e:
    print(f"❌ 发生异常：{str(e)}")