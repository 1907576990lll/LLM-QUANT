import json
import re
import numpy as np
from collections import defaultdict
from tqdm import tqdm
from openai import OpenAI
from multiprocessing import Pool


class StockTagCode:
    def __init__(self, api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"):
        self.api_key = api_key
        self.base_url = base_url

    # -------------------------
    # 标签生成部分
    # -------------------------

    def stock_tag_code_gen(self, text):
        """调用模型生成技术信号代码"""
        prompt = self._build_prompt(text)
        return self._call_model(prompt)

    def _build_prompt(self, text):
        """构建提示词"""
        return """现在有一份df数据，包含 trade_date open   high    low  close  pre_close  change  pct_chg  vol  amount字段。
        现在需要在这份数据中，根据输入，标识出特定的技术指标信号，请你写出标注信号的python代码。可以参考以下输入和输出样例,注意新增列的列名与输入
        需要严格保持一致,你只能新增这一列，这一列的值必须是整型0或者1，分别标识信号触发和未触发，不要修改任何已有列，包括索引列，中间列使用之后需要删除,代码运行前后不能使行数变化，所以dropna等函数不要轻易使用。
        输入：放量信号
        输出：
        def volume_increase(df):
            #放量信号：成交量比前一日增加超过50%
            df["放量信号"] = (df["vol"] > df["vol"].shift(1) * 1.5).astype(int)
            return df
        df = volume_increase(df)

        输入：十字星形态
        输出：
        def cross_k(df):
            df["十字星形态"] = ((abs(df["open"] - df["close"]) / df["close"] < 0.005) & ((df["high"] - df["low"]) / df["low"] > 0.015)).astype(int)
            return df
        df = cross_k(df)

        注意：信号只有0，1两种bool值分别标识没有出现，和出现，请确保代码可以运行。

        输入：{text}

        """.format(text=text)

    def _call_model(self, prompt):
        """调用模型接口（在子进程中创建 client）"""
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            extra_body={"enable_thinking": False},
        )
        return completion.choices[0].message.content

    def extract_code_and_chinese_text(self, content):
        """提取代码和中文说明"""
        code = self._extract_code(content)
        text = self._extract_chinese_text(content, code)
        return {"code": code.strip(), "text": text.strip()}

    def _extract_code(self, content):
        """提取代码块"""
        code_pattern = re.compile(r'```python(.*?)```', re.DOTALL)
        match = code_pattern.search(content)
        return match.group(1).strip() if match else ""

    def _extract_chinese_text(self, content, code_block):
        """提取中文说明"""
        content_without_code = re.sub(r'```python.*?```', '', content, flags=re.DOTALL)
        chinese_pattern = re.compile(r'[\u4e00-\u9fff\w\s，。！？、：“”‘’；（）《》〈〉【】〔〕…—～％＃＠＆＊－＋＝]')
        return ''.join(chinese_pattern.findall(content_without_code)).strip()

    # -------------------------
    # 多进程处理
    # -------------------------

    def process_item(self, dtag):
        """处理单个标签"""
        content = self.stock_tag_code_gen(dtag)
        return dtag, self.extract_code_and_chinese_text(content)

    @staticmethod
    def _process_item_wrapper(args):
        """用于多进程的静态方法包装器"""
        instance, dtag = args
        return instance.process_item(dtag)

    def tag_main(self, deduplicated_texts, pool_size=16):
        """多进程生成所有标签代码"""
        results = self._run_multiprocess(deduplicated_texts, pool_size)
        tag_code = {k: v for k, v in results}
        self._save_to_json(tag_code)
        return tag_code

    def _run_multiprocess(self, deduplicated_texts, pool_size):
        """运行多进程任务"""
        with Pool(processes=pool_size) as pool:
            # 传入 self 和参数
            args = [(self, dtag) for dtag in deduplicated_texts]
            return list(tqdm(pool.imap_unordered(self._process_item_wrapper, args),
                             total=len(deduplicated_texts)))

    def _save_to_json(self, tag_code):
        """保存结果到 JSON 文件"""
        with open('./data/stock_tag_codes.json', 'w', encoding='utf-8') as json_file:
            json.dump(tag_code, json_file, ensure_ascii=False, indent=4)

    # -------------------------
    # 语义去重
    # -------------------------

    def semantic_deduplicate(self, json_file, threshold=0.9, verbose=True):
        """语义去重主方法"""
        data = self._load_embeddings(json_file)
        texts, embeddings = self._parse_embeddings(data)
        normalized_embeddings = self._normalize_embeddings(embeddings)
        similarity_matrix = self._compute_similarity(normalized_embeddings)
        to_keep, seed_to_removed = self._apply_deduplication(similarity_matrix, texts, threshold)
        deduplicated_texts = [texts[i] for i in range(len(texts)) if to_keep[i]]
        if verbose:
            self._print_deduplication_result(seed_to_removed)
        return deduplicated_texts, seed_to_removed

    def _load_embeddings(self, json_file):
        """加载嵌入向量"""
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _parse_embeddings(self, data):
        """解析嵌入向量"""
        texts = list(data.keys())
        embeddings = np.array([np.array(vec, dtype=np.float32) for vec in data.values()])
        return texts, embeddings

    def _normalize_embeddings(self, embeddings):
        """归一化嵌入向量"""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / norms

    def _compute_similarity(self, normalized_embeddings):
        """计算余弦相似度矩阵"""
        return np.dot(normalized_embeddings, normalized_embeddings.T)

    def _apply_deduplication(self, similarity_matrix, texts, threshold):
        """应用去重逻辑"""
        to_keep = [True] * len(texts)
        seed_to_removed = defaultdict(list)

        for i in tqdm(range(len(texts)), desc="Processing items", unit="item"):
            if not to_keep[i]:
                continue
            for j in range(i + 1, len(texts)):
                if to_keep[j] and similarity_matrix[i, j] >= threshold:
                    to_keep[j] = False
                    seed_to_removed[texts[i]].append(texts[j])
        return to_keep, seed_to_removed

    def _print_deduplication_result(self, seed_to_removed):
        """打印去重结果"""
        print("\n=== 每个种子文本对应的去重内容 ===\n")
        for seed, removed_list in seed_to_removed.items():
            print(f"种子文本：{seed}")
            for removed in removed_list:
                print(f"  被去重文本：{removed}")
            print()

    # -------------------------
    # 主流程
    # -------------------------

    def run(self, json_file="./data/embeddings.json", threshold=0.955):
        """运行完整流程"""
        deduplicated_texts, seed_to_removed = self.semantic_deduplicate(json_file, threshold)
        result = self.tag_main(deduplicated_texts)
        return result, seed_to_removed


# 示例用法
if __name__ == "__main__":
    api_key = "sk-8948b4b75ee84da4a00b3d9a003ba635"
    stock_tagger = StockTagCode(api_key)
    result, seed_to_removed = stock_tagger.run()
    print("生成的标签代码已保存到 stock_tag_codes.json")