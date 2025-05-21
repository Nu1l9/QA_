# -*- coding: utf-8 -*-
# @Author: Gaoyongjie
# @Date:  2025-05-21 14:00:00
# @Last Modified by: GYJ
# @Last Modified time: 2025-05-21 14:00:00

"""
根据指定问题，直接调用大模型去返回问题的答案，保存为jsonl
"""

# coding:utf-8
import os
import json
import requests
from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI


current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")

def send_request_to_your_server(content):
    client = OpenAI(
        base_url="your url here",
        api_key="your api key here",
    )

    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Site URL for rankings on openrouter.ai.
            "X-Title": "<YOUR_SITE_NAME>",  # Optional. Site title for rankings on openrouter.ai.
        },
        extra_body={},
        model="google/gemini-2.5-flash-preview",
        messages=[
            {"role": "system", "content": "您是一个专业的可控核聚变和人工智能专家。根据输入文本的语言和背景，生成高度专业和技术性的问题与回答对，专注于可控核聚变的研究，特别针对高级教育目的。问题应聚焦于核聚变的关键方面或挑战，如等离子体约束、能量效率、托卡马克设计等，涵盖领域中的基本问题，同时也涉及正在进行的研究和实验努力。确保问题具体并深入探讨该领域的核心问题，同时也涵盖最新的发展、理论和实验成果，逐步解释关键概念。如果输入文本是中文，生成的问题和答案应为中文；如果是英文，则生成英文的问题和答案。您需要尽可能的从以下几个方面对问题进行回答：1.问题的背景介绍。2. 名词定义与实例分析3. 多角度推理与替代解答探索 4. 实际案例与现实应用验证 5. 总结与互动式引导。多层次背景分析与局限性提示在解答任何问题之前，首先进行背景知识的多层次分析，确保用户能够理解相关领域的基本概念。特别是在涉及复杂问题时，如人工智能和核聚变，提供清晰的基础解释是非常重要的。同时，我将明确指出我作为大型语言模型的局限性，例如不能访问实时数据、无法进行实际实验等。名词定义与实例分析对问题中的关键术语逐一进行详细定义，并用具体的实例或应用场景帮助用户理解。这不仅仅是对术语的字面解释，还要通过实例展示这些术语在现实世界中的应用。例如，如果问题涉及“等离子体约束”，你需要详细解释等离子体约束的物理原理，并结合托卡马克等实验设备来展示这一概念。多角度推理与替代解答探索在面对用户的具体问题时，你需要采取至少三种不同的方法来进行推理，从多个角度进行分析。通过这样全面的探讨，你需要确保从不同的技术路径或理论框架中得出结论，并能够提供多种可行的解决方案。如果某个推理过程存在漏洞或错误，你需要立即识别并进行反思，采用另一种方法进行修正。你需要对所有可能的解答路径进行测试和验证，充分考虑它们的优势与局限性，确保提供的信息是准确且经过深思熟虑的。例如，如果问题是关于人工智能如何协助核聚变，你需要分别从不同的技术路径（如强化学习、神经网络和专家系统）进行分析，并在每个方案中提出潜在的挑战和改进方法。实际案例与现实应用验证基于理论分析，你需要结合现实中的案例或实验项目，帮助用户理解这些技术如何在实际中得到应用。通过分析已知的科研项目或工业应用，展示这些方法的有效性和实际效果。如果现实中存在类似的成功案例，我将提供这些案例作为参考，并探讨其应用的前景与挑战。总结与互动式引导在回答的最后，你需要总结主要的技术分析和解答，帮助用户理解问题的核心要点。除了总结外，你需要邀请用户进一步提问或讨论，从而建立一种持续的互动关系，确保用户能够在理解过程中得到更多的支持和帮助。重要提示：你需要特别注意在每一步推理过程中指出可能的局限性，保持透明和诚实，避免给出过于绝对的结论。同时，鼓励用户在不确定的情况下寻求更多的信息或进行实际实验验证，如果问题是中文，回答也应该是中文."},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": content
                    },
                ]
            }
        ]
    )
    return completion.choices[0].message.content

def extract_inputs_from_jsonl(file_path):
    inputs = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line.strip())
                if "input" in item:
                    inputs.append(item["input"])
            except json.JSONDecodeError:
                continue
    return inputs[:5]

def ask_and_collect(input_text):
    output_text = send_request_to_your_server(input_text)
    return {"input": input_text, "output": output_text} if output_text else None

def process_questions_parallel(question_file, output_file, max_workers=8):
    questions = extract_inputs_from_jsonl(question_file)
    print(f"共载入问题数：{len(questions)}")

    with open(output_file, 'w', encoding='utf-8') as f_out:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(ask_and_collect, q): q for q in questions}
            for future in tqdm(as_completed(futures), total=len(futures), desc=" 正在生成回答"):
                res = future.result()
                if res:
                    f_out.write(json.dumps(res, ensure_ascii=False) + '\n')

    print(f"\n 所有回答完成，保存于: {output_file}")

if __name__ == "__main__":
    question_file = r"D:\supie-work\model-test\QA-2025-05-15_09-28-38.jsonl"
    output_file = f"./QA-{current_time}.jsonl"
    process_questions_parallel(question_file, output_file, max_workers= 16)
