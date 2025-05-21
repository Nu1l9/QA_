# -*- coding: utf-8 -*-
# @Author: Gaoyongjie
# @Date:  2025-05-21 14:00:00
# @Last Modified by: GYJ
# @Last Modified time: 2025-05-21 14:00:00

"""
根据不同板块，提取实验数据，并进行对比分析和总结概括
"""
import os
import json
import requests
from datetime import datetime

# 实验报告存储的基础目录，每个时间阶段的报告存放在其子目录中
REPORTS_BASE_DIR = "./experiment_reports"

# 定义实验报告的标准板块（章节）名称
REPORT_SECTIONS = [
    "板块1",
    "板块2",
    "板块3",
    "板块4",
]

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
OUTPUT_FILE = os.path.join("experimental_analysis_qa", f"-{current_time}.json")  # 输出的JSON文件名

def send_request_to_your_server(content):
    url = "url"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "model": " ",
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        "max_tokens": 7500,
        "temperature": 0.8,
        "top_p": 1,
        "top_k": 50,
        "frequency_penalty": 0,
        "stream": False
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
                print(f"JSON解析失败: {str(e)}")
                print(f" 原始返回内容是：{response.text}")
                return ""
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(response.text)
            return ""
    except Exception as e:
        print(f" 请求过程中异常：{str(e)}")
        return ""

from docx import Document

def extract_reports_by_stage(base_dir: str) -> dict:
    reports = {}  # 初始化一个空字典来存储报告
    if not os.path.exists(base_dir):
        print(f"错误: 基础目录 '{base_dir}' 未找到。")
        return reports

    print(f"基础目录 '{base_dir}' 已找到。正在检查报告文件...")

    # 遍历基础目录下的所有条目，检查是否是 .docx 文件
    for fname in os.listdir(base_dir):
        file_path = os.path.join(base_dir, fname)
        if os.path.isfile(file_path) and fname.lower().endswith(".docx"):  # 查找 .docx 文件
            try:
                # 使用 python-docx 打开 .docx 文件并提取文本
                doc = Document(file_path)
                full_text = ""
                for para in doc.paragraphs:
                    full_text += para.text + "\n"  # 每个段落后加上换行符
                reports[fname] = full_text
                print(f"成功提取报告文件: {fname}")
            except Exception as e:
                print(f"读取报告文件 {file_path} 时出错: {e}")
    return reports

def summarize_section_with_llm(section_title: str, report_content: str) -> str:
    """使用LLM总结给定的板块内容。"""
    if not report_content.strip():  # 检查板块内容是否为空或仅包含空白
        return "板块内容为空或缺失。"

    # 构建用于总结的提示
    prompt = f"""请对以下标题为“{section_title}”的实验报告板块提供一个简洁的总结：

    ---
    {report_content}
    ---

    请专注于该特定板块中提出的关键发现、方法或结论。
    总结应客观并准确反映内容。
    """
    summary = send_request_to_your_server(prompt)
    return summary if summary else "未能总结该板块。"  # 返回总结内容，如果失败则返回提示信息

def generate_comparative_analysis(section_title: str, stage_summaries: dict) -> str:
    """
    为特定板块在不同阶段之间生成对比分析。
    stage_summaries: {"stage_name": "summary_content"}
    """
    if not stage_summaries or len(stage_summaries) < 2:
        items = list(stage_summaries.items())  # 获取阶段总结的条目
        if items:
            return f"板块“{section_title}”仅找到一个阶段（“{items[0][0]}”）的数据。总结：{items[0][1]}"
        return f"板块“{section_title}”没有足够的数据（或无数据）进行对比。"

    # 构建用于对比分析的提示
    prompt_parts = [f"以下是实验报告中“{section_title}”板块在不同时间阶段的总结："]

    for stage, summary in stage_summaries.items():
        prompt_parts.append(f"\n--- 阶段: {stage} 的总结 ---\n{summary}")

    prompt_parts.append(f"\n--- 分析任务 ---\n请对这些阶段中“{section_title}”板块的内容进行详细的对比分析。")
    prompt_parts.append("请重点突出以下方面：")
    prompt_parts.append("- 随着时间的推移，在发现、方法、目标或结论方面的关键变化或演进。")
    prompt_parts.append("- 任何显著的趋势（例如，改进、退步、焦点转移）。")
    prompt_parts.append("- 该板块在不同阶段之间的一致性或差异性。")
    prompt_parts.append("- 如果可以从总结中推断，请说明观察到的变化的潜在原因。")
    prompt_parts.append("\n请清晰、简洁地呈现您的分析。专注于提供一个“横向对比”，综合所有提供阶段中该特定板块的见解。")

    prompt = "\n".join(prompt_parts)
    analysis = send_request_to_your_server(prompt)
    return analysis if analysis else f"未能为板块“{section_title}”生成对比分析。"

def main_agent():
    """协调整个处理流程。"""

    print(f"\n步骤 1: 从 '{REPORTS_BASE_DIR}' 提取报告...")
    raw_reports_by_stage = extract_reports_by_stage(REPORTS_BASE_DIR)  # 提取各个阶段的原始报告
    if not raw_reports_by_stage:  # 如果没有找到报告
        print("未找到报告或基础目录为空。正在退出。")
        return

    print(f"\n找到以下阶段的报告: {list(raw_reports_by_stage.keys())}")

    # 用于存储所有已处理数据的结构:
    processed_data = {}

    print("\n步骤 2: 总结每个报告的板块内容...")
    for stage, report_content in raw_reports_by_stage.items():
        print(f"\n正在处理阶段: {stage}")
        processed_data[stage] = {}  # 为当前阶段创建条目

        for section_title in REPORT_SECTIONS:  # 遍历所有板块标题
            print(f"  正在总结阶段 '{stage}' 的板块: '{section_title}'...")

            # 调用LLM总结该板块内容
            summary = summarize_section_with_llm(section_title, report_content)

            processed_data[stage][section_title] = {
                "summary": summary
            }
            print(f"    板块 '{section_title}' 的总结: {'完成' if summary else '失败或为空'}")

    print("\n步骤 3: 为每个板块在不同阶段之间生成对比分析...")
    final_qa_pairs = []

    for section_title in REPORT_SECTIONS:  # 遍历每个板块标题
        print(f"\n正在为板块 '{section_title}' 生成分析...")

        # 收集该板块在所有阶段的总结
        summaries_for_section_across_stages = {}
        for stage, stage_data in processed_data.items():
            if section_title in stage_data:
                summaries_for_section_across_stages[stage] = stage_data[section_title]["summary"]

        if not summaries_for_section_across_stages:  # 如果没有找到该板块的总结
            print(f"  在任何阶段均未找到板块 '{section_title}' 的总结。跳过分析。")
            continue  # 跳过当前板块

        # 生成对比分析内容
        analysis_content = generate_comparative_analysis(section_title, summaries_for_section_across_stages)

        question = f"针对“{section_title}”板块在不同实验阶段的对比分析是什么？"
        final_qa_pairs.append({
            "question": question,
            "answer": analysis_content,
            "section_analyzed": section_title,
            "contributing_stages_and_summaries": summaries_for_section_across_stages
        })
        print(f"  板块 '{section_title}' 的分析: 完成")

    print(f"\n步骤 4: 将最终QA对保存到 '{OUTPUT_FILE}'...")
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_qa_pairs, f, indent=4, ensure_ascii=False)
        print(f"成功将分析保存到 {OUTPUT_FILE}")
    except Exception as e:
        print(f"保存JSON输出时出错: {e}")

    print("\n智能体处理完成。")

if __name__ == "__main__":
    main_agent()  # 执行主智能体逻辑
