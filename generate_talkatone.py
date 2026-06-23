import urllib.request
import re
import os
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# -------------------------------------------------------------
# 1. 抓取与规则配置
# -------------------------------------------------------------
# 用户自用的参考 Talkatone 代理规则集（静态参考，用于补全和强制代理）
USER_PROXY_URL = "https://raw.githubusercontent.com/ssupssup/ini/refs/heads/main/talkatone.list"

# 社区高频更新的 Talkatone 核心规则文件（LOWERTOP 维护）
COMMUNITY_RULES_URL = "https://raw.githubusercontent.com/LOWERTOP/Shadowrocket-First/refs/heads/main/Talkatone.sgmodule"

# 社区主要的广告联盟规则集（用于动态更新 Talkatone 中的联盟广告拦截）
AD_SOURCES = {
    "GoogleAds": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Google/Google.yaml",
    "UnityAds": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Unity/Unity.yaml",
    "AppLovin": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/AppLovin/AppLovin.yaml",
    "AmazonAds": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Amazon/Amazon.yaml"
}

# 针对 Talkatone 特定广告域名及联盟广告（直接内置的最高优先级规则）
CUSTOM_AD_RULES = [
    # Smadex / Jampp
    "DOMAIN-SUFFIX,creatives.smadex.com,REJECT",
    "DOMAIN-SUFFIX,static-content-1.smadex.com,REJECT",
    "DOMAIN-SUFFIX,br-trk.smadex.com,REJECT",
    "DOMAIN-SUFFIX,imp-lb-us2.jampp.com,REJECT",
    # 联盟补充域名
    "DOMAIN-SUFFIX,mobilefuse.com,REJECT",
    "DOMAIN-SUFFIX,cdn.mobilefuse.com,REJECT",
    "DOMAIN-SUFFIX,mfx.mobilefuse.com,REJECT",
    "DOMAIN-SUFFIX,adsappier.com,REJECT",
    "DOMAIN-SUFFIX,cr.adsappier.com,REJECT",
    "DOMAIN-SUFFIX,appier.net,REJECT",
    "DOMAIN-SUFFIX,appiersig.com,REJECT",
    "DOMAIN-SUFFIX,vst.c.appier.net,REJECT",
    "DOMAIN-SUFFIX,mt-usw.appiersig.com,REJECT",
    "DOMAIN-SUFFIX,cdn2.inner-active.mobi,REJECT",
    "DOMAIN-SUFFIX,exchange-b-events.inner-active.mobi,REJECT",
    "DOMAIN-SUFFIX,sdk-events.inner-active.mobi,REJECT",
    "DOMAIN-SUFFIX,wv.inner-active.mobi,REJECT",
    "DOMAIN-SUFFIX,skadnetworks.fyber.com,REJECT",
    "DOMAIN-SUFFIX,cdn-f.adsmoloco.com,REJECT",
    "DOMAIN-SUFFIX,tr-asia.adsmoloco.com,REJECT",
    "DOMAIN-SUFFIX,cdn.liftoff-creatives.io,REJECT",
    "DOMAIN-SUFFIX,impression-asia.liftoff.io,REJECT",
    "DOMAIN-SUFFIX,ins.track.tappx.com,REJECT",
    "DOMAIN-SUFFIX,ssp.api.tappx.com,REJECT",
    "DOMAIN-SUFFIX,taboola.com,REJECT",
    "DOMAIN-SUFFIX,pubmatic.com,REJECT",
    "DOMAIN-SUFFIX,ads.pubmatic.com,REJECT",
    "DOMAIN-SUFFIX,ow.pubmatic.com,REJECT",
    "DOMAIN-SUFFIX,view.adjust.com,REJECT",
    "DOMAIN-SUFFIX,ep7.facebook.com,REJECT",
    "DOMAIN-SUFFIX,impression.link,REJECT",
    "DOMAIN-SUFFIX,app-analytics-services.com,REJECT",
    "DOMAIN-SUFFIX,paypal-metrics.com,REJECT",
    # Talkatone 的广告服务商域名（注意与核心域 tktn.be 区分！）
    "DOMAIN-SUFFIX,ads.tntk.be,REJECT",
    "DOMAIN-SUFFIX,a1.tntk.be,REJECT",
    # Firebase (统计/崩溃日志/配置)
    "DOMAIN-SUFFIX,firebaseinstallations.googleapis.com,REJECT",
    "DOMAIN-SUFFIX,firebaselogging-pa.googleapis.com,REJECT",
    "DOMAIN-SUFFIX,firebaseremoteconfig.googleapis.com,REJECT",
    "DOMAIN-SUFFIX,firebase-settings.crashlytics.com,REJECT"
]

# 防误杀白名单（绝对禁止 REJECT 的核心网络域）
WHITELIST_DOMAINS = [
    "talkatone.com",
    "tktn.be",
    "tktn.at"
]

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
            # 过滤注释
            if not line_stripped or line_stripped.startswith("#"):
                continue
                
            # 我们查找 PROXY 分流（LOWERTOP中使用 {{{代理分流}}} 和 {{{节点检测}}} 模板参数）
            if "{{{" in line_stripped:
                # 提取规则：例如 DOMAIN-SUFFIX,tktn.at,{{{代理分流}}}
                match = re.match(r'^(DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|IP-CIDR|IP-CIDR6),([^,\s]+)', line_stripped, re.IGNORECASE)
                if match:
                    rule_type = match.group(1).upper()
                    value = match.group(2).lower()
                    key = f"{rule_type},{value}"
                    community_seen_keys[key] = "PROXY"
                    community_proxy_rules.append(f"{rule_type},{value},PROXY")
                    
            # 查找 DIRECT 直连分流
            elif ",DIRECT" in line_stripped:
                # 提取直连规则
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

    # 2. 抓取用户自用静态参考规则集 (talkatone.list)
    user_rules_to_add = []
    user_seen = set()
    user_content = download_url(USER_PROXY_URL)
    if user_content:
        print("Parsing user reference talkatone.list...")
        for line in user_content.splitlines():
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                continue
                
            # 严格正则提取，自动过滤和跳过末尾写错的 DOMAIN-SUFFI 等错误行
            match = re.match(r'^(DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|IP-CIDR|IP-CIDR6),([^,\s]+)', line_stripped, re.IGNORECASE)
            if match:
                rule_type = match.group(1).upper()
                value = match.group(2).lower()
                key = f"{rule_type},{value}"
                
                # 核心逻辑：
                # 如果别人的规则集里没有包含该域名，则将其作为代理规则补上！
                # 如果别人的规则集把它设为了 DIRECT，但用户的自用文件指示需要代理，则优先尊重用户，将其设为 PROXY
                if key not in community_seen_keys:
                    if key not in user_seen:
                        user_seen.add(key)
                        user_rules_to_add.append(f"{rule_type},{value},PROXY")
                        print(f"   [補全] 别人未包含，补充代理: {rule_type},{value}")
                elif community_seen_keys[key] == "DIRECT":
                    # 用户的参考配置需要代理，我们重写/覆盖为 PROXY 并移除原本 DIRECT 记录
                    if key not in user_seen:
                        user_seen.add(key)
                        user_rules_to_add.append(f"{rule_type},{value},PROXY")
                        # 从 direct 列表中移出
                        community_direct_rules = [r for r in community_direct_rules if not r.startswith(key + ",")]
                        print(f"   [覆蓋] 别人设为直连，强制改为代理: {rule_type},{value}")
    else:
        print("Warning: Failed to fetch user proxy list.")

    # 3. 整合汇总
    final_rules = []
    final_rules.append("# === 1. User Customized & Remapped Rules ===")
    final_rules.extend(user_rules_to_add)
    
    final_rules.append("\n# === 2. Community High-frequency Proxy Rules ===")
    # 过滤掉已经被用户覆盖了的域名
    for rule in community_proxy_rules:
        key = ",".join(rule.split(",")[:2])
        if key not in user_seen:
            final_rules.append(rule)
            
    final_rules.append("\n# === 3. Community High-frequency Direct Rules ===")
    for rule in community_direct_rules:
        final_rules.append(rule)

    output_path = os.path.join(script_dir, "talkatone_proxy.sgmodule")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#!name=Talkatone.Proxy.sgmodule\n")
        f.write("#!desc=自用 Talkatone 代理分流模块。合并社区高频更新规则与用户自定义参考规则 (每日 08:00 自动更新)\n")
        f.write(f"#!total={len(user_rules_to_add) + len(community_proxy_rules) + len(community_direct_rules)}\n\n")
        f.write("[Rule]\n")
        for rule in final_rules:
            f.write(rule + "\n")
            
    print(f"Successfully generated integrated Talkatone Proxy module at: {output_path}")

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
            
            # 提取 REJECT 规则
            if ",REJECT" in line_stripped:
                match = re.match(r'^(DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|IP-CIDR|IP-CIDR6),([^,\s]+)', line_stripped, re.IGNORECASE)
                if match:
                    rule_type = match.group(1).upper()
                    value = match.group(2).lower()
                    
                    # 进行防误杀过滤
                    if rule_type in ("DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"):
                        if is_whitelisted(value):
                            continue
                            
                    norm = f"{rule_type},{value}"
                    if norm not in seen:
                        seen.add(norm)
                        adblock_rules.append(f"{rule_type},{value},REJECT")
                        added_count += 1
        print(f" - Parsed and added {added_count} adblock rules from community source.")

    # 2. 首先加载并解析自定义广告规则（高优先级）
    for rule in CUSTOM_AD_RULES:
        parts = rule.split(',')
        if len(parts) >= 2:
            rule_type = parts[0].strip().upper()
            value = parts[1].strip().lower()
            
            # 进行防误杀过滤
            if rule_type in ("DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"):
                if is_whitelisted(value):
                    continue
                    
            norm = f"{rule_type},{value}"
            if norm not in seen:
                seen.add(norm)
                adblock_rules.append(f"{rule_type},{value},REJECT")

    # 3. 抓取远程广告联盟规则并解析合并
    for alliance, url in AD_SOURCES.items():
        content = download_url(url)
        if not content:
            print(f"Warning: Failed to fetch {alliance} rules")
            continue
            
        parsed = parse_clash_yaml(content)
        added_count = 0
        for rule_type, value in parsed:
            # 防误杀白名单安全过滤
            if rule_type in ("DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"):
                if is_whitelisted(value):
                    continue
            
            norm = f"{rule_type},{value}"
            if norm not in seen:
                seen.add(norm)
                adblock_rules.append(f"{rule_type},{value},REJECT")
                added_count += 1
        print(f" - Parsed {len(parsed)} rules from {alliance}, added {added_count} clean rules.")

    output_path = os.path.join(script_dir, "talkatone_adblock.sgmodule")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#!name=Talkatone.AdBlock.sgmodule\n")
        f.write("#!desc=自用 Talkatone 去广告模块。整合社区最新规则与 AdMob, Unity, AppLovin, Smaato, InMobi 拦截源 (每日 08:00 自动更新)\n")
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
