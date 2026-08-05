#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_custome_conf.py
从 Johnshall Top500 抓取最新白名单规则，结合 references/custom_conf_rules.txt 中的动作规则：
1. 物理擦除 REMOVE 指定的上游误杀坏行；
2. 在 [Rule] 顶端按绝对优先次序注入 PREPEND_PROXY (强代理) 与 PREPEND_DIRECT (强直连，如 cn1.gi-de.com)；
3. 保留时间戳与 dns-server / update-url 配置，生成纯净高效的 Shadowrocket 主配置文件 custome_conf.conf。
"""

import os
import sys
import datetime
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOP500_URL = "https://johnshall.github.io/Shadowrocket-ADBlock-Rules-Forever/sr_top500_whitelist.conf"
CUSTOM_RULES_FILE = os.path.join(BASE_DIR, "references", "custom_conf_rules.txt")
OUTPUT_CONF = os.path.join(BASE_DIR, "custome_conf.conf")

def load_custom_override_rules():
    remove_set = set()
    prepend_proxy_rules = []
    prepend_direct_rules = []
    
    if not os.path.exists(CUSTOM_RULES_FILE):
        print(f"⚠️ 自定义规则文件未找到: {CUSTOM_RULES_FILE}，将按默认规则处理。")
        return remove_set, prepend_proxy_rules, prepend_direct_rules

    print(f"📖 正在读取自定义规则文件: {CUSTOM_RULES_FILE}...")
    with open(CUSTOM_RULES_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            if stripped.startswith("REMOVE,"):
                target_rule = stripped[7:].strip()
                remove_set.add(target_rule)
            elif stripped.startswith("PREPEND_PROXY,"):
                target_rule = stripped[14:].strip()
                prepend_proxy_rules.append(target_rule)
            elif stripped.startswith("PREPEND_DIRECT,"):
                target_rule = stripped[15:].strip()
                prepend_direct_rules.append(target_rule)
                
    print(f"✅ 自定义规则解析完成: 物理擦除 {len(remove_set)} 条 | 强代理 {len(prepend_proxy_rules)} 条 | 强直连 {len(prepend_direct_rules)} 条")
    return remove_set, prepend_proxy_rules, prepend_direct_rules

def fetch_top500_rules():
    print(f"📥 正在从 {TOP500_URL} 抓取最新 Top500 白名单规则...")
    req = urllib.request.Request(TOP500_URL, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8')
            lines = content.splitlines()
            print(f"✅ 成功抓取 Top500 原始文本，共 {len(lines)} 行。")
            return lines
    except Exception as e:
        print(f"⚠️ 抓取 Top500 规则失败: {e}")
        raise e

def process_and_align_conf(lines, remove_set, prepend_proxy_rules, prepend_direct_rules):
    aligned_lines = []
    now_str = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    
    injected_custom_rules = False
    
    for l in lines:
        stripped = l.strip()
        
        # 0. 动态擦除自定义规则文件中标记为 REMOVE 的上游坏行
        if stripped in remove_set:
            print(f"✂️ 成功物理擦除上游坏行: {stripped}")
            continue

        # 1. 动态替换第 3 行时间戳为当前最新构建时间，并在最顶端注入元数据描述
        if stripped.startswith("# build time:"):
            aligned_lines.insert(0, "#!name=Top500 WhiteList Conf")
            aligned_lines.insert(1, f"#!desc=最近更新: {now_str} (UTC+8) | Pure IP DoH & Top500 100% pixel aligned.")
            aligned_lines.append(f"# build time: {now_str} (UTC+8)")
            continue
            
        # 2. 精确替换第 11 行左右的 dns-server 并融入 update-url 及防擦除时间戳
        if stripped.startswith("dns-server ="):
            aligned_lines.append("# 🟢 100% 对齐 Top500 官方原版：阿里/腾讯纯 IP DoH (免 Bootstrap 延迟)")
            aligned_lines.append("dns-server = https://223.5.5.5/dns-query, https://223.6.6.6/dns-query, https://1.12.12.12/dns-query")
            aligned_lines.append("\n# === GitHub 在线一键更新地址 ===")
            aligned_lines.append("update-url = https://raw.githubusercontent.com/ssupssup/sgmodule/main/custome_conf.conf")
            aligned_lines.append("\n# === GitHub 云端真实抓取生成时间戳 (防小火箭 APP 头部擦除) ===")
            aligned_lines.append(f"# github_build_time = {now_str} (UTC+8)")
            continue

        # 3. 在 [Rule] 段落顶部位置前置按严密次序注入自定义强代理与强直连区
        if stripped == "# 手工定义的 Direct 列表" and not injected_custom_rules:
            injected_custom_rules = True
            
            if prepend_proxy_rules:
                aligned_lines.append("# === 🟢 1. 顶层最高优先级强代理区 (核心认证与 2FA/API 优先) ===")
                for r in prepend_proxy_rules:
                    aligned_lines.append(r)
                aligned_lines.append("")
                
            if prepend_direct_rules:
                aligned_lines.append("# === 🟢 2. 顶层最高优先级强直连区 (如 cn1.gi-de.com 优先直连) ===")
                for r in prepend_direct_rules:
                    aligned_lines.append(r)
                aligned_lines.append("")
                
            aligned_lines.append(l)
            continue
            
        aligned_lines.append(l)
        
    final_content = "\n".join(aligned_lines)
    return final_content

def main():
    remove_set, prepend_proxy_rules, prepend_direct_rules = load_custom_override_rules()
    raw_lines = fetch_top500_rules()
    conf_str = process_and_align_conf(raw_lines, remove_set, prepend_proxy_rules, prepend_direct_rules)
    
    os.makedirs(os.path.dirname(OUTPUT_CONF), exist_ok=True)
    with open(OUTPUT_CONF, 'w', encoding='utf-8') as f:
        f.write(conf_str)
        
    line_count = len(conf_str.splitlines())
    print(f"🎉 成功生成带有动态构建时间戳与自定义规则融合的纯净配置文件 {OUTPUT_CONF}！")
    print(f"📈 统计数据: 物理总行数 {line_count} 行 | 100% 匹配次序与擦除策略已物理落地！")

if __name__ == "__main__":
    main()
