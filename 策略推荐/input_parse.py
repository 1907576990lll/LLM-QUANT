# -*- coding: utf-8 -*-
from openai import OpenAI
import re
import tushare as ts
import pandas as pd


class InputParser:
    def __init__(self, api_key, ts_token, ts_code='000001.SZ',
                 start_date='20240901', end_date='20250101'):
        self.api_key = api_key
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        # 股票数据配置
        self.ts_token = ts_token
        self.ts_code = ts_code
        self.start_date = start_date
        self.end_date = end_date
        self.df = self._prepare_data()

    def _prepare_data(self):
        """获取并预处理数据"""
        ts.set_token(self.ts_token)
        pro = ts.pro_api()
        df = pro.daily(ts_code=self.ts_code, start_date=self.start_date,
                       end_date=self.end_date)
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df.set_index('trade_date', inplace=True)
        df = df.sort_index()
        return df

    def _build_prompt(self, que):
        """构建提示词"""
        return """入参df包含close和trade_date字段。请你生成python代码，根据用户输入，增加唯一的target列,
        不要改返回变量名。除了python代码部分之外，不要有任何其他字符。
        ###样例：
        输入：次日涨幅5%以上
        输出：
        def get_index(df):
            # 计算次日涨幅
            df['target'] = (df['close'].shift(-1) - df['close']) / df['close']  # 向前取下一日的涨幅
            # 找出涨幅大于5%的行的索引
            df['target'] = (df['target'] > 0.05).astype(int)
            return df
        df = get_index(df)
        ###指令
        输入：{que}
        """.format(que=que)

    def _call_model(self, prompt):
        """调用模型生成代码"""
        completion = self.client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            extra_body={"enable_thinking": False},
        )
        return completion.choices[0].message.content

    def _extract_code(self, content):
        """提取代码块"""
        code_block = re.search(r'```python(.*?)```', content, re.DOTALL)
        if code_block:
            return code_block.group(1).strip()
        return content.strip()

    def _generate_full_code(self, code):
        """拼接完整执行代码"""
        extra_code = """
# 设置你的 Tushare Token，替换成你自己的 token
import tushare as ts
import pandas as pd
ts.set_token('{ts_token}')  
pro = ts.pro_api()

# 获取股票数据
df = pro.daily(ts_code='{ts_code}', start_date='{start_date}', end_date='{end_date}')

# 将数据转换为 pandas DataFrame 并设置日期索引
df['trade_date'] = pd.to_datetime(df['trade_date'])
df.set_index('trade_date', inplace=True)
# 按照日期升序排序（默认是降序）
df = df.sort_index()
        """.format(
            ts_token=self.ts_token,
            ts_code=self.ts_code,
            start_date=self.start_date,
            end_date=self.end_date
        )
        return extra_code + code

    def parse(self, que):
        """主流程：解析用户输入，生成代码并执行"""
        prompt = self._build_prompt(que)
        response = self._call_model(prompt)
        code = self._extract_code(response)
        full_code = code  # 不再重复加载数据，因为 self.df 已加载

        print("生成代码：\n", full_code)

        # 执行代码并获取结果
        my_vars = {"df": self.df}
        try:
            exec(full_code, {}, my_vars)
        except Exception as e:
            print(f"代码执行出错: {e}")
            return None

        return my_vars["df"]


# 示例使用
if __name__ == "__main__":
    parser = InputParser(
        api_key="sk-8948b4b75ee84da4a00b3d9a003ba635",
        ts_token="849b7324f12baf30b3ea43a6eea15d9dd75118b7352228fc6ebbb490"
    )

    result, df = parser.parse("次日涨5%以上")
    print("返回索引：")
    print(result)
    print("股票数据：")
    print(df)
