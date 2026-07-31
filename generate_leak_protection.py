import os
import json
import datetime

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "references", "leak_protection_config.json")
    output_path = os.path.join(script_dir, "leak_protection.sgmodule")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    general = config.get("general", {})
    leak_test_proxy = config.get("leak_test_proxy_domains", [])
    custom_direct = config.get("custom_direct_domains", [])
    rule_sets = config.get("rule_sets", [])

    utc_now = datetime.datetime.utcnow()
    beijing_now = utc_now + datetime.timedelta(hours=8)
    beijing_time_str = beijing_now.strftime('%Y-%m-%d %H:%M:%S')

    dns_direct_system = "true" if general.get("dns_direct_system", False) else "false"
    dns_fallback_system = "true" if general.get("dns_fallback_system", False) else "false"
    dns_servers = ", ".join(general.get("dns_server", []))
    direct_dns_servers = ", ".join(general.get("direct_dns_server", []))
    hijack_dns_servers = ", ".join(general.get("hijack_dns", []))
    dns_mode = general.get("dns_mode", "fake-ip")
    fake_ip_filters = ", ".join(general.get("fake_ip_filter", []))

    lines = []
    lines.append("#!name=防泄露与分流优化模块(强化版)")
    lines.append(f"#!desc=最近更新: {beijing_time_str} | 包含 0 DNS/WebRTC 泄露防护、DNS 劫持强化、Fake-IP 优化与精细分流\n")

    lines.append("[General]")
    lines.append("# 1. 禁用系统自带 DNS 转发，强制小火箭接管")
    lines.append(f"dns-direct-system = {dns_direct_system}")
    lines.append(f"dns-fallback-system = {dns_fallback_system}\n")

    lines.append("# 2. 强制系统 DNS 劫持 (拦截所有 53 端口暗度陈仓流量)")
    lines.append(f"hijack-dns = {hijack_dns_servers}\n")

    lines.append("# 3. 远程加密 DNS (含 8.8.8.8/1.1.1.1 引导 IP，防止 DoH 解析死锁)")
    lines.append(f"dns-server = {dns_servers}\n")

    lines.append("# 4. 国内直连专属 DNS (阿里/腾讯 DoH 极速解析)")
    lines.append(f"direct-dns-server = {direct_dns_servers}\n")

    lines.append("# 5. 全局 Fake-IP 模式 (远端节点解析，杜绝 DNS 泄露)")
    lines.append(f"dns-mode = {dns_mode}\n")

    lines.append("# 6. 必须使用 Real-IP 的域名列表 (保护微信音视频、局域网 mDNS、系统校时)")
    lines.append(f"fake-ip-filter = {fake_ip_filters}\n")

    lines.append("[Rule]")
    lines.append("# ==========================================")
    lines.append("# 1. 局域网与内网直连 (最高优先级，保障 NAS/软路由连接)")
    lines.append("# ==========================================")
    lines.append("IP-CIDR,10.0.0.0/8,DIRECT")
    lines.append("IP-CIDR,172.16.0.0/12,DIRECT")
    lines.append("IP-CIDR,192.168.0.0/16,DIRECT")
    lines.append("IP-CIDR,127.0.0.0/8,DIRECT")
    lines.append("IP-CIDR,224.0.0.0/4,DIRECT")
    lines.append("GEOIP,LAN,DIRECT\n")

    lines.append("# ==========================================")
    lines.append("# 2. 封堵 WebRTC / STUN 泄露 (阻断真实 IP 探针)")
    lines.append("# ==========================================")
    lines.append("DOMAIN-KEYWORD,stun,REJECT")
    lines.append("DOMAIN-KEYWORD,turn,REJECT")
    lines.append("DOMAIN-SUFFIX,stun.l.google.com,REJECT")
    lines.append("AND,((PROTOCOL,UDP),(DEST-PORT,3478)),REJECT")
    lines.append("AND,((PROTOCOL,UDP),(DEST-PORT,5349)),REJECT\n")

    lines.append("# ==========================================")
    lines.append("# 3. 防泄露测试网站强走代理 (防止 GEOIP 判断前触发本地 DNS 查询)")
    lines.append("# ==========================================")
    for domain in leak_test_proxy:
        lines.append(f"DOMAIN-SUFFIX,{domain},PROXY")
    lines.append("")

    lines.append("# ==========================================")
    lines.append("# 4. 自动直连域名")
    lines.append("# ==========================================")
    for domain in custom_direct:
        lines.append(f"DOMAIN-SUFFIX,{domain},DIRECT")
    lines.append("")

    lines.append("# ==========================================")
    lines.append("# 5. 远程规则集精细分流")
    lines.append("# ==========================================")
    for rs in rule_sets:
        lines.append(f"RULE-SET,{rs['url']},{rs['policy']}")
    lines.append("")

    lines.append("# ==========================================")
    lines.append("# 6. 国内 IP 直连与最终兜底")
    lines.append("# ==========================================")
    lines.append("GEOIP,CN,DIRECT")
    lines.append("FINAL,PROXY")

    content = "\n".join(lines) + "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully generated leak_protection.sgmodule at: {output_path}")

if __name__ == "__main__":
    main()
