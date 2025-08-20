# -*- coding: utf-8 -*-
# # -*- coding = utf-8 -*-
import os
from openai import OpenAI
import re
import csv
from filelock import FileLock
from multiprocessing import Pool


def code_process(code):
    prompt = """{}

    你需要完成以下任务:
    1、逐行翻译这段通达信指标公式，翻译时不要出现源码，只写中文逻辑。画线绘图公式也要翻译，你可以参考这些绘图函数的说明来翻译画线语句：
    DRAWKLINE(HIGH,OPEN,LOW,CLOSE)		画K线。四个参数分别为H,O,L,C(按顺序）	
    STICKLINE(COND,PRICE1,PRICE2,WIDTH,EMPTY)	STICKLINE(CLOSE>OPEN,CLOSE,OPEN,0.8,1)	满足条件时，在AB之间画宽度为X的柱状线，EMPTY参数用来控制画实心柱还是空心柱	
    DRAWICON(COND,PRICE,TYPE)	                DRAWICON(CLOSE>OPEN,LOW,1)	满足条件时，在PRICE位置画图标。不同图标代表不同图标类型。
    DRAWTEXT(COND,PRICE,TEXT)	DRAWTEXT(CLOSE/OPEN>1.08,LOW,'大阳线')	满足条件时，在PRICE位置，书写文案TEXT
    DRAWBAND(VAL1,COLOR1,VAL2,COLOR2)	DRAWBAND(OPEN,RGB(0,224,224),CLOSE,RGB(255,96,96));	当VAL1大于VAL2时，在VAL1与VAL2之间画颜色1；当VAL1小于VAL2时，在VAL1与VAL2之间画颜色2。
    2、描述策略详细逻辑，你需要逐行翻译，去除其中的画线语句，分析变量定义的逻辑，使用这些已经定义的变量，判断何时买入，何时卖出如果是单边策略可以只有一个操作。
    3、用一句话描述这个策略的逻辑。
    4、请你简要说明这段量化策略适合在什么样的股票上使用，可以从技术面分析2买点和卖点的技术形态，买点技术形态：底部放量，卖点技术形态：顶部缩量。
    5、请你为这段代码打上3类标签，用于后续用户搜索。首先请你参考逐行的代码逻辑打标至少5个标签词，记住：一定要和代码逻辑强相关，不要说一些概念性的，宽泛的词，比如量价关系，技术分析等，
    其次根据策略逻辑在以下标签中：[分时 基本面 短线 中线 长线 涨停 趋势 波段 抄底 逃顶 换手率 突破 筹码 资金 成交量 庄家 机构 背离 牛股 主力 吸筹 追涨 杀跌 支撑 压力]。选取最相关的5个标签作为策略类型标签。
    最后抽取分析最相关的5个指标技术形态标签，作为策略指标技术形态标签，比如macd金叉买入，RSI超卖，底部十字买入，务必具体一点，比如均线策略，要说明是什么周期的均线，金叉要说明是什么指标金叉。
    按照以下标题输出：
    ### 1、逐行翻译
    ### 2、策略详细逻辑
    ### 3、一句话总结策略逻辑
    ### 4、适用股票类型
    ### 5、标签


    """.format(code)
    # 初始化OpenAI客户端
    client = OpenAI(
        api_key="sk-8948b4b75ee84da4a00b3d9a003ba635",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    completion = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
        # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
        extra_body={"enable_thinking": False},
    )
    return completion.choices[0].message.content


def answer_extract(text):
    # 使用正则表达式按标题分割文本
    sections = re.split(r'### \d、', text)[1:]  # 跳过第一个空元素

    # 提取每个部分的标题和内容
    result_dict = {}
    titles = [
        "逐行翻译",
        "策略详细逻辑",
        "一句话总结策略逻辑",
        "适用股票类型",
        "标签"
    ]

    for i, section in enumerate(sections):
        key = titles[i]
        content = section.strip()
        result_dict[key] = content.replace(key, "")
    return result_dict


def load_data(file_path):
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = [row for row in reader]
    return data


def process_and_save(data):
    output_file = "../data/tdx_already_done.csv"
    lock_file = output_file + ".lock"  # 对应的锁文件

    for i in data:
        try:
            text = code_process(i["公式源码"])
            if "没有源码" in i["公式源码"]:
                continue
            else:
                text_dic = answer_extract(text)
                # print(text_dic)
                # 补充原始字段
                text_dic["公式源码"] = i["公式源码"]
                text_dic["标题"] = i["标题"]
                text_dic["中文"] = i["中文"]
                text_dic["发布时间和点击"] = i["发布时间和点击"]
                text_dic["公式链接"] = i["公式链接"]

                # 加锁写入文件
                with FileLock(lock_file):  # 获取锁
                    file_exists = os.path.isfile(output_file)
                    with open(output_file, mode='a', encoding='utf-8',
                              newline='') as f:
                        writer = csv.DictWriter(f,
                                                fieldnames=text_dic.keys())
                        if not file_exists:
                            writer.writeheader()  # 第一次写入时添加表头
                        writer.writerow(text_dic)  # 写入一行数据
        except:
            continue


def chunk_list(lst, chunks):
    """将列表均分成 chunks 份"""
    n = len(lst)
    return [lst[i * n // chunks: (i + 1) * n // chunks] for i in
            range(chunks)]


def main_process():
    # 已处理的数据
    if os.path.exists("../data/tdx_already_done.csv"):
        already_done = load_data("../data/tdx_already_done.csv")
    else:
        already_done = []
    # 原始数据
    data = load_data("../data/通达信.csv")
    # 构建已处理集合（基于“标题”+“链接”唯一标识）
    done_set = {(item["标题"], item["公式链接"]) for item in already_done}
    # 筛选未处理的数据
    todo_data = [
        item for item in data
        if (item["标题"], item["公式链接"]) not in done_set
    ]
    print(f"总共数据: {len(data)}")
    print(f"已处理: {len(already_done)}")
    print(f"待处理: {len(todo_data)}")
    if not todo_data:
        print("没有需要处理的新数据。")
        return
    # 均分成 4 个子任务
    tasks = chunk_list(todo_data, 4)
    # 创建 4 个进程并发处理
    with Pool(processes=4) as pool:
        pool.map(process_and_save, tasks)
    print("全部数据处理完成。")


if __name__ == '__main__':
    main_process()
