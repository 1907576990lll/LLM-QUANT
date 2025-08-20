# -*- coding: utf-8 -*-

import numpy as np
from tqdm.notebook import tqdm
import onnxruntime as ort
from transformers import AutoTokenizer
import os
import json
import re
import pandas as pd


# 原始文件提取所有标签，再embedding存储，注意去除空串，超长串。
def get_jishu_taglist():
    """获取技术形态标签，用于反打股票"""
    path = "data/tdx_already_done.csv"
    df = pd.read_csv(path)
    tags = []
    tags_text = df["标签"].values.tolist()
    for tags_str in tags_text:
        tags_dic = parse_tags_to_dict(tags_str)
        jishu_tags = tags_dic["技术指标形态"]
        tags = tags + jishu_tags
    return tags


def parse_tags_to_dict(text):
    text = text.split("输出")
    if len(text) == 1:
        text = text[0]
    else:
        text = text[1]
    sections = [s.strip() for s in re.split(r'####.*\n?', text) if
                s.strip()]
    result = {
        '通用词': [],
        '策略类型': [],
        '技术指标形态': []
    }
    # 检查是否正好有三个部分
    if len(sections) != 3:
        return result  # 不符合格式要求，跳过

    keys = list(result.keys())

    for i, sec in enumerate(sections):
        # 去除含有 # 的行
        lines = [line for line in sec.split('\n') if '#' not in line]
        clean_sec = '\n'.join(lines)

        # 判断是换行多还是逗号多
        newline_count = clean_sec.count('\n')
        comma_count = clean_sec.count('，')

        if newline_count >= comma_count:
            items = [item.strip('- ').strip() for item in
                     clean_sec.split('\n')]
        else:
            items = [item.strip('- ').strip() for item in
                     clean_sec.split(',')]

        result[keys[i]] = items

    return result


def encode_texts(strings):
    model_path = "models/multilingual-e5-small/onnx/model.onnx"
    batch_size = 10
    output_json_path = "embeddings.json"
    dim = 384

    # 加载 ONNX 模型和分词器
    session = ort.InferenceSession(model_path)
    tokenizer = AutoTokenizer.from_pretrained(
        "models/multilingual-e5-small")

    embeddings_dict = {}
    # 如果输出文件已经存在，则加载现有的数据
    if os.path.exists(output_json_path):
        with open(output_json_path, 'r', encoding='utf-8') as file:
            embeddings_dict = json.load(file)

    # 分批处理
    for i in tqdm(range(0, len(strings), batch_size),
                  desc="Encoding batches"):
        batch = strings[i:i + batch_size]
        # 使用 tokenizer 编码输入
        encoded = tokenizer(batch, padding=True, truncation=True,
                            return_tensors="np")

        # 显式构建 feed_dict
        feed_dict = {
            'input_ids': encoded['input_ids'],
            'attention_mask': encoded['attention_mask'],
            'token_type_ids': encoded.get('token_type_ids', np.zeros_like(
                encoded['input_ids']))
        }
        # 推理
        batch_embeddings = session.run(None, feed_dict)[0]  # 假设输出是第一个节点
        batch_embeddings = batch_embeddings[:, 0, :]
        # L2 Normalize（如果模型输出未归一化）
        batch_embeddings /= np.linalg.norm(batch_embeddings, axis=1,
                                           keepdims=True)

        # 将每条记录添加到字典中
        for text, embedding in zip(batch, batch_embeddings.tolist()):
            embeddings_dict[text] = embedding

        # 清理内存
        del encoded, feed_dict, batch_embeddings

    # 将结果写回到 JSON 文件中
    with open(output_json_path, 'w', encoding='utf-8') as file:
        json.dump(embeddings_dict, file, ensure_ascii=False, indent=2)

    print(f"Saved {len(embeddings_dict)} vectors to {output_json_path}")
