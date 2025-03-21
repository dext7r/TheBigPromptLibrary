#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import json
import requests
import argparse
import re
import subprocess
from pathlib import Path
from tqdm import tqdm
import time

# 翻译日志路径
TRANSLATION_LOG_FILE = "translation_log.json"

def get_file_from_main_branch(file_path):
    """获取main分支上的文件内容"""
    try:
        # 首先检查git命令是否可用
        check_git = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if check_git.returncode != 0:
            print("警告: 无法执行git命令，跳过与main分支的比较")
            return None
            
        # 检查当前是否在git仓库中
        check_repo = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if check_repo.returncode != 0:
            print("警告: 当前目录不是git仓库，跳过与main分支的比较")
            return None
            
        # 检查main分支是否存在
        check_main = subprocess.run(
            ["git", "rev-parse", "--verify", "main"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if check_main.returncode != 0:
            print("警告: main分支不存在，尝试检查master分支")
            # 尝试master分支
            check_master = subprocess.run(
                ["git", "rev-parse", "--verify", "master"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if check_master.returncode == 0:
                branch = "master"
            else:
                print("警告: 无法找到main或master分支，跳过比较")
                return None
        else:
            branch = "main"
            
        # 获取文件内容
        result = subprocess.run(
            ["git", "show", f"{branch}:{file_path}"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"警告: 无法获取{branch}分支上的文件内容: {file_path}")
            if "fatal: path" in result.stderr and "does not exist" in result.stderr:
                print(f"文件在{branch}分支上不存在")
            else:
                print(f"错误信息: {result.stderr}")
            return None
    except Exception as e:
        print(f"获取main分支文件内容时出错: {e}")
        return None

def is_file_already_translated(file_path):
    """检查文件是否已经被翻译过"""
    if not os.path.exists(TRANSLATION_LOG_FILE):
        return False
    
    try:
        with open(TRANSLATION_LOG_FILE, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
            
        file_log = log_data.get(file_path, {})
        # 获取文件的最后修改时间
        last_modified = os.path.getmtime(file_path)
        
        # 如果文件在翻译后修改过，需要重新翻译
        if 'last_translated' in file_log and 'last_modified' in file_log:
            return file_log['last_modified'] >= last_modified
            
        return False
    except Exception as e:
        print(f"检查翻译日志时出错: {e}")
        return False

def update_translation_log(file_path, success=True):
    """更新翻译日志"""
    try:
        log_data = {}
        if os.path.exists(TRANSLATION_LOG_FILE):
            with open(TRANSLATION_LOG_FILE, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        
        log_data[file_path] = {
            'last_translated': time.time(),
            'last_modified': os.path.getmtime(file_path),
            'success': success
        }
        
        with open(TRANSLATION_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"更新翻译日志时出错: {e}")

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
            {"role": "system", "content": f"请将以下Markdown内容翻译成{language}。保持原有的Markdown格式，只翻译文本内容。代码块内的内容和URL不需要翻译。"},
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

def process_file(file_path, api_url, api_key, model, language="中文", output_dir=None, max_tokens=4000, force=False):
    """处理单个Markdown文件"""
    print(f"正在处理文件: {file_path}")
    
    # 检查文件是否需要翻译
    if not force:
        # 检查文件是否已翻译
        if is_file_already_translated(file_path):
            print(f"文件已翻译过，跳过: {file_path}")
            return True
            
        # 获取main分支上的文件内容
        main_content = get_file_from_main_branch(file_path)
        
        # 读取当前文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
                
            # 如果与main分支内容相同，需要翻译
            if main_content is not None and main_content == current_content:
                print(f"文件与主分支内容相同，需要翻译: {file_path}")
            else:
                # 内容不同，检查是否为已翻译文件
                if main_content is not None:
                    print(f"文件与主分支内容不同，可能已翻译，跳过: {file_path}")
                    update_translation_log(file_path, success=True)
                    return True
        except Exception as e:
            print(f"读取文件内容时出错: {e}")
            return False
    else:
        print(f"强制模式: 不检查文件状态，直接翻译: {file_path}")
    
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
            
            # 更新翻译日志
            update_translation_log(file_path, success=True)
            return True
        else:
            print(f"翻译失败: {file_path}")
            update_translation_log(file_path, success=False)
            return False
    except Exception as e:
        print(f"处理文件时出错 {file_path}: {e}")
        update_translation_log(file_path, success=False)
        return False

def test_api_connection(api_url, api_key, model, language="中文"):
    """测试API连接和响应情况"""
    print(f"正在测试API连接: {api_url}")
    print(f"使用模型: {model}")
    print(f"目标语言: {language}")
    
    # 创建一个简单的测试文本
    test_text = "这是一个API测试。This is an API test."
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": f"请将以下文本翻译成{language}，保持原文的格式和风格。"},
            {"role": "user", "content": test_text}
        ],
        "temperature": 0.3
    }
    
    try:
        print("发送测试请求...")
        response = requests.post(api_url, headers=headers, json=data)
        print(f"API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("API连接成功!")
            result = response.json()
            print("\n响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if 'choices' in result and len(result['choices']) > 0:
                translation = result['choices'][0]['message']['content']
                print(f"\n翻译结果示例: {translation}")
                return True
            else:
                print("警告: 响应中没有找到翻译内容")
                return False
        else:
            print(f"错误: API返回非200状态码")
            print(f"响应内容: {response.text}")
            return False
    except Exception as e:
        print(f"测试API连接时出错: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='将Markdown文件翻译成中文')
    parser.add_argument('-i', '--input', type=str, help='输入文件或目录路径')
    parser.add_argument('-o', '--output', type=str, help='输出目录路径（默认覆盖原文件）')
    parser.add_argument('--openai-url', type=str, required=True, help='OpenAI API URL')
    parser.add_argument('--api-key', type=str, required=True, help='OpenAI API Key')
    parser.add_argument('--model', type=str, default='claude-3-7-sonnet-latest', help='使用的模型')
    parser.add_argument('--recursive', action='store_true', help='递归处理目录中的所有文件')
    parser.add_argument('--max-tokens', type=int, default=4000, help='每批次的最大令牌数')
    parser.add_argument('-l', '--language', type=str, default='中文', help='目标语言（默认：中文）')
    parser.add_argument('--test', action='store_true', help='只测试API连接，不执行翻译')
    parser.add_argument('--force', action='store_true', help='强制执行翻译，即使文件已翻译过')
    parser.add_argument('--no-git-check', action='store_true', help='不检查git仓库中的原始文件')
    parser.add_argument('--log-file', type=str, default=TRANSLATION_LOG_FILE, help='指定翻译日志文件路径')
    
    args = parser.parse_args()
    
    # 更新日志文件路径
    global TRANSLATION_LOG_FILE
    TRANSLATION_LOG_FILE = args.log_file
    
    # 先测试API连接
    if args.test:
        print("\n===== API连接测试 =====")
        test_result = test_api_connection(args.openai_url, args.api_key, args.model, args.language)
        # 在测试模式下，根据API测试结果设置退出码
        if not test_result:
            print("API测试失败")
            exit(1)
        else:
            print("API测试成功")
            exit(0)
        return

    # 检测是否在GitHub Actions环境中运行
    is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
    
    # 检查必要参数
    if not args.input:
        print("错误: 在翻译模式下，必须提供输入文件或目录路径 (-i/--input)")
        exit(1)
    
    # 在正式翻译前进行API测试
    print("\n===== API连接测试 =====")
    if not test_api_connection(args.openai_url, args.api_key, args.model, args.language):
        print("API测试失败")
        # 如果不是强制执行且不在GitHub Actions环境中，询问用户是否继续
        if not args.force and not is_github_actions:
            confirm = input("API测试失败，是否继续? 输入 'y' 继续，其他任意键退出: ")
            if confirm.lower() != 'y':
                print("已取消翻译任务")
                exit(1)
        elif not args.force and is_github_actions:
            print("在GitHub Actions环境中检测到API测试失败，取消翻译任务")
            exit(1)
        else:
            print("强制执行翻译任务，忽略API测试失败")
    
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
        if process_file(file_path, args.openai_url, args.api_key, args.model, args.language, args.output, args.max_tokens, args.force):
            success_count += 1
    
    print(f"翻译完成! 成功: {success_count}/{len(md_files)}")
    print(f"翻译日志已保存到: {TRANSLATION_LOG_FILE}")

if __name__ == "__main__":
    main() 
