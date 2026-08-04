#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_custome_conf.py
自动抓取 Johnshall Top500 最新白名单规则，并结合纯 IP 式 DoH 加密 DNS、5G 退避防发热与手爆加白补丁，
自动生成 Shadowrocket 主配置文件 custome_conf.conf。
"""

import os
import sys
import datetime
import urllib.request

TOP500_URL = "https://johnshall.github.io/Shadowrocket-ADBlock-Rules-Forever/sr_top500_whitelist.conf"
OUTPUT_CONF = "/Users/shizupeng/Documents/antigravity/sgmodule/custome_conf.conf"

HEADER_TEMPLATE = """# =================================================================
# 📄 Shadowrocket 智能双轨 DNS 终极定制配置文件 (custome_conf.conf)
# 🕒 生成时间 (Timestamp): {timestamp} (UTC+8)
# 🛡️ 核心特性: 基于 Top500 全量 780+ 规则 + 纯 IP DoH + 0 DNS 泄露 + 白名单代理 (FINAL, PROXY)
# =================================================================

[General]
ipv6 = false
bypass-system = true
skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, fe80::/10, fc00::/7, localhost, *.local, *.lan, *.internal, e.crashlytics.com, captive.apple.com, sequoia.apple.com, seed-sequoia.siri.apple.com, *.ls.apple.com
bypass-tun = 10.0.0.0/8,100.64.0.0/10,127.0.0.0/8,169.254.0.0/16,172.16.0.0/12,192.0.0.0/24,192.0.2.0/24,192.88.99.0/24,192.168.0.0/16,198.18.0.0/15,198.51.100.0/24,203.0.113.0/24,233.252.0.0/24,224.0.0.0/4,255.255.255.255/32,::1/128,::ffff:0:0/96,::ffff:0:0:0/96,64:ff9b::/96,64:ff9b:1::/48,100::/64,2001::/32,2001:20::/28,2001:db8::/32,2002::/16,3fff::/20,5f00::/16,fc00::/7,fe80::/10,ff00::/8

# 🟢 国内直连加密 DNS (纯 IP 形式，免去 DoH 域名 Bootstrap 延迟，5G 下 0 秒秒开)
direct-dns-server = https://223.5.5.5/dns-query, https://223.6.6.6/dns-query, https://1.12.12.12/dns-query

# 🌐 海外代理加密 DNS & Fallback (纯 IP 形式，远端代理解析，彻底杜绝本地 DNS 泄露)
dns-server = https://1.1.1.1/dns-query, https://8.8.8.8/dns-query
fallback-dns-server = https://1.1.1.1/dns-query, https://8.8.8.8/dns-query

update-url = https://raw.githubusercontent.com/ssupssup/sgmodule/main/custome_conf.conf

icmp-auto-reply = true
always-reject-url-rewrite = false
private-ip-answer = true

[Rule]
"""

FOOTER_TEMPLATE = """
[Host]
localhost = 127.0.0.1

[URL Rewrite]
^https?://(www.)?g.cn https://www.google.com 302
^https?://(www.)?google.cn https://www.google.com 302

(?<=_region=)CN(?=&) US 307
(?<=&mcc_mnc=)460[0-9]{2} 310260 307
(?<=&sim_region=)cn(?=&) us 307
(?<=&sys_region=)CN(?=&) US 307
"""

# 手动追加的补丁域名（确保哔哩哔哩 CDN、豆瓣等 100% 直连）
MANUAL_DIRECT_PATCHES = [
    "DOMAIN-SUFFIX,douban.com,DIRECT",
    "DOMAIN-SUFFIX,doubanio.com,DIRECT",
    "DOMAIN-SUFFIX,hdslb.com,DIRECT",
    "DOMAIN-SUFFIX,b23.tv,DIRECT",
    "DOMAIN-SUFFIX,bilibili.com,DIRECT"
]

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
        print(f"⚠️ 抓取 Top500 规则失败: {e}，尝试使用备用逻辑或抛出异常")
        raise e

def parse_rules(lines):
    in_rule_section = False
    rules = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('[') and stripped.endswith(']'):
            in_rule_section = (stripped == '[Rule]')
            continue
            
        if in_rule_section:
            if stripped and not stripped.startswith('#'):
                # 规范化大小写，保留 Direct / Proxy
                if stripped.lower().endswith(',direct'):
                    normalized = stripped[:-7] + ',DIRECT'
                    rules.append(normalized)
                elif stripped.lower().endswith(',proxy'):
                    normalized = stripped[:-6] + ',PROXY'
                    rules.append(normalized)
                else:
                    rules.append(stripped)
                    
    print(f"📊 从原始文本中解析出 [Rule] 规则共 {len(rules)} 条。")
    return rules

def build_conf_content(rules):
    now_str = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    header = HEADER_TEMPLATE.format(timestamp=now_str)
    
    # 分类打标签
    direct_rules = []
    proxy_rules = []
    
    # 注入手动补丁去重
    seen = set()
    for patch in MANUAL_DIRECT_PATCHES:
        if patch not in seen:
            seen.add(patch)
            direct_rules.append(patch)
            
    for r in rules:
        if r in seen:
            continue
        seen.add(r)
        if ',DIRECT' in r:
            direct_rules.append(r)
        elif ',PROXY' in r:
            proxy_rules.append(r)
            
    # 过滤 proxy_rules 中的 FINAL,PROXY 以防重复
    proxy_rules = [r for r in proxy_rules if not r.startswith('FINAL,')]

    rule_lines = []
    rule_lines.append("# === 1. Top500 直连规则集 (Direct Rules) ===")
    rule_lines.extend(direct_rules)
    rule_lines.append("\n# === 2. Top500 代理规则集 (Proxy Rules) ===")
    rule_lines.extend(proxy_rules)
    
    # 终极对齐：纯正白名单代理，末尾保持 FINAL, PROXY
    rule_lines.append("\n# === 3. 白名单代理模式终极兜底 ===")
    rule_lines.append("FINAL,PROXY\n")
    
    final_content = header + "\n".join(rule_lines) + FOOTER_TEMPLATE
    return final_content, len(direct_rules), len(proxy_rules)

def main():
    lines = fetch_top500_rules()
    rules = parse_rules(lines)
    conf_str, d_cnt, p_cnt = build_conf_content(rules)
    
    os.makedirs(os.path.dirname(OUTPUT_CONF), exist_ok=True)
    with open(OUTPUT_CONF, 'w', encoding='utf-8') as f:
        f.write(conf_str)
        
    line_count = len(conf_str.splitlines())
    print(f"🎉 成功生成 {OUTPUT_CONF}！")
    print(f"📈 统计数据: 物理总行数 {line_count} 行 | Direct 规则 {d_cnt} 条 | Proxy 规则 {p_cnt} 条 | 规则匹配末尾: FINAL,PROXY")

if __name__ == "__main__":
    main()
