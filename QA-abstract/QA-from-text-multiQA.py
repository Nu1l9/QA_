# -*- coding: utf-8 -*-
# @Author: Gaoyongjie
# @Date:  2025-05-21 14:00:00
# @Last Modified by: GYJ
# @Last Modified time: 2025-05-21 14:00:00

"""
指定prompt给出文本，提取多个QA对
"""
import sys
import random
import re
import json
import time
import os
import requests
from PyPDF2 import PdfReader
from datetime import datetime
current_time = datetime.now().strftime("%m-%d_%H-%M")

# 直接用requests连接自己的推理服务器
def send_request_to_your_server(content):
    url = "your url key"

    headers = {
        "Authorization": " ",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "",
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        "max_tokens": 10000,
        "temperature": 0.7,
        "top_p": 1,
        "top_k": 50,
        "frequency_penalty": 0,
        "stream": False  # ⚡暂时关掉stream，直接拿完整返回；后续如果想流式再开
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=3000)

        if response.status_code == 200:
            if response.text.strip() == '':
                print(" 服务器返回了空白内容，无法解析")
                return ""
            try:
                data = response.json()
                if 'choices' in data:
                    return data["choices"][0]["message"]["content"]
                else:
                    print(f" 服务器返回了异常结构：{data}")
                    return ""
            except Exception as e:
                print(f" JSON解析失败: {str(e)}")
                print(f" 原始返回内容是：{response.text}")
                return ""
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(response.text)
            return ""
    except Exception as e:
        print(f" 请求过程中异常：{str(e)}")
        return ""


# 解析返回的JSON数据
import json
import re

def save_to_file(output_file, content):
    """保存内容到文件"""
    try:
        with open(output_file, 'a', encoding='utf-8') as file:
            file.write(content + '\n')
    except Exception as e:
        print(f" 保存到文件失败: {str(e)}")


def parse_json(text, output_file):
    try:
        # 尝试提取完整的 JSON 数组（考虑到可能包含嵌套数组）
        match = re.search(r'\[(.*?)\]', text, re.DOTALL)
        if match:
            json_text = match.group(1)  # 提取匹配到的文本
            try:
                data = json.loads(json_text)
                if isinstance(data, list):
                    return data
                else:
                    print(" 解析后不是列表格式！")
                    save_to_file(output_file, json_text)
                    return []
            except json.JSONDecodeError as e:
                error_message = f"{json_text}"
                # 保存错误信息到文件
                save_to_file(output_file, error_message)
                return []
        else:
            error_message = " 没找到合法的列表结构！"
            print(error_message)
            # 保存错误信息到文件
            save_to_file(output_file, error_message)
            return []
    except Exception as e:
        error_message = f" 解析过程中发生错误：{str(e)}"
        print(error_message)
        # 保存错误信息到文件
        save_to_file(output_file, error_message)
        return []

def extract_text_from_md(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 专门处理.pdf文件
def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
        return text
    except Exception as e:
        print(f"⚠️ 读取PDF失败: {e}")
        return ''
# 生成prompt
def return_random_prompt(content):
    system_prompt = "根据下面提供有关领域文本，请你仔细通读全文，你需要依据该文本：\n\n######\n{}######\n尽可能给出多样化的问题和对应的回答。我们将用于人工评估模型对问答对数据的完成情况。要求:\n".format(content)
    system_prompt += "1. 生成问题有价值且遵守该文本信息，回答准确专业。\n"
    system_prompt += "2. 生成问答对不能重复。\n"
    system_prompt += "3. 问题多样化，同个问题可以换成不同表述方式，但意思保持不变。\n"
    system_prompt += "4. 为问题生成作为<input>，不应该只包含简单的占位符。<input>应提供实质性的内容问题，具有挑战性。字数不超过" + str(random.randint(80, 120)) + "字。\n"
    system_prompt += "5. <output>应该是对问题的适当且真实的回答，不能只回复答应或拒绝请求。如果需要额外信息才能回复时，请努力预测用户意图并尝试回复，但不能胡编乱造。回复内容尽量描述清楚详细的内容步骤，不要输出参考相关章节的规定，需要具体可落实的方法<output>的内容应少于" + str(random.randint(512, 1024)) + "字。\n\n"
    system_prompt += "请生成60条满足上述条件的JSON格式数据，严格遵守JSON格式，包括每个标点符号和括号。每条数据必须是一个JSON对象，并且每个对象包含 'input' 和 'output' 字段，且不包含多余的字符和符号。数据应以列表的形式呈现，每个元素是一个独立的JSON对象，不需要额外回复文字内容。请确保生成的数据符合JSON格式并且无遗漏，且每个JSON对象之间没有额外的字符或格式错误。返回数据应如下所示：\n"
    system_prompt += '[\n    {\n        "input": "问题1",\n        "output": "答案1"\n    },\n    {\n        "input": "问题2",\n        "output": "答案2"\n    }\n]\n'
    return system_prompt


# 通用的遍历目录并处理文件
def list_files_and_generate_QA(directory):
    # 获取当前时间，作为文件名的一部分
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        if os.path.isfile(file_path):
            start = time.time()
            print("正在处理文件:", filename)
            print("前三个字符:", filename[:3])
            print()

            ext = os.path.splitext(filename)[1].lower()
            content = ""

            if ext == '.md':
                content = extract_text_from_md(file_path)
            elif ext == '.pdf':
                content = extract_text_from_pdf(file_path)
            else:
                print(f" 文件类型 {ext} 不支持，跳过。")
                continue

            if not content.strip():
                print("⚠ 提取到的内容为空，跳过。")
                continue

            MAX_LEN = 20000
            print(f"提取到的原始文本长度：{len(content)} 字符")
            if len(content) > MAX_LEN:
                print(f"内容过长，截断到前 {MAX_LEN} 字符")
                content = content[:MAX_LEN]

            # 生成输出文件路径，并加入当前时间戳
            input_file = file_path
            output_file = os.path.join(directory, f"{filename[:5]}-{current_time}.jsonl")

            print("输入文件: ", input_file)
            print("输出文件: ", output_file)

            MAX_EPOCHS = 3  # 每个文件请求几次

            for k in range(MAX_EPOCHS):
                now = time.time()
                prompt = return_random_prompt(content)
                result = send_request_to_your_server(prompt)
                if not result:
                    continue
                print("模型返回结果：", result)

                # 处理解析结果并保存到文件
                output = parse_json(result, output_file)
                if output:
                    print(output)
                    with open(output_file, 'a', encoding='utf-8') as file:
                        for i in output:
                            json_str = json.dumps(i, ensure_ascii=False)
                            file.write(json_str + ","+'\n')
                    print("处理完成，用时", time.time() - now, "秒")
                    print("-" * 60)

            print("处理完成，用时", time.time() - start, "秒")
            print("-" * 60)

if __name__ == "__main__":
    # 直接写死路径，不用命令行传参
    folder_path = './test2'

    list_files_and_generate_QA(folder_path)

