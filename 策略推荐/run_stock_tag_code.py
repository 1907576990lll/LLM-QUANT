import pandas as pd
import json
from multiprocessing import Pool, cpu_count
import tushare as ts


class StockTagProcessor:
    def __init__(self, df, json_path):
        self.df = df.copy()
        self.json_path = json_path
        self.result = self._load_json()

    def _load_json(self):
        with open(self.json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _run_code_for_tag(self, tag_info):
        """
        每个进程执行的函数，用于处理一个 tag
        """
        tag_name, code_info = tag_info
        code = code_info["code"]
        df = self.df.copy()  # 每个进程使用自己的 df 副本
        try:
            locals_dict = {'df': df}
            exec(code, {}, locals_dict)
            new_df = locals_dict['df']
            if tag_name in new_df.columns:
                if len(df) != len(new_df):
                    print(
                        f"Tag {tag_name} 执行后df的序列长度发生改变.*****************************\n")
                    return tag_name, None
                else:
                    return tag_name, new_df[tag_name]
            else:
                # print(f"Tag {tag_name} 执行后列名与标签名不一致\n")
                # print(code)4. MACD式动能柱增强（致富线）和MACD式动能柱增强（致富线）不一致，这种后面优化。
                return tag_name, None

        except Exception as e:
            # print(f"执行时python报错 {tag_name}: {e}\n")
            return tag_name, None

    def process_tags(self, num_processes=None):
        """
        主函数，启动多进程处理所有标签
        """
        if num_processes is None:
            num_processes = cpu_count()  # 默认使用所有 CPU 核心

        with Pool(processes=num_processes) as pool:
            results = pool.map(self._run_code_for_tag, self.result.items())

        # 收集结果
        result_dict = {tag: series for tag, series in results if
                       (series is not None) and isinstance(series.index,
                                                           pd.DatetimeIndex)}

        return pd.DataFrame(result_dict)


if __name__ == '__main__':
    # 使用示例：
    ts.set_token(
        '849b7324f12baf30b3ea43a6eea15d9dd75118b7352228fc6ebbb490')
    pro = ts.pro_api()

    # 获取股票数据
    df_ori = pro.daily(ts_code='000001.SZ', start_date='20240901',
                       end_date='20250101')

    # 将数据转换为 pandas DataFrame 并设置日期索引
    df_ori['trade_date'] = pd.to_datetime(df_ori['trade_date'])
    df_ori.set_index('trade_date', inplace=True)

    # 按照日期升序排序（默认是降序）
    df_ori = df_ori.sort_index()
    processor = StockTagProcessor(df_ori, './data/stock_tag_codes.json')
    result_df = processor.process_tags(num_processes=4)  # 可指定进程数
    for col in result_df.columns:
        print(f"列名: {col}")
        print(result_df[col].value_counts())
        print("-" * 40)
