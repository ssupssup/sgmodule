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

PROXY_PROTECT_KEYWORDS = [
    # 搜索引擎与基础设施 API
    "google", "googleapis", "gstatic", "googleusercontent", "ggpht",
    # AI 平台
    "openai", "chatgpt", "oaistatic", "oaiusercontent", "claude", "anthropic", "gemini", "grok", "perplexity",
    # 视频与流媒体
    "youtube", "googlevideo", "ytimg", "netflix", "hbo", "disney", "spotify", "hulu", "twitch",
    # 社交与通讯
    "twitter", "x.com", "facebook", "instagram", "telegram", "discord", "line", "whatsapp", "pixiv",
    # 开发者与代码
    "github", "githubusercontent", "gist", "medium", "wikipedia"
]

# 常见二级域名后缀 SLD 清单 (防止将 edu.cn 或 com.cn 错误合并)
SLD_SUFFIXES = {".com.cn", ".net.cn", ".org.cn", ".gov.cn", ".edu.cn", ".co.uk", ".com.tw", ".com.hk", ".co.jp"}

def extract_root_domain(domain):
    """主根域名强力折叠算法：将 ap-southeast-1.myhuaweicloud.com 归并为 myhuaweicloud.com"""
    for sfx in SLD_SUFFIXES:
        if domain.endswith(sfx):
            prefix = domain[:-len(sfx)]
            parts = prefix.split(".")
            if parts:
                return parts[-1] + sfx
            return domain
    parts = domain.split(".")
    if len(parts) >= 2:
        return parts[-2] + "." + parts[-1]
    return domain

def load_custom_override_rules():
    remove_set = set()
    disable_set = set()
    prepend_proxy_rules = []
    prepend_direct_rules = []
    
    if not os.path.exists(CUSTOM_RULES_FILE):
        print(f"⚠️ 自定义规则文件未找到: {CUSTOM_RULES_FILE}，将按默认规则处理。")
        return remove_set, disable_set, prepend_proxy_rules, prepend_direct_rules

    print(f"📖 正在读取自定义规则文件: {CUSTOM_RULES_FILE}...")
    with open(CUSTOM_RULES_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            if stripped.startswith("REMOVE,"):
                target_rule = stripped[7:].strip()
                remove_set.add(target_rule)
            elif stripped.startswith("DISABLE,"):
                target_rule = stripped[8:].strip()
                disable_set.add(target_rule)
            elif stripped.startswith("PREPEND_PROXY,"):
                target_rule = stripped[14:].strip()
                prepend_proxy_rules.append(target_rule)
            elif stripped.startswith("PREPEND_DIRECT,"):
                target_rule = stripped[15:].strip()
                prepend_direct_rules.append(target_rule)
                
    print(f"✅ 自定义规则解析完成: 物理擦除 {len(remove_set)} 条 | 原位注释 {len(disable_set)} 条 | 强代理 {len(prepend_proxy_rules)} 条 | 强直连 {len(prepend_direct_rules)} 条")
    return remove_set, disable_set, prepend_proxy_rules, prepend_direct_rules

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

def fetch_and_clean_china_direct_rules(existing_top500_rules):
    import urllib.request
    china_rules = []
    url = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/China/China_Domain.list"
    
    # 1. 提取 Top500 中已有的全量域名 (包含 Proxy 和 Direct)，遵循 Top500 绝对优先法则
    top500_domains = set()
    for line in existing_top500_rules:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = [p.strip() for p in stripped.split(',')]
        if len(parts) >= 2 and parts[0] in ["DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"]:
            dom = parts[1].lower().split('#')[0].strip()
            if dom:
                top500_domains.add(dom)

    print(f"📊 Top500 提取出已知权威域名基线: {len(top500_domains)} 个")

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            lines = resp.read().decode('utf-8').splitlines()
            
            raw_domains = []
            for l in lines:
                stripped = l.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if stripped.startswith("."):
                    stripped = stripped[1:]
                domain_lower = stripped.lower()
                
                # 2. 防误杀黑名单物理过滤：丢弃任何包含代理/敏感关键字的域名
                if any(kw in domain_lower for kw in PROXY_PROTECT_KEYWORDS):
                    continue
                
                raw_domains.append(domain_lower)

            # 3. 实施主根域名强力归并折叠 (如 ap-southeast-1.myhuaweicloud.com -> myhuaweicloud.com)
            folded_roots = set()
            for d in raw_domains:
                root = extract_root_domain(d)
                folded_roots.add(root)

            # 4. Top500 绝对优先法则：只要 Top500 里已经有了 (无论是 Proxy 还是 Direct)，一律采用 Top500，直接丢弃
            for domain in sorted(list(folded_roots)):
                if domain in top500_domains:
                    continue
                
                is_subdomain_covered = False
                for top_dom in top500_domains:
                    if domain.endswith("." + top_dom):
                        is_subdomain_covered = True
                        break
                if is_subdomain_covered:
                    continue

                china_rules.append(f"DOMAIN-SUFFIX,{domain},Direct")
    except Exception as e:
        print(f"⚠️ 抓取 BlackMatrix7 China_Domain.list 失败: {e}")
        
    china_rules = list(dict.fromkeys(china_rules))
    print(f"✅ 成功清洗 China_Domain 并完成主根强力归并与 Top500 优先去重，得出 {len(china_rules)} 条精炼纯净的中国域名直连规则。")
    return china_rules

def process_and_align_conf(lines, remove_set, disable_set, prepend_proxy_rules, prepend_direct_rules):
    aligned_lines = []
    seen_conf_domains = set()
    now_str = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    
    injected_custom_rules = False
    china_direct_rules = fetch_and_clean_china_direct_rules(lines)
    
    for l in lines:
        stripped = l.strip()
        
        # 0. 动态擦除自定义规则文件中标记为 REMOVE 的上游坏行
        if stripped in remove_set:
            print(f"✂️ 成功物理擦除上游坏行: {stripped}")
            continue

        # 0.1 动态将自定义规则文件中标记为 DISABLE 的坏行原位注释化禁用
        if stripped in disable_set:
            print(f"🚫 成功原位注释化禁用上游坏行: {stripped}")
            aligned_lines.append(f"# 🚫 [已禁用-由顶层Direct覆盖] {l}")
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
                
        # 4. 在 GEOIP,CN,DIRECT 前注入经 Python 在线清洗+Top500去重后的 Loyalsoldier 中国域名直连规则段
        if stripped == "GEOIP,CN,DIRECT":
            aligned_lines.append("# === 🇨🇳 经 Python 脚本在线清洗+Top500去重后的 Loyalsoldier 中国域名直连区 ===")
            for cr in china_direct_rules:
                aligned_lines.append(cr)
            aligned_lines.append("")
            aligned_lines.append(l)
            continue

        # 5. 全局 Top500 原版物理防重滤镜：彻底消除上游 Top500 文件自带的冲突重复行 (如 Line 531 Proxy 与 Line 568 Direct 冲突)
        if stripped and not stripped.startswith("#"):
            parts = [p.strip() for p in stripped.split(',')]
            if len(parts) >= 2 and parts[0] in ["DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"]:
                dom_key = parts[1].lower().split('#')[0].strip()
                if dom_key in seen_conf_domains:
                    print(f"✂️ 成功清理 Top500 原版自带冲突行: {stripped}")
                    continue
                seen_conf_domains.add(dom_key)

        aligned_lines.append(l)
        
    final_content = "\n".join(aligned_lines)
    return final_content

def main():
    remove_set, disable_set, prepend_proxy_rules, prepend_direct_rules = load_custom_override_rules()
    raw_lines = fetch_top500_rules()
    conf_str = process_and_align_conf(raw_lines, remove_set, disable_set, prepend_proxy_rules, prepend_direct_rules)
    
    os.makedirs(os.path.dirname(OUTPUT_CONF), exist_ok=True)
    with open(OUTPUT_CONF, 'w', encoding='utf-8') as f:
        f.write(conf_str)
        
    line_count = len(conf_str.splitlines())
    print(f"🎉 成功生成带有动态构建时间戳与自定义规则融合的纯净配置文件 {OUTPUT_CONF}！")
    print(f"📈 统计数据: 物理总行数 {line_count} 行 | 100% 匹配次序与擦除/注释策略已物理落地！")

if __name__ == "__main__":
    main()

