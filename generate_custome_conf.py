#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
generate_custome_conf.py
自动抓取 Johnshall Top500 最新白名单规则，结合纯 IP 式 DoH 加密 DNS、5G 退避防发热、
以及原版 Line 843 (.cn) 与 Line 844 (GEOIP,CN) 物理防线，自动生成纯净 Shadowrocket 主配置文件 custome_conf.conf。
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
# 🛡️ 核心特性: Top500 全量规则 + 纯 IP DoH + GEOIP CN 防线 + 0 本地 DNS 泄露
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
                # 规范化大小写
                if stripped.lower().endswith(',direct'):
                    prefix = stripped[:-7]
                    rules.append(f"{prefix.upper()},DIRECT")
                elif stripped.lower().endswith(',proxy'):
                    prefix = stripped[:-6]
                    rules.append(f"{prefix.upper()},PROXY")
                elif stripped.upper().startswith("GEOIP,"):
                    rules.append(stripped.upper())
                else:
                    rules.append(stripped)
                    
    print(f"📊 从原始文本中解析出 [Rule] 规则共 {len(rules)} 条。")
    return rules

def build_conf_content(rules):
    now_str = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    header = HEADER_TEMPLATE.format(timestamp=now_str)
    
    # 分类与排重
    direct_rules = []
    proxy_rules = []
    
    seen = set()
    for r in rules:
        if r in seen or r == "FINAL,PROXY":
            continue
        seen.add(r)
        if ',DIRECT' in r and not r.startswith('GEOIP,'):
            direct_rules.append(r)
        elif ',PROXY' in r:
            proxy_rules.append(r)
            
    rule_lines = []
    rule_lines.append("# === 1. Top500 直连规则集 (Direct Rules) ===")
    rule_lines.extend(direct_rules)
    
    rule_lines.append("\n# === 2. Top500 代理规则集 (Proxy Rules) ===")
    rule_lines.extend(proxy_rules)
    
    rule_lines.append("\n# === 3. .cn 国家顶级域名直连 (继承 Top500 原版 Line 843) ===")
    rule_lines.append("DOMAIN-SUFFIX,CN,DIRECT")
    
    rule_lines.append("\n# === 4. GEOIP 中国 IP 物理防线 (继承 Top500 原版 Line 844，内置 GeoLite2 数据库) ===")
    rule_lines.append("GEOIP,CN,DIRECT")
    
    rule_lines.append("\n# === 5. 未知海外域名终极兜底 (防 DNS 泄露) ===")
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
    print(f"🎉 成功生成纯净配置文件 {OUTPUT_CONF}！")
    print(f"📈 统计数据: 物理总行数 {line_count} 行 | Direct 规则 {d_cnt} 条 | Proxy 规则 {p_cnt} 条 | 防线规则: .CN 直连 + GEOIP CN 直连 + FINAL PROXY")

if __name__ == "__main__":
    main()
