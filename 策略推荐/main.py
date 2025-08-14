# -*- coding: utf-8 -*-
import json

import pandas as pd
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mdates
from input_parse import InputParser
from run_stock_tag_code import StockTagProcessor
from data_process.reverse_index import RveIndex
from strategy_explore import StrategyExplore
from matplotlib import rcParams
import warnings
import re

warnings.filterwarnings('ignore')


def plot_kline_with_signals(df, signal_columns):
    """
    绘制K线图并标注信号点（修改版）

    参数:
    df (pd.DataFrame): 包含 ohlc 数据的 DataFrame，必须包含 'open', 'high', 'low', 'close' 列，且以 'trade_date' 为索引
    signal_columns (list of dicts): 标注信号列，现在采用 {"signal_name": "color"} 的形式
    """
    rcParams['font.family'] = 'Noto Serif CJK JP'

    # 确保日期是 datetime 类型

    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df['date_num'] = mdates.date2num(df.index)

    # 创建 OHLC 数据
    ohlc = df[['date_num', 'open', 'high', 'low', 'close']]

    # 创建画布
    fig, ax = plt.subplots(figsize=(16, 8))

    # 绘制 K 线图
    candlestick_ohlc(ax, ohlc.values, width=0.6, colorup='r',
                     colordown='g', alpha=0.8)

    # 设置 x 轴为日期格式
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    fig.autofmt_xdate()

    # 添加信号标注
    for signal in signal_columns:
        for column, color in signal.items():
            ax.scatter(df[df[column] > 0].index,
                       df[df[column] > 0]['close'],
                       color=color, label=column)

    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    plt.legend()
    plt.show()


if __name__ == '__main__':
    result = {}
    target = input(
        "请你告诉我你想探索的股票标的，以及你预期的收益如何")  # 次日收益5%以上
    parser = InputParser(
        api_key="sk-8948b4b75ee84da4a00b3d9a003ba635",
        ts_token="849b7324f12baf30b3ea43a6eea15d9dd75118b7352228fc6ebbb490",
        ts_code='600619.SH',
        start_date='20250101',
        end_date='20250801'
    )

    target_df = parser.parse(target)
    print("以下是符合你预期的买入点！")
    print("下面我会在指标库里进行指标探索寻找……")
    print("以下指标策略同你的预期最符合")
    processor = StockTagProcessor(target_df, './data/stock_tag_codes.json')
    tag_df = processor.process_tags(num_processes=2)
    print(tag_df)
    target_tag_df = pd.concat([tag_df, target_df], axis=1, join='inner')

    rve = RveIndex(target_tag_df)
    tag_list = rve.get_top_tag(target_col='target', top_n=5)
    atricle_list = rve.search_reverse_index(tag_list, top_n=5)
    print("以下是我找到的与你的预期操作最符合的几个单指标策略（画图）")
    print(tag_list)
    # 取出可视化数据
    result_df = pd.concat([tag_df[tag_list], target_df], axis=1,
                          join='inner')
    print("下面我将继续探索多指标策略组合")
    # 人工智能算法标签组合探索
    vectors = tag_df.fillna(0).astype(int).to_dict(orient='list')
    seed = target_df["target"].values.tolist()
    # 设置 max_elements 来控制表达式中最多使用的不同向量数量
    se = StrategyExplore(vectors, seed, max_depth=3, generations=400,
                         pop_size=50, max_elements=3)
    best_expr, result_vector, distance = se.evolve()
    print(f"\nBest Expression: {best_expr}")
    print(f"Result Vector: {result_vector}")
    print(f"Hamming Distance: {distance}")
    # 我探索到如下一条多指标策略，他的逻辑和操作点如下（画图）
    result_df["AI_explore"] = result_vector
    plot_kline_with_signals(result_df, [{"AI_explore": "blue"}])
    print("你还可以参考以下策略库策略，这些策略都是开源社区作者分享的。")
    print(atricle_list)
    print(result_df)
    result["k线可视化数据"] = result_df.to_dict(orient='records')
    result["复合指标探索"] = best_expr
    best_expr_tags = [p.strip() for p in
                      re.split(r'[()\s]+and\b|\b(?:and|or)\b|[()\s]+',
                               best_expr, flags=re.IGNORECASE) if
                      p.strip()]
    result["推荐指标"] = atricle_list
    with open("./data/stock_tag_codes.json", 'r', encoding='utf-8') as f:
        data_dic = json.load(f)
    for t in tag_list + best_expr_tags:
        result[t] = data_dic[t]

    # data={"tag1_explain":,"tag2_explain":,"tag3_explain":,
    # "tag4_explain":,
    # "tag5_explain":,"AI_explore_express":,"k线可视化数据":[{high:,open:,low:,
    # close:,tag1:,tag2:,tag3:,tag4:,tag5:,ai_explore:}]}
