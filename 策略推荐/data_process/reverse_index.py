# -*- coding: utf-8 -*-
import json
import pandas as pd
from tqdm import tqdm
import numpy as np


class RveIndex:
    def __init__(self, df):
        # 有标签、有价格、有seed的df
        self.df = df
        with open('./data/stock_tag_codes.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        tag_list = list(data.keys())
        self.tag_list = tag_list
        article_df = pd.read_csv("data/tdx_already_done.csv")
        article_df = article_df.dropna()
        self.article_df = article_df

    def save_rev_index(self):
        """制作倒排索引，主键就按"公式链接"索引来"""
        tag_list = self.tag_list
        revers_dic = {}
        df_list_of_dicts = self.article_df.to_dict('records')
        for i in tqdm(range(len(tag_list))):
            tag_name = tag_list[i]
            # 标签里混有杂质，遇到跳过
            if len(tag_name) < 3:
                continue
            try:
                revers_dic[tag_name] = []
                for itm in df_list_of_dicts:
                    if tag_name in itm["标签"]:
                        revers_dic[tag_name].append(itm["公式链接"])
            except:
                continue
        with open("./data/revers_index.json", 'w',
                  encoding='utf-8') as file:
            json.dump(revers_dic, file, ensure_ascii=False, indent=2)

    def hamming_distance(self, s1, s2):
        """计算两个等长字符串s1, s2之间的汉明距离"""
        return sum(ch1 != ch2 for ch1, ch2 in zip(s1, s2))

    def get_top_tag(self, target_col='target', top_n=5):
        """根据汉明距离找到与seed最相似的topN标签"""
        distances = []
        seed_vector = self.df[target_col].values

        for col in self.df.columns:
            if col == target_col:
                continue
            vector = self.df[col].values
            distance = self.hamming_distance(seed_vector, vector)
            distances.append((col, distance))

        # 按距离排序并取前top_n个
        distances.sort(key=lambda x: x[1])
        return [item[0] for item in distances[:top_n]]

    def search_reverse_index(self, tag_list, top_n=5):
        with open("./data/revers_index.json", 'r',
                  encoding='utf-8') as file:
            revers_dic = json.load(file)

        article_list = []
        for tag in tag_list:
            if tag in revers_dic:
                article_list.extend(revers_dic[tag])

        from collections import Counter
        counter = Counter(article_list)
        most_common_articles = counter.most_common(top_n)

        return [article[0] for article in most_common_articles]