import urllib.request
import re
import sys
import hashlib
import os
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# User's installed apps (excluding China Unicom)
# Load config and rules data from separate JSON file
import json
_base_dir = os.path.dirname(__file__)
_ref_dir = os.path.join(_base_dir, 'references')
if not os.path.exists(_ref_dir):
    _ref_dir = os.path.join(os.path.dirname(_base_dir), 'references')

with open(os.path.join(_ref_dir, 'adblock_rules_data.json'), 'r', encoding='utf-8') as _f:
    _rules_data = json.load(_f)
INSTALLED_APPS = _rules_data['INSTALLED_APPS']
APP_KEYWORDS = _rules_data['APP_KEYWORDS']
OVERRIDE_APPS = _rules_data['OVERRIDE_APPS']
EXTRA_REWRITE_DOMAINS = _rules_data['EXTRA_REWRITE_DOMAINS']
SDK_BLOCK_RULES = _rules_data['SDK_BLOCK_RULES']
MANDATORY_MITM_DOMAINS = _rules_data['MANDATORY_MITM_DOMAINS']
CUSTOM_REWRITE_RULES = _rules_data['CUSTOM_REWRITE_RULES']


# App keywords mapping for BlackMatrix7 filtering (excluding China Unicom)

# Apps that we will fetch from ddgksf2013 or Maasea instead of BlackMatrix7 (excluding China Unicom)

# Extra domains that we want to reject via Rules (like QQ Music)

# Universal Ad SDK domains to reject unconditionally via Rules
# Load decoupled static rules data
static_data_path = os.path.join(_ref_dir, 'generator_static_data.json')
with open(static_data_path, 'r', encoding='utf-8') as _sf:
    _s_data = json.load(_sf)

ALWAYS_INJECT_DOMAINS = [x for x in _s_data["ALWAYS_INJECT_DOMAINS"] if not x.startswith("#")]
ALWAYS_KEEP_KEYWORDS = _s_data["ALWAYS_KEEP_KEYWORDS"]
HIGH_RISK_MITM_DOMAINS = [x for x in _s_data["HIGH_RISK_MITM_DOMAINS"] if not x.startswith("#")]

def load_agh_blocked_domains():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(base_dir, "../istoreos/scratch/adguardhome_custom_rules.txt"),
        os.path.join(base_dir, "adguardhome_custom_rules.txt"),
        "/Users/shizupeng/Documents/antigravity/istoreos/scratch/adguardhome_custom_rules.txt"
    ]
    agh_file = None
    for p in possible_paths:
        if os.path.exists(p):
            agh_file = p
            break
            
    if not agh_file:
        print("Warning: AGH custom rules file not found, skipping local AGH injection.")
        return []
    
    domains = []
    try:
        with open(agh_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        in_track_a = False
        in_track_b = False
        
        for line in lines:
            line_str = line.strip()
            
            if "轨道 A · Fake-IP" in line_str:
                in_track_a = True
                in_track_b = False
                continue
            elif "轨道 B · NXDOMAIN" in line_str:
                in_track_a = False
                in_track_b = True
                continue
            elif "第二部分：常规严格拦截" in line_str or ("\u0001F534 \u4e13\u5c5e\u533a\u57df" in line_str and "轨道 B" not in line_str):
                in_track_a = False
                in_track_b = False
            
            if in_track_a:
                if line_str.startswith("@@||") and "$important" in line_str:
                    domain = line_str.replace("@@||", "").split("^")[0].strip()
                    if domain:
                        domains.append(domain)
            elif in_track_b:
                if line_str.startswith("||") and "$dnsrewrite=NXDOMAIN" in line_str:
                    domain = line_str.replace("||", "").split("^")[0].strip()
                    if domain:
                        domains.append(domain)
    except Exception as e:
        print(f"Error parsing AGH rules: {e}")
        
    return sorted(list(set(domains)))

_agh_domains = load_agh_blocked_domains()


def sanitize_hostname(host):
    host = host.strip()
    # Remove protocol prefix if present
    host = re.sub(r'^https?://', '', host)
    # Remove path, port or query components
    host = host.split('/')[0].split(':')[0].split('?')[0]
    # Strip dots and whitespace
    host = host.strip('.')
    return host

def is_high_risk_mitm(host):
    host_lower = host.lower()
    clean_host = host_lower.replace('*', '').strip('.')
    for domain in HIGH_RISK_MITM_DOMAINS:
        if clean_host == domain or clean_host.endswith('.' + domain) or (domain + '.') in clean_host:
            return True
    return False


def should_bypass_rule_content(pattern_or_line):
    line_lower = pattern_or_line.lower()
    line_clean = line_lower.replace('\\.', '.').replace('\\', '')
    
    # 0. Bypass Tencent stats domains to prevent high frequency background retry loop (发热耗电根源)
    if "beacon.qq.com" in line_clean or "rqd.qq.com" in line_clean or "wup.imtt.qq.com" in line_clean:
        return True
        
    # 0. Bypass fragile Tieba protobuf script which causes blank pages
    if "tieba-proto.js" in line_lower:
        return True
        
    # 1. Specific Baidu Netdisk VIP rules that break VIP display/loading
    if "pan.baidu.com/pmall/order/privilege/info" in line_clean or \
       "pan.baidu.com/api/certuser/get" in line_clean or \
       ("pan.baidu.com/component/view/" in line_clean and "vip" in line_clean):
        return True
        
    # 2. Specific Zhihu config/MQTT retry-loop domains (发热与超时根源)
    if "api.zhihu.com/ab/api/v1/products/zhihu/platforms/ios/config" in line_clean or \
       "api.zhihu.com/ad-style-service/request" in line_clean or \
       "mqtt.zhihu.com" in line_clean or \
       "appcloud.zhihu.com" in line_clean:
        return True
        
    # Aliyun Beacon analytics bypass (防阿里系 App 闪退)
    if "beacon-api.aliyuncs.com" in line_clean:
        return True
        
    # 3. High risk domains in rewrites/scripts (since they require MITM to trigger)
    for domain in HIGH_RISK_MITM_DOMAINS:
        if domain in line_clean:
            return True
            
    # 4. Clean up weird/temporary timestamp domains and placeholder examples
    if "2026.06.02" in line_clean or "this-is-an-example" in line_clean:
        return True
        
    return False

def is_advanced_rewrite(rw_line):
    rw_line = rw_line.strip()
    if not rw_line or rw_line.startswith('#') or rw_line.startswith(';'):
        return False
    parts = rw_line.split()
    if len(parts) >= 2:
        action = parts[-1].lower()
        if action in ("reject-200", "reject-dict", "reject-img") or "header" in action:
            return True
    return False

def download_url(url):
    print(f"Downloading: {url}")
    # Local cache settings
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(base_dir, "scratch")
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    cache_path = os.path.join(cache_dir, f"cache_{url_hash}.txt")
    
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
            # Save successful download to cache
            os.makedirs(cache_dir, exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(content)
            return content
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        if os.path.exists(cache_path):
            print(f"[WARNING] Network request failed. Falling back to offline local cache: scratch/cache_{url_hash}.txt")
            with open(cache_path, "r", encoding="utf-8") as f:
                return f.read()
        return None

def clean_line_for_matching(line):
    return re.sub(r'[\^$?\\.*()[\]{}|+]', '', line).lower()

def identify_app(line):
    clean_line = clean_line_for_matching(line)
    for sdk_kw in ALWAYS_KEEP_KEYWORDS:
        if sdk_kw in clean_line:
            return "通用广告SDK", sdk_kw
            
    for app in INSTALLED_APPS:
        if app in APP_KEYWORDS:
            keywords = APP_KEYWORDS[app]
            for kw in keywords:
                if kw in clean_line:
                    return app, kw
                    
    if line.startswith("IP-CIDR"):
        return "通用IP分流", "ip-cidr"
        
    return None, None

def parse_qx_conf(content, app_name):
    rules = []
    rewrites = []
    scripts = []
    mitm_domains = set()
    
    lines = content.splitlines()
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("//") or line_stripped.startswith(";"):
            continue
            
        # Parse hostname line
        if line_stripped.startswith("hostname"):
            match = re.search(r'hostname\s*=\s*(.+)', line_stripped)
            if match:
                hosts_part = match.group(1).replace('%APPEND%', '').strip()
                # Split by comma and then split by whitespace/newlines to avoid concat bugs
                hosts = []
                for part in hosts_part.split(','):
                    for sub_h in part.split():
                        san_h = sanitize_hostname(sub_h)
                        if san_h:
                            hosts.append(san_h)
                for h in hosts:
                    if h and not is_high_risk_mitm(h):
                        mitm_domains.add(h)
            continue
            
        # Parse filter rules
        parts_comma = [p.strip() for p in line_stripped.split(',')]
        if len(parts_comma) >= 3 and parts_comma[0].lower() in ("host", "host-suffix", "host-keyword", "ip-cidr", "ip-cidr6"):
            rule_type = parts_comma[0].lower()
            domain = parts_comma[1]
            policy = parts_comma[2].upper()
            
            surge_type = None
            if rule_type == "host":
                surge_type = "DOMAIN"
            elif rule_type == "host-suffix":
                surge_type = "DOMAIN-SUFFIX"
            elif rule_type == "host-keyword":
                surge_type = "DOMAIN-KEYWORD"
            elif rule_type == "ip-cidr":
                surge_type = "IP-CIDR"
            elif rule_type == "ip-cidr6":
                surge_type = "IP-CIDR6"
                
            if surge_type:
                rules.append(f"{surge_type},{domain},{policy}")
            continue
            
        # Parse rewrite rules
        if " url " in line_stripped:
            parts = line_stripped.split()
            if len(parts) >= 3:
                pattern = parts[0]
                url_type = parts[2]
                
                if url_type == "jsonjq-response-body":
                    continue
                    
                if should_bypass_rule_content(pattern):
                    continue
                    
                # Skip duplicate Pinduoduo cappuccino/splash reject in favor of reject-200
                if url_type == "reject" and "cappuccino/splash" in pattern.lower().replace('\\', ''):
                    continue
                    
                if url_type in ("reject", "reject-200", "reject-dict"):
                    rewrites.append(f"{pattern} - {url_type}")
                elif url_type in ("script-response-body", "script-request-body", "script-response-header", "script-request-header", "script-analyze-echo-response", "script-analyze-echo-request"):
                    if len(parts) >= 4:
                        script_url = parts[3]
                        h = hashlib.md5(pattern.encode('utf-8')).hexdigest()[:6]
                        script_name = f"{app_name.lower()}_{h}"
                        
                        if "echo" in url_type:
                            req_body = "1"
                            script_type = "http-request"
                        else:
                            req_body = "1" if "body" in url_type else "0"
                            script_type = "http-response" if "response" in url_type else "http-request"
                        
                        script_def = f"{script_name} = type={script_type},pattern={pattern},script-path={script_url},requires-body={req_body}"
                        scripts.append(script_def)
                        
    return rules, rewrites, scripts, mitm_domains

def parse_surge_module(content):
    rules = []
    rewrites = []
    scripts = []
    mitm_domains = set()
    
    lines = content.splitlines()
    current_section = None
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("#") or line_stripped.startswith(";"):
            continue
            
        if line_stripped.startswith("[") and line_stripped.endswith("]"):
            current_section = line_stripped
            continue
            
        if current_section == "[Rule]":
            if not should_bypass_rule_content(line_stripped):
                rules.append(line_stripped)
        elif current_section == "[URL Rewrite]":
            if not should_bypass_rule_content(line_stripped):
                line_clean = line_stripped.lower().replace('\\', '')
                if "cappuccino/splash" in line_clean and line_clean.strip().endswith("reject"):
                    continue
                rewrites.append(line_stripped)
        elif current_section == "[Script]":
            if not should_bypass_rule_content(line_stripped):
                scripts.append(line_stripped)
        elif current_section == "[MITM]":
            if line_stripped.startswith("hostname"):
                match = re.search(r'hostname\s*=\s*%APPEND%\s*(.+)', line_stripped)
                if match:
                    hosts_raw = match.group(1).split(',')
                else:
                    match_direct = re.search(r'hostname\s*=\s*(.+)', line_stripped)
                    if match_direct:
                        hosts_raw = match_direct.group(1).split(',')
                    else:
                        hosts_raw = []
                
                hosts = []
                for part in hosts_raw:
                    for sub_h in part.split():
                        san_h = sanitize_hostname(sub_h)
                        if san_h:
                            hosts.append(san_h)
                            
                for h in hosts:
                    if h and not is_high_risk_mitm(h):
                        mitm_domains.add(h)
                        
    return rules, rewrites, scripts, mitm_domains

def extract_hosts_from_pattern(pattern):
    p = pattern.replace(r'\/', '/')
    p = re.sub(r'^\^?https?\??://', '', p)
    parts = p.split('/')
    host_part = parts[0]
    
    # Safeguard against IP address regex or excessively complex patterns
    if "255" in host_part or "25[0-5]" in host_part or host_part.count('|') > 5 or host_part.count(r'\d') > 3:
        return []
        
    # Clean up escape dots
    host_part = host_part.replace('\\.', '.')
    
    # Split top-level '|' choices (e.g. (114.115.217.129)|(home.umetrip.com)) using parentheses-matching
    top_parts = []
    current_part = []
    depth = 0
    for char in host_part:
        if char == '(':
            depth += 1
            current_part.append(char)
        elif char == ')':
            depth -= 1
            current_part.append(char)
        elif char == '|' and depth == 0:
            top_parts.append("".join(current_part))
            current_part = []
        else:
            current_part.append(char)
    top_parts.append("".join(current_part))
    
    hosts = [tp.strip() for tp in top_parts if tp.strip()]
    
    # 1. Expand capturing groups containing '|' (e.g. (pinduoduo|yangkeduo))
    max_expansions = 20
    has_or_group = True
    while has_or_group:
        if len(hosts) > max_expansions:
            return []
        new_hosts = []
        changed = False
        for h in hosts:
            match_group = re.search(r'\(([^)]*\|[^)]*)\)', h)
            if match_group:
                choices = match_group.group(1).split('|')
                prefix = h[:match_group.start()]
                suffix = h[match_group.end():]
                for choice in choices:
                    new_hosts.append(prefix + choice + suffix)
                changed = True
            else:
                new_hosts.append(h)
        hosts = new_hosts
        if not changed:
            has_or_group = False

    # 2. Expand (\d)? or \d? or (\d) or \d
    for _ in range(5):
        if len(hosts) > max_expansions:
            return []
        new_hosts = []
        changed = False
        for h in hosts:
            if r'(\d)?' in h or r'\d?' in h:
                h_target = r'(\d)?' if r'(\d)?' in h else r'\d?'
                idx = h.find(h_target)
                prefix = h[:idx]
                suffix = h[idx + len(h_target):]
                # Option 1: empty
                new_hosts.append(prefix + suffix)
                # Option 2: digits 0-9
                for d in "0123456789":
                    new_hosts.append(prefix + d + suffix)
                changed = True
            elif r'(\d)' in h or r'\d' in h:
                h_target = r'(\d)' if r'(\d)' in h else r'\d'
                idx = h.find(h_target)
                prefix = h[:idx]
                suffix = h[idx + len(h_target):]
                for d in "0123456789":
                    new_hosts.append(prefix + d + suffix)
                changed = True
            else:
                new_hosts.append(h)
        hosts = new_hosts
        if not changed:
            break
            
    cleaned_hosts = []
    for h in hosts:
        h = h.replace('\\', '')
        h = re.sub(r'\[[^\]]+\]\+?', '', h)
        h = re.sub(r'[^a-zA-Z0-9.-]', '', h)
        h = h.strip('.')
        if h:
            cleaned_hosts.append(h)
            
    return cleaned_hosts


def hostname_matches_pattern(host, pattern):
    clean_pat = pattern.replace('\\', '').replace('?', '').replace('^', '').replace('$', '')
    if host in clean_pat:
        return True
    if '*' in host:
        parts = host.split('*')
        if all(p in clean_pat for p in parts if p):
            return True
    return False


# =================================================================
# 🚀 动态同步机制：自动从 Clash /ini 仓 of sdkdomain.list 动态追加全部核心打点域名
# =================================================================
_sdkdomain_list_file = os.path.join(os.path.dirname(__file__), "../ini/sdkdomain.list")
if os.path.exists(_sdkdomain_list_file):
    print(f"Loading dynamic domains from: {_sdkdomain_list_file}")
    with open(_sdkdomain_list_file, "r", encoding="utf-8") as f:
        _dynamic_count = 0
        for _line in f.read().splitlines():
            _line = _line.strip()
            if not _line or _line.startswith("#"):
                continue
            _parts = _line.split(",")
            if len(_parts) >= 2:
                _dom = _parts[1].strip().lower()
                _rule = f"DOMAIN,{_dom},REJECT-NO-DROP"
                if _rule not in SDK_BLOCK_RULES:
                    SDK_BLOCK_RULES.append(_rule)
                    _dynamic_count += 1
    print(f"Dynamically appended {_dynamic_count} domains from sdkdomain.list into SDK_BLOCK_RULES.")
else:
    print(f"Warning: {_sdkdomain_list_file} not found! Dynamic alignment fallback.")

# =================================================================
# 🚀 双端联动：自动从本地 AdGuard Home 自定义规则 (Track A + Track B) 动态加载全部核心拦截域名并强制统一为 REJECT-NO-DROP
# =================================================================
_agh_count = 0
for _dom in _agh_domains:
    _rule = f"DOMAIN,{_dom},REJECT-NO-DROP"
    if _rule not in SDK_BLOCK_RULES:
        SDK_BLOCK_RULES.append(_rule)
        _agh_count += 1
print(f"Dynamically appended {_agh_count} domains from AdGuard Home (Track A + B) into SDK_BLOCK_RULES.")



def extract_pattern(line, is_script=False):
    line_stripped = line.strip()
    if is_script:
        match = re.search(r'pattern=([^,]+)', line_stripped)
        if match:
            return match.group(1)
    else:
        parts = line_stripped.split()
        if len(parts) >= 2:
            return parts[0]
    return line_stripped

DYNAMIC_REJECT_APP_FILTERS = {
    "Outlook": [r"outlookads\.live\.com"],
    "LinkedIn": [r"ads\.linkedin\.com", r"analytics\.pointdrive\.linkedin\.com"],
    "Firefox": [r"firefoxchina\.cn"]
}

def fetch_and_extract_dynamic_rules(target_apps):
    import urllib.request
    import urllib.error
    dynamic_rules = []
    url = "https://johnshall.github.io/Shadowrocket-ADBlock-Rules-Forever/sr_ad_only.conf"
    
    print("Downloading Johnshall rules for dynamic extraction...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
            
        for line in content.splitlines():
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                continue
            
            parts = line_stripped.split(",")
            if len(parts) >= 2 and parts[-1].strip().lower() == "reject":
                domain = parts[1].strip().lower()
                
                # Check pattern matches for targets
                for app in target_apps:
                    if app in DYNAMIC_REJECT_APP_FILTERS:
                        for pattern in DYNAMIC_REJECT_APP_FILTERS[app]:
                            if re.search(pattern, domain):
                                standard_rule = f"{parts[0].strip()},{domain},REJECT"
                                dynamic_rules.append(standard_rule)
                                break
                            
        print(f"Successfully extracted {len(dynamic_rules)} dynamic rules from Johnshall's conf.")
    except Exception as e:
        print(f"Warning: Could not fetch dynamic rules locally ({e}). Using static cache.")
        
    return list(set(dynamic_rules))

def generate():
    import os
    supported_apps = set(APP_KEYWORDS.keys()) | set(OVERRIDE_APPS.keys())
    unsupported_installed_apps = [app for app in INSTALLED_APPS if app not in supported_apps]
    
    IS_GITHUB_ACTIONS = "GITHUB_ACTIONS" in os.environ
    FORCE_FETCH = "FORCE_FETCH" in os.environ
    if IS_GITHUB_ACTIONS or FORCE_FETCH:
        dynamic_rules = fetch_and_extract_dynamic_rules(unsupported_installed_apps)
        SDK_BLOCK_RULES.extend(dynamic_rules)
        print(f"Added {len(dynamic_rules)} dynamic rules into SDK_BLOCK_RULES.")

    # 1. Download and parse BlackMatrix7 AllInOne
    aio_url = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/Shadowrocket/AllInOne/AllInOne.sgmodule"
    aio_content = download_url(aio_url)
    if not aio_content:
        print("Error: Could not download BlackMatrix7 AllInOne")
        sys.exit(1)
        
    print("Parsing BlackMatrix7 AllInOne...")
    aio_rules, aio_rewrites, aio_scripts, aio_mitm = parse_surge_module(aio_content)
    
    raw_rules = []
    raw_rewrites = []
    raw_scripts = []
    
    # Process BM7 Rules
    for r in aio_rules:
        app, kw = identify_app(r)
        if app and app in INSTALLED_APPS:
            if not should_bypass_rule_content(r):
                raw_rules.append({'text': r, 'pattern': r, 'priority': 2, 'app': app})
            
    # Process BM7 Rewrites
    for rw in aio_rewrites:
        app, kw = identify_app(rw)
        if app and app in INSTALLED_APPS:
            if not should_bypass_rule_content(rw):
                pat = extract_pattern(rw, is_script=False)
                raw_rewrites.append({'text': rw, 'pattern': pat, 'priority': 2, 'app': app})
                
    # Process BM7 Scripts
    for s in aio_scripts:
        app, kw = identify_app(s)
        if app and app in INSTALLED_APPS:
            if app in OVERRIDE_APPS:
                continue
            if not should_bypass_rule_content(s):
                pat = extract_pattern(s, is_script=True)
                raw_scripts.append({'text': s, 'pattern': pat, 'priority': 2, 'app': app})
            
    # 3. Fetch and parse Override Apps (ddgksf2013, Maasea, fmz200 etc.)
    override_mitm = set()
    all_urls = [aio_url]
    for app_name, urls in OVERRIDE_APPS.items():
        if isinstance(urls, str):
            all_urls.append(urls)
        elif isinstance(urls, list):
            all_urls.extend(urls)
            
    # Parallel pre-fetch all URLs to reduce execution time to < 1.5s
    from concurrent.futures import ThreadPoolExecutor
    print(f"Parallel pre-fetching {len(all_urls)} rule source URLs...")
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(download_url, all_urls)

    for app_name, urls in OVERRIDE_APPS.items():
        installed_name = None
        if app_name == "微博轻享版":
            if "微博轻享版" in INSTALLED_APPS or "微博" in INSTALLED_APPS:
                installed_name = "微博轻享版"
        elif app_name in INSTALLED_APPS:
            installed_name = app_name
            
        if not installed_name:
            continue
            
        if isinstance(urls, str):
            urls = [urls]
            
        for url in urls:
            priority = 4
            if "ddgksf2013" in url or "StartUpAds" in url:
                priority = 1
            elif "Maasea" in url:
                priority = 3
                
            content = download_url(url)
            if not content:
                continue
                
            if app_name == "SOUL":
                cleaned_lines = []
                for line in content.split('\n'):
                    line_str = line.strip()
                    if not line_str or line_str.startswith('//') or line_str.startswith(';'):
                        cleaned_lines.append(line)
                        continue
                    if line_str.startswith('#'):
                        cleaned_lines.append(line)
                        continue
                    if line_str.startswith('hostname'):
                        parts = line_str.split('=', 1)
                        hosts = [h.strip() for h in parts[1].split(',')]
                        cleaned_hosts = [h for h in hosts if 'soul' in h.lower() or h.startswith('47.') or h.startswith('120.') or h.startswith('121.')]
                        cleaned_lines.append(f"hostname = {', '.join(cleaned_hosts)}")
                        continue
                    if 'soul' in line_str.lower() or any(ip in line_str for ip in ['47.110.187.87', '47.56.131.76', '47.97.215.55', '47.99.42.29', '47.243.147.125', '120.27.235.201', '121.196.197.147']):
                        cleaned_lines.append(line)
                content = '\n'.join(cleaned_lines)
                
            if url.endswith(".sgmodule"):
                r, rw, s, m = parse_surge_module(content)
            else:
                r, rw, s, m = parse_qx_conf(content, app_name)
                
            for rule in r:
                if not should_bypass_rule_content(rule):
                    raw_rules.append({'text': rule, 'pattern': rule, 'priority': priority, 'app': app_name})
            for rewrite in rw:
                if not should_bypass_rule_content(rewrite):
                    pat = extract_pattern(rewrite, is_script=False)
                    raw_rewrites.append({'text': rewrite, 'pattern': pat, 'priority': priority, 'app': app_name})
            for script in s:
                if not should_bypass_rule_content(script):
                    pat = extract_pattern(script, is_script=True)
                    raw_scripts.append({'text': script, 'pattern': pat, 'priority': priority, 'app': app_name})
            override_mitm.update(m)
            
    # 4. Inject Extra domain rejects as DOMAIN rules
    for app_name, domains in EXTRA_REWRITE_DOMAINS.items():
        if app_name in INSTALLED_APPS:
            for domain in domains:
                domain_san = sanitize_hostname(domain)
                if not is_high_risk_mitm(domain_san):
                    rule_text = f"DOMAIN,{domain_san},REJECT-200"
                    raw_rules.append({'text': rule_text, 'pattern': rule_text, 'priority': 1, 'app': app_name})
            print(f" - [RULE INJECTION] {app_name}: {len(domains)} domains injected as rules")
            
    # Inject Universal Ad SDK Rejects as DOMAIN rules
    for domain in ALWAYS_INJECT_DOMAINS:
        domain_san = sanitize_hostname(domain)
        if not is_high_risk_mitm(domain_san):
            rule_text = f"DOMAIN,{domain_san},REJECT-200"
            raw_rules.append({'text': rule_text, 'pattern': rule_text, 'priority': 1, 'app': "通用广告SDK"})
            
    # Inject Custom Rewrite Rules
    for item in CUSTOM_REWRITE_RULES:
        if item['app'] in INSTALLED_APPS:
            raw_rewrites.append(item)
            
    # Sort by priority ascending (1 highest, then 2, 3, 4)
    raw_rules.sort(key=lambda x: x['priority'])
    raw_rewrites.sort(key=lambda x: x['priority'])
    raw_scripts.sort(key=lambda x: x['priority'])
    
    # Deduplicate rules, rewrites, and scripts keeping higher priority first
    final_rules = []
    seen_rules = set()
    for item in raw_rules:
        text_clean = item['text'].strip()
        if text_clean not in seen_rules:
            seen_rules.add(text_clean)
            final_rules.append(text_clean)
    # 智能过滤被 DOMAIN-SUFFIX 或 DOMAIN-KEYWORD REJECT 覆盖的冗余规则
    suffix_rejects = set()
    keyword_rejects = set()
    for r in final_rules:
        parts = r.split(',')
        if len(parts) >= 3 and parts[2].upper() == "REJECT":
            rule_type = parts[0].upper()
            domain = parts[1].lower()
            if rule_type == "DOMAIN-SUFFIX":
                suffix_rejects.add(domain)
            elif rule_type == "DOMAIN-KEYWORD":
                keyword_rejects.add(domain)
                
    optimized_rules = []
    for r in final_rules:
        parts = r.split(',')
        if len(parts) >= 3 and parts[2].upper() == "REJECT":
            rule_type = parts[0].upper()
            domain = parts[1].lower()
            
            # 检查是否能被更广范的 DOMAIN-KEYWORD REJECT 覆盖
            is_covered_by_keyword = False
            for kw in keyword_rejects:
                if kw in domain and rule_type in ("DOMAIN", "DOMAIN-SUFFIX"):
                    if kw != domain:
                        is_covered_by_keyword = True
                        break
            if is_covered_by_keyword:
                continue
                
            # 检查是否能被更广范的 DOMAIN-SUFFIX REJECT 覆盖
            if rule_type == "DOMAIN":
                is_covered_by_suffix = False
                for suffix in suffix_rejects:
                    if domain.endswith('.' + suffix):
                        is_covered_by_suffix = True
                        break
                if is_covered_by_suffix:
                    continue
                    
            # 检查 DOMAIN 与 DOMAIN-SUFFIX 完全同域并存的情况
            if rule_type == "DOMAIN" and domain in suffix_rejects:
                continue
                
        optimized_rules.append(r)
    final_rules = optimized_rules

            
    final_rewrites = []
    for item in raw_rewrites:
        pat = item['pattern']
        app = item['app']
        overlap = False
        for existing in final_rewrites:
            # 1. Global identical pattern check (regardless of app)
            if pat == existing['pattern']:
                overlap = True
                break
                
            # 2. Global overlap check for known core ad endpoints across apps
            pat_clean = pat.replace('\\', '')
            exist_clean = existing['pattern'].replace('\\', '')
            global_overlap_endpoints = [
                ("api.douban.com", "app_ads/splash"),
                ("frodo.douban.com", "app_ads/splash"),
                ("frodo.douban.com", "erebor/feed_ad"),
                ("frodo.douban.com", "home_banner"),
                ("frodo.douban.com", "search/found_words"),
                ("c.tieba.baidu.com", "splashSchedule"),
                ("c.tieba.baidu.com", "getAdInfo"),
                ("tiebac.baidu.com", "getFeedAd"),
                ("tieba.baidu.com", "getFeedAd")
            ]
            kw_overlap = False
            for domain_kw, path_kw in global_overlap_endpoints:
                if (domain_kw in pat_clean and path_kw in pat_clean) and (domain_kw in exist_clean and path_kw in exist_clean):
                    kw_overlap = True
                    break
            if kw_overlap:
                overlap = True
                break

            # 3. Traditional app-specific overlap check
            if existing['app'] == app:
                core_endpoints = ["frs/page", "pb/page", "getFeedAd", "getAdList"]
                for ep in core_endpoints:
                    if ep in pat and ep in existing['pattern']:
                        overlap = True
                        break
                if overlap:
                    break
        if not overlap:
            final_rewrites.append(item)
    final_rewrites_texts = [x['text'] for x in final_rewrites]
            
    final_scripts = []
    for item in raw_scripts:
        pat = item['pattern']
        app = item['app']
        overlap = False
        for existing in final_scripts:
            if existing['app'] == app:
                if pat == existing['pattern']:
                    overlap = True
                    break
                core_endpoints = ["frs/page", "pb/page", "getFeedAd", "getAdList"]
                for ep in core_endpoints:
                    if ep in pat and ep in existing['pattern']:
                        overlap = True
                        break
                if overlap:
                    break
        if not overlap:
            final_scripts.append(item)
    final_scripts_texts = [x['text'] for x in final_scripts]
            
    # Two-pass cappuccino/splash deduplication and iQIYI reject conversion
    has_group_pdd = any(
        "cappuccino/splash" in rw.lower().replace('\\', '') and 
        "pinduoduo" in rw.lower() and "yangkeduo" in rw.lower()
        for rw in final_rewrites_texts
    )
    
    optimized_rewrites = []
    for rw in final_rewrites_texts:
        rw_stripped = rw.strip()
        if "cappuccino/splash" in rw_stripped.lower().replace('\\', ''):
            if has_group_pdd and not ("pinduoduo" in rw_stripped.lower() and "yangkeduo" in rw_stripped.lower()):
                continue
                
        if "iqiyi" in rw_stripped.lower() or "qiyi" in rw_stripped.lower():
            parts = rw_stripped.split()
            if len(parts) >= 3 and parts[1] == "-":
                action = parts[2].lower()
                if action in ("reject", "reject-img"):
                    rw_stripped = f"{parts[0]} - reject-200"
                    
        optimized_rewrites.append(rw_stripped)
    final_rewrites = list(dict.fromkeys(optimized_rewrites))
    final_scripts = list(dict.fromkeys(final_scripts_texts))
    
    # 自动筛查并剔除与 Script 动态清洗冲突的同路径静态 REJECT 重写
    def patterns_conflict(rew_pat, scr_pat):
        def clean(p):
            return p.replace('\\', '').replace('^', '').replace('$', '').replace('?', '').strip()
        c_rew = clean(rew_pat)
        c_scr = clean(scr_pat)
        if c_rew == c_scr or (c_rew in c_scr and len(c_scr) - len(c_rew) < 15) or (c_scr in c_rew and len(c_rew) - len(c_scr) < 15):
            return True
        return False

    script_patterns = []
    for s in final_scripts:
        match = re.search(r'pattern=([^,]+)', s)
        if match:
            script_patterns.append(match.group(1).strip())

    clean_rewrites = []
    for rw in final_rewrites:
        parts = rw.split()
        if len(parts) >= 3 and parts[1] == '-':
            action = parts[2].lower()
            if "reject" in action:
                pat = parts[0].strip()
                conflict = False
                for scr_pat in script_patterns:
                    if patterns_conflict(pat, scr_pat):
                        print(f"[CONFLICT FILTER] Removed redundant rewrite '{pat}' because it conflicts with script '{scr_pat}'")
                        conflict = True
                        break
                if conflict:
                    continue
        clean_rewrites.append(rw)
    final_rewrites = clean_rewrites

    # Exclude any rule that is exactly in SDK_BLOCK_RULES
    sdk_set = set(SDK_BLOCK_RULES)
    final_rules = [r for r in final_rules if r not in sdk_set]
    
    # 5. MITM domains processing (Highly Optimized)
    candidate_mitm = set(aio_mitm).union(override_mitm)
    
    final_mitm = set()
    for host in candidate_mitm:
        host_san = sanitize_hostname(host)
        if not host_san or is_high_risk_mitm(host_san):
            continue
            
        if '*' in host_san:
            for s in final_scripts:
                match = re.search(r'pattern=([^,]+)', s)
                if match:
                    pattern = match.group(1)
                    if hostname_matches_pattern(host_san, pattern):
                        extracted_hosts = extract_hosts_from_pattern(pattern)
                        for eh in extracted_hosts:
                            eh_san = sanitize_hostname(eh)
                            if eh_san and not is_high_risk_mitm(eh_san):
                                if hostname_matches_pattern(host_san, "https://" + eh_san):
                                    final_mitm.add(eh_san)
            for rw in final_rewrites:
                if is_advanced_rewrite(rw):
                    parts = rw.split()
                    if parts:
                        pattern = parts[0]
                        if hostname_matches_pattern(host_san, pattern):
                            extracted_hosts = extract_hosts_from_pattern(pattern)
                            for eh in extracted_hosts:
                                eh_san = sanitize_hostname(eh)
                                if eh_san and not is_high_risk_mitm(eh_san):
                                    if hostname_matches_pattern(host_san, "https://" + eh_san):
                                        final_mitm.add(eh_san)
        else:
            matched = False
            for s in final_scripts:
                match = re.search(r'pattern=([^,]+)', s)
                if match:
                    pattern = match.group(1)
                    if hostname_matches_pattern(host_san, pattern):
                        final_mitm.add(host_san)
                        matched = True
                        break
            if matched:
                continue
                
            for rw in final_rewrites:
                if is_advanced_rewrite(rw):
                    parts = rw.split()
                    if parts:
                        pattern = parts[0]
                        if hostname_matches_pattern(host_san, pattern):
                            final_mitm.add(host_san)
                            break
                        
    # Sort and final filter, cleaning up any wildcards
    cleaned_mitm = set()
    for h in final_mitm:
        h_clean = h.replace('*.', '').replace('*', '').strip('.')
        if h_clean and '.' in h_clean and not is_high_risk_mitm(h_clean):
            cleaned_mitm.add(h_clean)
            
    # Force include WeChat unblock domains if enabled
    if "微信解除链接限制" in INSTALLED_APPS:
        cleaned_mitm.add("weixin110.qq.com")
        cleaned_mitm.add("security.wechat.com")
        
    # Force include mandatory MITM domains
    for h in MANDATORY_MITM_DOMAINS:
        cleaned_mitm.add(h)
        
    final_mitm = sorted(list(cleaned_mitm))
    
    print("\n--- FINAL BUILD SUMMARY ---")
    print(f"Total Rules count: {len(final_rules) + len(SDK_BLOCK_RULES)}")
    print(f"Total Rewrites count: {len(final_rewrites)}")
    print(f"Total Scripts count: {len(final_scripts)}")
    print(f"Total MITM Hostnames count: {len(final_mitm)}")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(script_dir) == 'scratch':
        script_dir = os.path.dirname(script_dir)
    output_path = os.path.join(script_dir, "custom_adblock.sgmodule")
    
    import datetime
    utc_now = datetime.datetime.utcnow()
    beijing_now = utc_now + datetime.timedelta(hours=8)
    beijing_time_str = beijing_now.strftime('%Y-%m-%d %H:%M:%S')
    
    BYPASS_RULES = [x for x in _s_data["BYPASS_RULES"] if not x.startswith("#") or "Bypass Rules" in x]

    # 动态排除 AGH 的打点/拦截域名及字节 TNC 相关，防止编译生成的 final_rules 等地方带入普通 REJECT 或重写
    _filter_domains = set(_agh_domains) | {"pglstatp-toutiao.com"}
    final_rules = [r for r in final_rules if not any(d in r.lower() for d in _filter_domains)]
    final_rewrites = [r for r in final_rewrites if not any(d in r.lower() for d in _filter_domains)]
    final_scripts = [s for s in final_scripts if not any(d in s.lower() for d in _filter_domains)]
    final_mitm = [m for m in final_mitm if not any(d in m.lower() for d in _filter_domains)]
    final_bypass = [r for r in BYPASS_RULES if not any(d in r.lower() for d in _filter_domains)]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#!name=custom apps adblock.sgmodule\n")
        f.write(f"#!desc=最近更新: {beijing_time_str} | Deep ad block & UI purification customized for user's installed apps.\n")
        f.write(f"#!total={len(final_rules) + len(SDK_BLOCK_RULES) + len(final_rewrites) + len(final_scripts) + len(final_bypass)}\n\n")
        
        if final_rules or SDK_BLOCK_RULES or final_bypass:
            EXCLUDED_DOMAINS = ["firebaselogging-pa.googleapis.com"]
            f.write("[Rule]\n")
            for line in final_bypass:
                f.write(line + "\n")
            f.write("# === SDK Core REJECT Rules ===\n")
            for line in SDK_BLOCK_RULES:
                if any(ex in line for ex in EXCLUDED_DOMAINS):
                    continue
                f.write(line + "\n")
            f.write("# === Compiled App Rules ===\n")
            for line in final_rules:
                if any(ex in line for ex in EXCLUDED_DOMAINS):
                    continue
                f.write(line + "\n")
            f.write("\n")
            
        if final_rewrites:
            f.write("[URL Rewrite]\n")
            for line in final_rewrites:
                f.write(line + "\n")
            f.write("\n")
            
        if final_scripts:
            f.write("[Script]\n")
            for line in final_scripts:
                f.write(line + "\n")
            f.write("\n")
            
        if final_mitm:
            f.write("[MITM]\n")
            hostnames_str = ",".join(final_mitm)
            f.write(f"hostname = %APPEND% {hostnames_str}\n")
            
    print(f"\nSuccessfully generated custom V2 module at: {output_path}")

    # Self-validation block to prevent line breaks or invalid hostname characters
    print("Running generated module self-validation...")
    with open(output_path, "r", encoding="utf-8") as f:
        val_lines = f.readlines()
        
    errors = 0
    for idx, line in enumerate(val_lines):
        line_str = line.strip()
        if line_str.endswith("-"):
            print(f"Error: Line {idx+1} ends with a trailing hyphen: {repr(line)}")
            errors += 1
        if line_str in ("reject", "reject-200", "reject-dict", "reject-img"):
            print(f"Error: Line {idx+1} contains only action keyword: {repr(line)}")
            errors += 1
        if idx >= len(val_lines) - 5 and "hostname" in line_str:
            hosts = line_str.replace("hostname =", "").replace("%APPEND%", "").split(",")
            for host in hosts:
                host = host.strip()
                if "://" in host or "/" in host or ":" in host or " " in host or not host:
                    print(f"Error: Invalid hostname in MITM list: {repr(host)}")
                    errors += 1
                    
    if errors > 0:
        print(f"Validation failed with {errors} errors! Please inspect the output file.")
        sys.exit(1)
    else:
        print("Self-validation passed successfully!")


if __name__ == "__main__":
    generate()
