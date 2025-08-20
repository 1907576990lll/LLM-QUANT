# -*- coding: utf-8 -*-
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd


def top_k_tags(df, incd):
    """
    根据给定的日期索引 incd，构造一个 seed 列（只有 incd 行为 1，其余为 0），
    计算所有其他 0/1 标签列与 seed 列的余弦相似度，返回按相似度排序的列名和值。

    参数:
    df -- 打上标签列的 DataFrame（包含所有信号列）
    incd -- 标准买卖点的日期索引（字符串或 Timestamp）

    返回:
    按相似度降序排列的元组列表 [(列名, 相似度值), ...]
    """
    # 1. 创建 seed 列：只有 incd 行为 1，其余为 0
    df = df.copy()  # 避免修改原始 df
    df['seed'] = 0
    df.loc[incd, 'seed'] = 1  # 使用标签索引赋值，incd 是日期索引

    # 2. 去除不需要的列（保留 seed 列和其他信号列）
    columns_to_drop = ['ts_code', 'open', 'high', 'low', 'close',
                       'pre_close', 'change', 'pct_chg', 'vol', 'amount']
    df_filtered = df.drop(columns=columns_to_drop, errors='ignore')

    # 确保所有列都是 0 或 1（布尔或整数）
    df_filtered = df_filtered.applymap(
        lambda x: 0 if pd.isna(x) or x == np.inf or x == -np.inf else int(
            bool(x)))

    # 3. 获取 seed 向量和其他信号列
    seed_vector = df_filtered['seed'].values.reshape(1, -1)

    similarity_scores = {}
    for col in df_filtered.columns:
        if col == 'seed' or col == 'bottom_peak' or col == 'top_peak':
            continue  # 跳过 seed 自己
        column_vector = df_filtered[col].values.reshape(1, -1)
        similarity = cosine_similarity(seed_vector, column_vector)[0][0]
        similarity_scores[col] = similarity

    # 4. 按相似度排序并返回
    sorted_similarities = sorted(similarity_scores.items(),
                                 key=lambda x: x[1], reverse=True)

    return sorted_similarities
