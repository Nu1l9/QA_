# -*- coding: utf-8 -*-
# @Author: Gaoyongjie
# @Date:  2025-05-21 14:00:00
# @Last Modified by: GYJ
# @Last Modified time: 2025-05-21 14:00:00

"""
讲给定文本按照板块切分成小的板块，方便传给模型处理
"""

import re
import os
from datetime import datetime
import glob

def split_md_by_blocks(file_path, block_size):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按 # 一级标题分割
    headings = re.split(r'(^# .*)', content, flags=re.MULTILINE)

    sections = []
    for i in range(1, len(headings), 2):
        heading = headings[i].strip()
        section_content = headings[i + 1].strip() if i + 1 < len(headings) else ""
        sections.append((heading, section_content))

    # 每 block_size 个组成一个块
    blocks = [sections[i:i + block_size] for i in range(0, len(sections), block_size)]

    return blocks


def save_blocks_to_file(blocks, original_filename, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    base_filename = os.path.splitext(original_filename)[0][:4]

    for block_num, block in enumerate(blocks, start=1):
        output_filename = f"{base_filename}-{block_num}.md"
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            for heading, content in block:
                f.write(f"{heading}\n\n")
                f.write(f"{content}\n\n")
            f.write("\n" + "=" * 50 + "\n")

        print(f"已保存文件：{output_path}")

    return len(blocks)  # 返回处理块数


def process_all_md_files(input_dir, output_dir, block_size):
    md_files = glob.glob(os.path.join(input_dir, "*.md"))
    total_blocks = 0

    for file_path in md_files:
        original_filename = os.path.basename(file_path)
        blocks = split_md_by_blocks(file_path, block_size)
        block_count = save_blocks_to_file(blocks, original_filename, output_dir)

        print(f"{original_filename} 拆分为 {block_count} 个块。\n")
        total_blocks += block_count

    print(f"\n✅ 所有文件处理完毕，总共生成 {total_blocks} 个块。")


# 设置路径
input_dir = r"/data1/QA_test/arxiv_data_2k"
output_dir = r"/split_md"

# 开始处理
process_all_md_files(input_dir, output_dir, block_size=8)
