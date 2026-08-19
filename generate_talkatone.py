import urllib.request
import re
import os
import ssl
import json

ssl._create_default_https_context = ssl._create_unverified_context

# -------------------------------------------------------------
# 1. 动态载入解耦后的静态 JSON 规则与白名单配置
# -------------------------------------------------------------
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references", "talkatone_sgmodule_config.json")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

COMMUNITY_RULES_URL = config["community_rules_url"]
AD_SOURCES = config["ad_sources"]
WHITELIST_DOMAINS = config["whitelist_domains"]

def load_custom_reject_methods():
    mapping = {}
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "references", "custom_reject_methods.txt"),
        os.path.join(os.path.dirname(base_dir), "references", "custom_reject_methods.txt")
    ]
    dict_path = None
    for p in candidates:
        if os.path.exists(p):
            dict_path = p
            break
            
    if not dict_path:
        print("⚠️ 未找到 custom_reject_methods.txt，将全量降级使用默认 REJECT")
        return mapping

    print(f"📖 正在读取自定义拒绝方式字典: {dict_path}")
    with open(dict_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) >= 2:
                domain = parts[0].lower()
                method = parts[1].upper()
                mapping[domain] = method
    print(f"✅ 成功加载 {len(mapping)} 条域名拒绝方式映射机制")
    return mapping

_custom_reject_mapping = load_custom_reject_methods()

def get_smart_reject_action(domain):
    domain_lower = domain.lower().strip('.')
    
    # 1. 显式字典精准优先匹配 (来自 custom_reject_methods.txt)
    if domain_lower in _custom_reject_mapping:
        return _custom_reject_mapping[domain_lower]
    for d, m in _custom_reject_mapping.items():
        if domain_lower == d or domain_lower.endswith("." + d):
            return m
            
    # 2. 智能特征分类匹配：
    # A类：高频广告 SDK 联盟、数据追踪与遥测分析 ➔ 统一步提升为 REJECT-DROP
    drop_keywords = [
        "googleads", "doubleclick", "analytics", "telemetry", "tracking", "tracker", 
        "adsystem", "inmobi", "pubmatic", "smadex", "criteo", "appier", "appiersig",
        "jampp", "bidswitch", "adrta", "serveteck", "iteleserve", "tk0x1",
        "rubiconproject", "openx", "casalemedia", "taboola", "outbrain"
    ]
    if any(kw in domain_lower for kw in drop_keywords):
        return "REJECT-DROP"
        
    # B类：SDK 日志、打点上报与验证码探针 ➔ 统一匹配为 REJECT-200 诱骗清空队列
    reject200_keywords = [
        "mobads-logs", "log-report", "stat-report", "geetest", "captcha", "report-api"
    ]
    if any(kw in domain_lower for kw in reject200_keywords):
        return "REJECT-200"

    # 3. 普通常规 Banner 广告域名 ➔ 维持标准 REJECT
    return "REJECT"

def download_url(url):
    print(f"Downloading: {url}")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def is_whitelisted(domain):
    domain_lower = domain.lower().strip('.')
    for whitelist in WHITELIST_DOMAINS:
        if domain_lower == whitelist or domain_lower.endswith('.' + whitelist):
            return True
    return False

def parse_clash_yaml(yaml_content):
    rules = []
    lines = yaml_content.splitlines()
    payload_section = False
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("#"):
            continue
            
        if line_stripped.startswith("payload:"):
            payload_section = True
            continue
            
        if payload_section or line_stripped.startswith("-"):
            match = re.search(r'^-\s+([^,]+),([^,]+)(?:,.+)?', line_stripped)
            if match:
                rule_type = match.group(1).strip().upper()
                value = match.group(2).strip().lower()
                
                if rule_type in ("DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "IP-CIDR", "IP-CIDR6"):
                    rules.append((rule_type, value))
    return rules

def generate_proxy_module(script_dir):
    print("\n=== Generating Talkatone Proxy Module ===")
    
    community_proxy_rules = []
    community_direct_rules = []
    community_seen_keys = {} # 格式: { "rule_type,value": "PROXY" / "DIRECT" }

    # 1. 抓取别人维护的高频更新分流规则 (LOWERTOP)
    community_content = download_url(COMMUNITY_RULES_URL)
    if community_content:
        print("Parsing community Talkatone.sgmodule for proxy and direct rules...")
        for line in community_content.splitlines():
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                continue
                
            # 我们查找 PROXY 分流（LOWERTOP中使用 {{{代理分流}}} 和 {{{节点检测}}} 模板参数）
            if "{{{" in line_stripped:
                match = re.match(r'^(DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|IP-CIDR|IP-CIDR6),([^,\s]+)', line_stripped, re.IGNORECASE)
                if match:
                    rule_type = match.group(1).upper()
                    value = match.group(2).lower()
                    key = f"{rule_type},{value}"
                    community_seen_keys[key] = "PROXY"
                    community_proxy_rules.append(f"{rule_type},{value},PROXY")
                    
            # 查找 DIRECT 直连分流
            elif ",DIRECT" in line_stripped:
                match = re.match(r'^(DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|IP-CIDR|IP-CIDR6),([^,\s]+)', line_stripped, re.IGNORECASE)
                if match:
                    rule_type = match.group(1).upper()
                    value = match.group(2).lower()
                    key = f"{rule_type},{value}"
                    community_seen_keys[key] = "DIRECT"
                    community_direct_rules.append(f"{rule_type},{value},DIRECT")
        print(f" - Found {len(community_proxy_rules)} PROXY and {len(community_direct_rules)} DIRECT rules in community source.")
    else:
        print("Warning: Failed to fetch community rule file.")

    # 2. 读取本地自建静态参考规则集 (custom_static_talkatone_proxy251213.sgmodule)
    user_rules_to_add = []
    user_seen = set()
    
    proxy_static_path = os.path.join(script_dir, "custom_static_talkatone_proxy251213.sgmodule")
    if os.path.exists(proxy_static_path):
        print(f"Reading local static proxy rules: {proxy_static_path}")
        with open(proxy_static_path, "r", encoding="utf-8") as f:
            user_content = f.read()
            
        in_rule_section = False
        for line in user_content.splitlines():
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                continue
            if line_stripped.startswith("[Rule]"):
                in_rule_section = True
                continue
            if line_stripped.startswith("["):
                in_rule_section = False
                continue
                
            if in_rule_section:
                # 严格正则提取，自动过滤可能多余的空格或写错的行
                match = re.match(r'^(DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|IP-CIDR|IP-CIDR6),([^,\s]+)', line_stripped, re.IGNORECASE)
                if match:
                    rule_type = match.group(1).upper()
                    value = match.group(2).lower()
                    key = f"{rule_type},{value}"
                    
                    # 补全与覆盖比对逻辑
                    if key not in community_seen_keys:
                        if key not in user_seen:
                            user_seen.add(key)
                            user_rules_to_add.append(f"{rule_type},{value},PROXY")
                            print(f"   [補全] 别人未包含，补充代理: {rule_type},{value}")
                    elif community_seen_keys[key] == "DIRECT":
                        if key not in user_seen:
                            user_seen.add(key)
                            user_rules_to_add.append(f"{rule_type},{value},PROXY")
                            community_direct_rules = [r for r in community_direct_rules if not r.startswith(key + ",")]
                            print(f"   [覆蓋] 别人设为直连，强制改为代理: {rule_type},{value}")
    else:
        print(f"Error: {proxy_static_path} not found!")

    # 3. 整合汇总
    final_rules = []
    final_rules.append("# === 1. User Customized & Remapped Rules ===")
    final_rules.extend(user_rules_to_add)
    
    final_rules.append("\n# === 2. Community High-frequency Proxy Rules ===")
    for rule in community_proxy_rules:
        key = ",".join(rule.split(",")[:2])
        if key not in user_seen:
            final_rules.append(rule)
            
    final_rules.append("\n# === 3. Community High-frequency Direct Rules ===")
    for rule in community_direct_rules:
        final_rules.append(rule)

    from datetime import datetime, timezone, timedelta
    beijing_time_str = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')

    output_path = os.path.join(script_dir, "talkatone_proxy.sgmodule")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#!name=Talkatone.Proxy.sgmodule\n")
        f.write(f"#!desc=最近更新: {beijing_time_str} | 自用 Talkatone 代理分流模块。合并社区高频更新规则与用户自建静态参考规则.\n")
        f.write(f"#!total={len(user_rules_to_add) + len(community_proxy_rules) + len(community_direct_rules)}\n\n")
        f.write("[Rule]\n")
        for rule in final_rules:
            f.write(rule + "\n")
            
    print(f"Successfully generated Talkatone Proxy module at: {output_path}")

def generate_adblock_module(script_dir):
    print("\n=== Generating Talkatone AdBlock Module ===")
    adblock_rules = []
    seen = set()

    # 1. 抓取别人维护的高频更新 Talkatone.sgmodule (LOWERTOP) 中的去广告规则
    community_content = download_url(COMMUNITY_RULES_URL)
    if community_content:
        print("Parsing community Talkatone.sgmodule for adblock rules...")
        added_count = 0
        for line in community_content.splitlines():
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                continue
            
            if ",REJECT" in line_stripped:
                match = re.match(r'^(DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|IP-CIDR|IP-CIDR6),([^,\s]+)', line_stripped, re.IGNORECASE)
                if match:
                    rule_type = match.group(1).upper()
                    value = match.group(2).lower()
                    
                    if rule_type in ("DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"):
                        if is_whitelisted(value):
                            continue
                            
                    norm = f"{rule_type},{value}"
                    if norm not in seen:
                        seen.add(norm)
                        action = get_smart_reject_action(value)
                        adblock_rules.append(f"{rule_type},{value},{action}")
                        added_count += 1
        print(f" - Parsed and added {added_count} adblock rules from community source.")

    # 2. 读取本地自建静态去广告参考规则 (custom_static_talkatone_adblock260119.sgmodule)
    adblock_static_path = os.path.join(script_dir, "custom_static_talkatone_adblock260119.sgmodule")
    if os.path.exists(adblock_static_path):
        print(f"Reading local static adblock rules: {adblock_static_path}")
        with open(adblock_static_path, "r", encoding="utf-8") as f:
            adblock_content = f.read()
            
        in_rule_section = False
        added_count = 0
        for line in adblock_content.splitlines():
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                continue
            if line_stripped.startswith("[Rule]"):
                in_rule_section = True
                continue
            if line_stripped.startswith("["):
                in_rule_section = False
                continue
                
            if in_rule_section:
                match = re.match(r'^(DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|IP-CIDR|IP-CIDR6),([^,\s]+)', line_stripped, re.IGNORECASE)
                if match:
                    rule_type = match.group(1).upper()
                    value = match.group(2).lower()
                    
                    if rule_type in ("DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"):
                        if is_whitelisted(value):
                            continue
                            
                    norm = f"{rule_type},{value}"
                    if norm not in seen:
                        seen.add(norm)
                        action = get_smart_reject_action(value)
                        adblock_rules.append(f"{rule_type},{value},{action}")
                        added_count += 1
        print(f" - Parsed and added {added_count} custom static adblock rules.")
    else:
        print(f"Error: {adblock_static_path} not found!")

    # 3. 抓取远程广告联盟规则并解析合并
    for alliance, url in AD_SOURCES.items():
        content = download_url(url)
        if not content:
            print(f"Warning: Failed to fetch {alliance} rules")
            continue
            
        parsed = parse_clash_yaml(content)
        added_count = 0
        for rule_type, value in parsed:
            if rule_type in ("DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"):
                if is_whitelisted(value):
                    continue
            
            norm = f"{rule_type},{value}"
            if norm not in seen:
                seen.add(norm)
                action = get_smart_reject_action(value)
                adblock_rules.append(f"{rule_type},{value},{action}")
                added_count += 1
        print(f" - Parsed {len(parsed)} rules from {alliance}, added {added_count} clean rules.")

    from datetime import datetime, timezone, timedelta
    beijing_time_str = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')

    output_path = os.path.join(script_dir, "talkatone_adblock.sgmodule")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#!name=Talkatone.AdBlock.sgmodule\n")
        f.write(f"#!desc=最近更新: {beijing_time_str} | 自用 Talkatone 去广告模块。整合社区最新规则、自建静态规则与 AdMob, Unity, AppLovin, Amazon 拦截源.\n")
        f.write(f"#!total={len(adblock_rules)}\n\n")
        f.write("[Rule]\n")
        for rule in adblock_rules:
            f.write(rule + "\n")
            
    print(f"Successfully generated Talkatone AdBlock module at: {output_path}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    generate_proxy_module(script_dir)
    generate_adblock_module(script_dir)

if __name__ == "__main__":
    main()
