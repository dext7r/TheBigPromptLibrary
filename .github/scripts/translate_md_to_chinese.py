#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import json
import requests
import argparse
import re
from pathlib import Path
from tqdm import tqdm
import time

def split_markdown_by_headers(text, max_tokens=4000):
    """
    按照Markdown标题分割文本为多个部分，确保每部分不超过最大令牌数
    """
    # 按照标题分割
    header_pattern = r'^#{1,6}\s+.*$'
    parts = []
    current_part = ""
    lines = text.split('\n')
    
    for line in lines:
        # 如果是标题并且当前部分已经足够长，开始新部分
        if re.match(header_pattern, line, re.MULTILINE) and len(current_part) > max_tokens:
            if current_part:
                parts.append(current_part)
            current_part = line + '\n'
        else:
            current_part += line + '\n'
    
    # 添加最后一部分
    if current_part:
        parts.append(current_part)
    
    # 进一步分割过长的部分
    result = []
    for part in parts:
        if len(part) > max_tokens:
            # 如果部分仍然太长，按段落分割
            paragraphs = re.split(r'\n\s*\n', part)
            temp_part = ""
            for para in paragraphs:
                if len(temp_part) + len(para) + 2 > max_tokens:
                    result.append(temp_part)
                    temp_part = para + "\n\n"
                else:
                    temp_part += para + "\n\n"
            if temp_part:
                result.append(temp_part)
        else:
            result.append(part)
    
    return result

def translate_text(text, api_url, api_key, model="claude-3-7-sonnet-latest", language="中文", max_retries=3, retry_delay=2):
    """使用大模型API将文本翻译成指定语言"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": f"你是一位专业的翻译专家，请将以下Markdown内容翻译成{language}。保持原有的Markdown格式，只翻译文本内容。代码块内的内容和URL不需要翻译。"},
            {"role": "user", "content": text}
        ],
        "temperature": 0.3
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"API调用出错 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                print("达到最大重试次数，放弃请求")
                return None

def translate_long_text(text, api_url, api_key, model="claude-3-7-sonnet-latest", language="中文", max_tokens=4000):
    """处理长文本，将其分割成多个部分进行翻译，然后合并结果"""
    if len(text) <= max_tokens:
        return translate_text(text, api_url, api_key, model, language)
    
    # 分割文本
    parts = split_markdown_by_headers(text, max_tokens)
    print(f"文本已分割为 {len(parts)} 个部分进行翻译")
    
    # 翻译每个部分
    translated_parts = []
    for i, part in enumerate(tqdm(parts, desc="分批翻译进度")):
        print(f"翻译第 {i+1}/{len(parts)} 部分 (长度: {len(part)}字符)")
        translated = translate_text(part, api_url, api_key, model, language)
        if translated:
            translated_parts.append(translated)
        else:
            # 如果翻译失败，保留原文
            print(f"第 {i+1} 部分翻译失败，保留原文")
            translated_parts.append(part)
        
        # 添加延迟以避免API限制
        if i < len(parts) - 1:
            time.sleep(1)
    
    # 合并结果
    return "\n".join(translated_parts)

def process_file(file_path, api_url, api_key, model, language="中文", output_dir=None, max_tokens=4000):
    """处理单个Markdown文件"""
    print(f"正在处理文件: {file_path}")
    
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 翻译内容
        translated_content = translate_long_text(content, api_url, api_key, model, language, max_tokens)
        
        if translated_content:
            # 确定输出路径
            if output_dir:
                # 保留相对路径结构
                rel_path = os.path.relpath(file_path, '.')
                output_path = os.path.join(output_dir, rel_path)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
            else:
                output_path = file_path
            
            # 保存翻译后的内容
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            print(f"已保存翻译结果到: {output_path}")
            return True
        else:
            print(f"翻译失败: {file_path}")
            return False
    except Exception as e:
        print(f"处理文件时出错 {file_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='将Markdown文件翻译成中文')
    parser.add_argument('-i', '--input', type=str, required=True, help='输入文件或目录路径')
    parser.add_argument('-o', '--output', type=str, help='输出目录路径（默认覆盖原文件）')
    parser.add_argument('--openai-url', type=str, required=True, help='OpenAI API URL')
    parser.add_argument('--api-key', type=str, required=True, help='OpenAI API Key')
    parser.add_argument('--model', type=str, default='claude-3-7-sonnet-latest', help='使用的模型')
    parser.add_argument('--recursive', action='store_true', help='递归处理目录中的所有文件')
    parser.add_argument('--max-tokens', type=int, default=4000, help='每批次的最大令牌数')
    parser.add_argument('-l', '--language', type=str, default='中文', help='目标语言（默认：中文）')
    
    args = parser.parse_args()
    
    # 获取所有Markdown文件
    if os.path.isfile(args.input) and args.input.endswith('.md'):
        md_files = [args.input]
    elif os.path.isdir(args.input):
        if args.recursive:
            md_files = glob.glob(os.path.join(args.input, '**', '*.md'), recursive=True)
        else:
            md_files = glob.glob(os.path.join(args.input, '*.md'))
    else:
        print(f"错误: 输入 '{args.input}' 不是Markdown文件或目录")
        return
    
    if not md_files:
        print(f"未找到任何Markdown文件")
        return
    
    print(f"找到 {len(md_files)} 个Markdown文件")
    
    # 处理每个文件
    success_count = 0
    for file_path in tqdm(md_files, desc="总体翻译进度"):
        if process_file(file_path, args.openai_url, args.api_key, args.model, args.language, args.output, args.max_tokens):
            success_count += 1
    
    print(f"翻译完成! 成功: {success_count}/{len(md_files)}")

if __name__ == "__main__":
    main() 
