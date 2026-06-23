import urllib.request
import re
import sys
import os
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# Target AI sources from BlackMatrix7
AI_SOURCES = {
    "OpenAI": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/OpenAI/OpenAI.yaml",
    "Claude": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Claude/Claude.yaml",
    "Gemini": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Gemini/Gemini.yaml",
    "Copilot": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Copilot/Copilot.yaml"
}

# Domains that are too broad and will pollute everyday direct browsing
# We strip/bypass these top-level domains unless they match the allow-subdomains list below
POLLUTION_DOMAINS = [
    "google.com", "microsoft.com", "bing.com", "live.com", "x.com", "twitter.com", "apple.com"
]

# Specifically allowed subdomains/keywords for the above parent domains
ALLOWED_SUBDOMAINS = [
    # Gemini / Google AI
    "gemini.google.com", "generativelanguage.googleapis.com", "notebooklm.google.com", "alkalimira-pa.clients6.google.com",
    # Copilot / Bing AI
    "copilot.microsoft.com", "sydney.bing.com", "edgeservices.bing.com",
    # Apple Intelligence
    "guzzoni.apple.com", "smoot.apple.com", "gspe1-ssl.ls.apple.com"
]

# User's manually verified custom rules (Highest priority)
CUSTOM_RULES = """# === User Custom AI & Apple Intelligence Rules ===
# > Apple Intelligence / Apple AI
# 核心Siri与听写服务
DOMAIN,guzzoni.apple.com,PROXY
DOMAIN,smoot.apple.com,PROXY

# Apple Relay & Private Relay 相关
# 新增：匹配任何包含 "apple-relay" 的域名 (如 mask.apple-relay.apple.com 等)
DOMAIN-KEYWORD,apple-relay,PROXY
DOMAIN,apple-relay.apple.com,PROXY
DOMAIN,apple-relay.cloudflare.com,PROXY
DOMAIN,apple-relay.fastly-edge.com,PROXY

# 位置服务 (注意：代理此域名可能会改变系统判定的地理位置)
DOMAIN,gspe1-ssl.ls.apple.com,PROXY
# 连接性检查
DOMAIN,cp4.cloudflare.com,PROXY

# > Yahoo (Keyword)
DOMAIN-KEYWORD,yahoo.com,PROXY

# > Claude (Anthropic) 依赖的第三方服务/分析统计
DOMAIN,cdn.usefathom.com,PROXY
DOMAIN,segment.io,PROXY
DOMAIN,segment.com,PROXY
DOMAIN,statsig.com,PROXY
DOMAIN,statsigapi.net,PROXY
DOMAIN,o532071.ingest.sentry.io,PROXY

# > Grok (xAI)
DOMAIN-SUFFIX,grok.com,PROXY
DOMAIN-SUFFIX,x.ai,PROXY

# > Poe
DOMAIN-SUFFIX,poe.com,PROXY

# > Manus
DOMAIN-SUFFIX,manus.im,PROXY
DOMAIN-SUFFIX,manus.app,PROXY
DOMAIN-SUFFIX,manus-api.im,PROXY
"""

def download_url(url):
    print(f"Downloading: {url}")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Quantumult X/1.4.3'}
        )
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def is_polluted(domain):
    domain_lower = domain.lower().strip('.')
    
    # 1. If it matches one of our explicitly allowed subdomains, it is NOT polluted
    for allowed in ALLOWED_SUBDOMAINS:
        if domain_lower == allowed or domain_lower.endswith('.' + allowed):
            return False
            
    # 2. Check if it matches one of the broad polluted domains
    for polluted in POLLUTION_DOMAINS:
        if domain_lower == polluted or domain_lower.endswith('.' + polluted):
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
            
        if payload_section:
            # Parse Clash rules in classical format e.g.
            # - DOMAIN-SUFFIX,openai.com
            # - DOMAIN,chat.openai.com
            # - IP-CIDR,12.34.56.78/24,no-resolve (we discard no-resolve/resolve in sgmodule)
            match = re.search(r'^-\s+([^,]+),([^,]+)(?:,.+)?', line_stripped)
            if match:
                rule_type = match.group(1).strip().upper()
                value = match.group(2).strip().lower()
                
                # Check for broad pollution domains
                if rule_type in ("DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"):
                    if is_polluted(value):
                        # Bypass this rule as it will pollute direct browsing traffic
                        continue
                
                # Map to Shadowrocket module rule format
                if rule_type in ("DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "IP-CIDR", "IP-CIDR6"):
                    rules.append(f"{rule_type},{value},PROXY")
                    
    return rules

def main():
    compiled_rules = []
    
    # Process BM7 sources
    for service, url in AI_SOURCES.items():
        content = download_url(url)
        if not content:
            print(f"Warning: Failed to fetch rules for {service}")
            continue
            
        print(f"Parsing Clash rules for {service}...")
        parsed = parse_clash_yaml(content)
        compiled_rules.extend(parsed)
        print(f" - Found {len(parsed)} clean rules for {service}")
        
    # Append custom rules (highest priority)
    custom_lines = []
    for line in CUSTOM_RULES.splitlines():
        line_stripped = line.strip()
        if line_stripped and not line_stripped.startswith("#"):
            custom_lines.append(line_stripped)
            
    # Deduplicate rules, ensuring custom rules are at the top and preserved
    final_rules = []
    seen = set()
    
    # 1. Add user custom rules first
    for line in CUSTOM_RULES.splitlines():
        line_stripped = line.strip()
        if line_stripped:
            if not line_stripped.startswith("#"):
                # Normalize rule for uniqueness checking
                norm = line_stripped.replace(" ", "").lower()
                if norm not in seen:
                    seen.add(norm)
                    final_rules.append(line_stripped)
            else:
                final_rules.append(line_stripped)
                
    # 2. Add compiled rules
    final_rules.append("\n# === Compiled AI & Subdomain Rules ===")
    for rule in compiled_rules:
        norm = rule.replace(" ", "").lower()
        if norm not in seen:
            seen.add(norm)
            final_rules.append(rule)
            
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "ai.sgmodule")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#!name=AI.sgmodule (Apple Intelligence/ChatGPT/Claude/Grok/Gemini/NotebookLM/Poe/Manus/Copilot)\n")
        f.write("#!desc=自用 AI 工具代理分流模块。针对平台: Apple Intelligence, ChatGPT, Claude, Grok, Gemini, NotebookLM, Poe, Manus, Copilot (每日 08:00 自动更新)\n")
        f.write(f"#!total={len(seen)}\n\n")
        
        f.write("[Rule]\n")
        for rule in final_rules:
            f.write(rule + "\n")
            
    print(f"\nSuccessfully generated AI Proxy V2 module with {len(seen)} unique rules at: {output_path}")

if __name__ == "__main__":
    main()

