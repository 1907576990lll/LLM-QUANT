# -*- coding: utf-8 -*-
# -*- coding = utf-8 -*-
"""
------------------------------------
@创建时间:2025/7/7 上午10:36
作者:liliuliu
@文件名:get_all.py
------------------------------------
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from tqdm import trange
import re
import csv
import os

CSV_FILE = 'data/通达信111.csv'

URLS = {"通达信": "https://www.gpxiazai.com/gpgs/html/list22-729.html"}


# "通达信": "https://www.gpxiazai.com/gpgs/html/list22-729.html"
# "同花顺": "https://www.gpxiazai.com/gpgs/html/list25-23.html",
# "大智慧": "https://www.gpxiazai.com/gpgs/html/list23-87.html"}


def append_to_csv(info):
    """
    将信息追加写入CSV文件。如果文件不存在，则先写入标题行。

    :param info: 包含要写入的数据的列表，如 ['标题', '公式链接', '列表链接', '中文', '发布时间点击次数', '公式源码']
    """
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, mode='a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            # 如果是第一次写入，添加标题行
            writer.writerow(['标题', '公式链接', '列表链接', '中文', '发布时间和点击', '公式源码', '来源'])
        writer.writerows(info)


class GetAll:
    def __init__(self):
        self.url = URLS
        self.driver = webdriver.PhantomJS()
        self.wait = WebDriverWait(self.driver, 10)
        try:
            self.already = [i[0] for i in pd.read_csv("通达信.csv")[['列表链接']].values.tolist()]
        except:
            self.already = []

    def get_single_page_links(self, url):
        """获取标题和内容链接"""
        self.driver.get(url)
        # 等待页面加载完成
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'softlistbox')))
        # 提取当前页的所有公示列表链接和标题
        items = self.driver.find_elements(By.XPATH, "//table[@width='100%']//tr[td[@width='85%']]")
        page_items = []
        titles_and_hrefs = []
        for item in items:
            try:
                link_element = item.find_element(By.XPATH, ".//a")
                title = link_element.text.strip()
                href = link_element.get_attribute("href").strip()
                titles_and_hrefs.append((title, href))
            except:
                print("元素已失效，跳过此条目")
                continue

        # 第二步：脱离DOM进行后续处理
        for title, href in titles_and_hrefs:
            page_info = self.extract_page_info(href)
            page_items.append([
                title, href, url,
                page_info["all_chinese_content"],
                page_info["publish_time_click"],
                page_info["formula_source_code"]
            ])
        return page_items

    def get_all_links(self):
        """获取所有需要爬取的链接"""
        result = []
        for k in self.url:
            base_url = self.url[k]
            source = k
            max_page_num = base_url.split("-")[-1].split(".")[0]
            # 以下测试用
            for page_num in trange(1, int(max_page_num) + 1):
                url = base_url.replace(max_page_num, str(page_num))
                print(url)
                if url in self.already:
                    print(url, "done")
                    continue
                else:

                    page_items_info = self.get_single_page_links(url) + [source]

                    result = result + page_items_info
                    time.sleep(1)  # 控制请求频率，避免被封IP
                    append_to_csv(page_items_info)
        return result

    def extract_page_info(self, url):
        """获取页面上的全部中文内容、公式源码、发布时间及点击信息"""
        self.driver.get(url)
        time.sleep(1)  # 等待页面加载完成
        # 获取 <DIV id="content"> 内的内容

        # 提取 <p> 标签和 .copydiv 中的文本内容
        p_elements = self.driver.find_elements(By.TAG_NAME, 'p')
        copydiv_element = self.driver.find_element(By.CLASS_NAME, 'copydiv') if \
            self.driver.find_elements(By.CLASS_NAME, 'copydiv') else None

        # 收集所有 <p> 和 copydiv 中的原始文本
        combined_text = ""
        for p in p_elements:
            combined_text += p.text + "\n"
        if copydiv_element:
            combined_text += copydiv_element.text

        # 提取中文字符和常用中文标点符号（包括句号、逗号、括号等）
        def extract_chinese_with_punctuation(text):
            # 匹配中文字符及常见中文标点：！“”#￥%＆‘’（）*+，-。/：；<=>？@【】、^＿`《》「」『』～【】
            pattern = r'[\u4e00-\u9fa5\u3000-\u303F\uff00-\uffef]'
            return ''.join(re.findall(pattern, text))

        all_chinese_content = extract_chinese_with_punctuation(combined_text)

        # 提取发布时间和点击数
        publish_time_elem = self.driver.find_element(By.XPATH, '//td[@style="line-height:45px;"]')
        publish_time_text = publish_time_elem.text.strip() if publish_time_elem else "未知"
        # 原始公式源码：直接获取 copydiv 的 HTML 内容（保留换行和格式）
        formula_source_code = "没有源码"
        try:
            if copydiv_element is None:
                paragraphs = self.driver.find_elements_by_tag_name('p')
                for p in paragraphs:
                    br_tags = p.find_elements_by_tag_name('br')
                    if len(br_tags) >= 2:
                        formula_source_code = p.text.strip()
                        break  # 找到第一个符合条件的 <p> 后退出循环
            else:
                formula_source_code = copydiv_element.text
        except:
            print(url, "没有源码")
        print("*" * 100)
        return {
            "all_chinese_content": all_chinese_content,
            "publish_time_click": publish_time_text,
            "formula_source_code": formula_source_code
        }


if __name__ == '__main__':
    g = GetAll()
    result = g.get_all_links()
    g.driver.quit()
    print(len(result))