# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import pandas as pd
from input_parse import InputParser
from run_stock_tag_code import StockTagProcessor
from data_process.reverse_index import RveIndex
from strategy_explore import StrategyExplore
import warnings
import re
import os

# 忽略警告
warnings.filterwarnings('ignore')

# 初始化 Flask 应用
app = Flask(__name__)

# 配置CORS，允许前端跨域访问
CORS(app, origins=['http://localhost:8000', 'http://127.0.0.1:8000'], supports_credentials=True)

# 配置参数（可根据需要外部化）
API_KEY = "sk-8948b4b75ee84da4a00b3d9a003ba635"
TS_TOKEN = "849b7324f12baf30b3ea43a6eea15d9dd75118b7352228fc6ebbb490"
TS_CODE = '600619.SH'
START_DATE = '20250101'
END_DATE = '20250801'
TAG_CODES_FILE = './data/stock_tag_codes.json'


@app.route('/explore', methods=['POST'])
def explore_stock_strategy():
    try:
        # 1. 获取请求数据
        data = request.get_json()
        target = data.get("input")
        if not target:
            return jsonify({"error": "缺少 'input' 参数"}), 400

        # 2. 初始化解析器
        parser = InputParser(
            api_key=API_KEY,
            ts_token=TS_TOKEN,
            ts_code=TS_CODE,
            start_date=START_DATE,
            end_date=END_DATE
        )

        target_df = parser.parse(target)

        # 3. 标签处理
        processor = StockTagProcessor(target_df, TAG_CODES_FILE)
        tag_df = processor.process_tags(num_processes=2)

        # 4. 合并标签与目标数据
        target_tag_df = pd.concat([tag_df, target_df], axis=1, join='inner')

        # 5. 反向索引获取 top 5 标签
        rve = RveIndex(target_tag_df)
        tag_list = rve.get_top_tag(target_col='target', top_n=5)
        article_list = rve.search_reverse_index(tag_list, top_n=5)

        # 6. 构建可视化数据
        result_df = pd.concat([tag_df[tag_list], target_df], axis=1, join='inner')

        # 7. AI 策略探索
        vectors = tag_df.fillna(0).astype(int).to_dict(orient='list')
        seed = target_df["target"].values.tolist()

        se = StrategyExplore(
            vectors,
            seed,
            max_depth=3,
            generations=400,
            pop_size=50,
            max_elements=3
        )
        best_expr, result_vector, distance = se.evolve()

        # 添加 AI 探索结果列
        result_df["AI_explore"] = result_vector

        # 8. 提取表达式中的标签
        best_expr_tags = [
            p.strip() for p in re.split(r'[()\s]+and\b|\b(?:and|or)\b|[()\s]+', best_expr, flags=re.IGNORECASE)
            if p.strip()
        ]

        # 9. 读取标签解释
        with open(TAG_CODES_FILE, 'r', encoding='utf-8') as f:
            data_dic = json.load(f)

        # 10. 构建返回结果
        result = {
            "k线可视化数据": result_df.to_dict(orient='records'),
            "复合指标探索": best_expr,
            "推荐指标": article_list
        }

        # 添加标签解释
        all_tags = set(tag_list + best_expr_tags)
        for t in all_tags:
            if t in data_dic:
                result[t] = data_dic[t]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # 确保 data 目录存在
    if not os.path.exists('./data'):
        os.makedirs('./data')
    app.run(host='0.0.0.0', port=5001, debug=True)