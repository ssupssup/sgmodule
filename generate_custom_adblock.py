import urllib.request
import re
import sys
import hashlib
import os
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# User's installed apps (excluding China Unicom)
INSTALLED_APPS = [
    "BookPlayer", "微信", "FTPManager", "AVPlayer", "VLC", "海贝音乐", "MOMO陌陌", "EZMP3Pro", "抖音", 
    "Edge Gallery", "探探", "闲鱼", "Telegram", "钉钉", "航旅纵横", "豆包", "夸克", "京东", "豆瓣", 
    "LocalSend", "百度网盘", "支付宝", "Chrome", "哔哩哔哩", "剪映", "百度地图", "淘宝", "网易云音乐", 
    "今日头条", "TikTok", "SOUL", "小红书", "米家", "铁路12306", "美团", "Ever Play", "知乎", "美图秀秀", 
    "大众点评", "iSub", "携程旅行", "萤石云视频", "GoodReader", "南方航空", "币安", "Gmail", "Bitget Wallet", 
    "滴滴企业版", "千问", "腾讯视频", "Edge", "上海银行", "优酷", "多邻国", "芒果TV", "百度贴吧", "QQ音乐", 
    "X", "Instagram", "Facebook", "KakaoTalk", "贝壳找房", "Bybit", "一嗨租车", "汽车之家", "网易邮箱大师", 
    "Word", "网易新闻", "Outlook", "PayPal", "腾讯会议", "Google Maps", "Google", "LinkedIn", "宝宝树孕育", 
    "中信银行", "腾讯新闻", "Tinder", "爱奇艺", "北京一卡通", "M365 Copilot", "PowerPoint", "Excel", "华夏银行", 
    "X Corp.", "涨乐财富通", "Wise", "滴滴", "叮咚买菜", "LINE", "交管12123", "中国国航", "YouTube", "北京银行", 
    "航班管家", "Chat", "去哪儿旅行", "阿里云盘", "首旅如家", "Firefox", "光大银行", "WhatsApp", "华住会", "SAVO", 
    "中国建设银行", "浦发银行", "招商银行", "万年历纯净版", "Gemini", "58同城", "东方航空", "拼多多", 
    "Clubhouse", "Bumble", "随手记", "MEGA", "Snapseed", "掌上生活", "欧路词典", "Grok", "首汽约车", "蜻蜓FM", 
    "个人所得税", "神州租车", "QQ邮箱", "Spotify", "ChatGPT", "易捷加油", "向日葵", "宝宝知道", "下厨房", "艺龙旅行", 
    "小米音箱", "海南航空", "Voice", "Copilot", "Manus", "云闪付", "NotebookLM", "小米商城", "微博轻享版", 
    "GoFun出行", "Orion", "多点", "Claude", "XChat", "DeepL", "Hiddify", "Authenticator", "Speedtest", 
    "数字人民币", "Google Earth", "伴生活", "厦门航空", "Shadowrocket", "锦江荟", "Swiftfin iOS", "Karing", 
    "天气通Pro", "城通网盘", "FTP Rush", "ShadowShare", "Clash Mi", "新浪邮箱", "AdBlocker", "凤凰视频", 
    "OPlayer Lite", "速8酒店", "小米WiFi", "购物党", "Talkatone", "资和信亿方", "小米电视助手", "DeepSeek", 
    "中国联合航空", "RustDesk", "EasyConnect", "Poe", "亚马逊购物", "sing-box", "PrivadoVPN", "北京燃气", 
    "AMonitor", "mimi 听力测试", "北京公积金", "图乐园", "Microsoft Corporation", "Kodi Remote", "通用开屏广告",
    "微信解除链接限制"
]

# App keywords mapping for BlackMatrix7 filtering (excluding China Unicom)
APP_KEYWORDS = {
    "微信": ["wechat", "applet", "tenpay", "weixin"],
    "哔哩哔哩": ["bilibili", "biliintl", "biliapi", "bili"],
    "知乎": ["zhihu"],
    "微博轻享版": ["weibo", "weico"],
    "豆瓣": ["douban"],
    "闲鱼": ["goofish", "idle", "taobao.idle"],
    "网易云音乐": ["netease", "music.163", "music.126", "163.com", "126.net"],
    "百度贴吧": ["tieba"],
    "高德地图": ["amap"],
    "百度地图": ["baidu.com/client", "map.baidu", "baidu.com/baidu"],
    "支付宝": ["alipay"],
    "美团": ["meituan", "wmapi.meituan"],
    "大众点评": ["dianping"],
    "今日头条": ["toutiao"],
    "小红书": ["xiaohongshu", "xhs", "edith.xiaohongshu"],
    "去哪儿旅行": ["qunar"],
    "携程旅行": ["ctrip"],
    "南方航空": ["csair"],
    "厦门航空": ["xiamenair"],
    "海南航空": ["hnair"],
    "中国国航": ["airchina"],
    "东方航空": ["ceair"],
    "华住会": ["huazhu"],
    "首旅如家": ["bthhotels", "homeinns"],
    "58同城": ["app.58.com", "58.com"],
    "拼多多": ["pinduoduo", "yangkeduo"],
    "车来了": ["chelaile"],
    "网易邮箱大师": ["neteasemail", "mail.163"],
    "宝宝树孕育": ["babytree"],
    "腾讯新闻": ["qqnews", "inews.qq.com"],
    "爱奇艺": ["iqiyi"],
    "优酷": ["youku"],
    "芒果TV": ["mgtv"],
    "腾讯视频": ["qqvideo", "video.qq.com"],
    "叮咚买菜": ["ddxq"],
    "下厨房": ["xiachufang"],
    "中国移动": ["10086", "chinamobile"],
    "中国电信": ["189.cn", "chinatelecom"],
    "星巴克": ["starbucks"],
    "麦当劳": ["mcd.cn"],
    "肯德基": ["kfc.com"],
    "顺丰速运": ["sf-express"],
    "中通快递": ["zto.com"],
    "个人所得税": ["chinatax"],
    "铁路12306": ["12306"],
    "同程旅行": ["ly.com", "17usoft"],
    "航班管家": ["feeyo"],
    "艺龙旅行": ["elong"],
    "QQ音乐": ["qqmusic", "music.qq.com", "tencentmusic", "y.qq.com"],
    "淘宝": ["taobao", "alicdn", "alimama"],
    "京东": ["jd.com", "360buy", "jdcloud"],
    "一嗨租车": ["1hi", "yihi"],
    "神州租车": ["zuche"],
    "首汽约车": ["01zhuanche", "shouqiev"],
    "滴滴": ["diditaxi", "didapinche", "xiaojukeji", "didi"],
    "招商银行": ["cmbchina", "cmb"],
    "掌上生活": ["cmbchina", "cmb"],
    "中信银行": ["ecitic"],
    "北京银行": ["bankofbeijing", "bob"],
    "上海银行": ["bankofshanghai", "bos"],
    "浦发银行": ["spdb"],
    "光大银行": ["cebbank"],
    "华夏银行": ["hxb"],
    "中国建设银行": ["ccb.com"],
    "随手记": ["suishouji"],
    "欧路词典": ["eudic"],
    "城通网盘": ["ctfile", "ctpocket"],
    "天气通Pro": ["tianqitong", "weathercn"],
    "凤凰视频": ["ifeng"],
    "OPlayer Lite": ["oplayer"],
    "速8酒店": ["super8"],
    "小米WiFi": ["miwifi"],
    "米家": ["mihome", "xiaomi"],
    "小米商城": ["mi.com"],
    "抖音": ["amemv", "douyin", "snssdk"],
    "TikTok": ["tiktok", "musical.ly"],
    "SOUL": ["soul"],
    "Tinder": ["tinder"],
    "Bumble": ["bumble"],
    "Clubhouse": ["clubhouse"],
    "Instagram": ["instagram"],
    "Facebook": ["facebook"],
    "Telegram": ["telegram"],
    "WhatsApp": ["whatsapp"],
    "LINE": ["line.me"],
    "KakaoTalk": ["kakaotalk"],
    "X": ["twitter", "x.com"],
    "YouTube": ["youtube", "googlevideo"],
    "Spotify": ["spotify"],
    "ChatGPT": ["openai"],
    "Gemini": ["gemini.google"],
    "Claude": ["anthropic", "claude"],
    "DeepSeek": ["deepseek"],
    "Poe": ["poe.com"],
    "Manus": ["manus"],
    "LocalSend": ["localsend"],
    "VLC": ["videolan"],
    "AVPlayer": ["avplayer"],
    "GoodReader": ["goodreader"],
    "BookPlayer": ["bookplayer"],
    "Snapseed": ["snapseed"],
    "Speedtest": ["speedtest", "ookla"],
    "数字人民币": ["ecny"],
    "中国联合航空": ["cueair", "flycua"],
    "剪映": ["jianying", "capcut"],
}

# Apps that we will fetch from ddgksf2013 or Maasea instead of BlackMatrix7 (excluding China Unicom)
OVERRIDE_APPS = {
    "微博轻享版": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/WeiboAds.conf",
    # "百度贴吧": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/TieBaAds.conf",
    "网易云音乐": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/NeteaseAds.conf",
    "闲鱼": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/GoofishAds.conf",
    "微信": [
        "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/WeChat.conf",
        "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/Applet.conf"
    ],
    "网易邮箱大师": "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/NeteaseMailAds.conf",
    "豆瓣": [
        "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/Html/Douban.conf",
        "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partD/Douban.snippet"
    ],
    "哔哩哔哩": "https://raw.githubusercontent.com/Maasea/sgmodule/master/Bilibili.Helper.sgmodule",
    
    # 新增的高级专属规则
    "通用开屏广告": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/Shadowrocket/Advertising/Advertising.sgmodule",
    # "小红书": "https://ddgksf2013.top/rewrite/XiaoHongShuAds.conf",
    "百度网盘": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partB/BaiduNetdisk.snippet",
    "知乎": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partZ/Zhihu.snippet",
    "淘宝": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partT/Taobao.snippet",
    "蜻蜓FM": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partQ/QingTingFM.snippet",
    "美团": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partM/Meituan.snippet",
    "大众点评": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partD/DianPing.snippet",
    "滴滴": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partX/XiaoJuTechnology.snippet",
    "航旅纵横": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partH/HangLvZongHeng.snippet",
    "去哪儿旅行": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partQ/Qunar.snippet",
    "携程旅行": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partX/Ctrip.snippet",
    "铁路12306": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/split/part1/12306.sgmodule",
    
    # 补强和优化的 App 去广告规则
    "QQ音乐": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partQ/QQMusic.snippet",
    "米家": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partM/Mijia.snippet",
    "网易新闻": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partW/NetEaseNews.snippet",
    "拼多多": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partP/Pinduoduo.snippet",
    "美图秀秀": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partM/MeituXiuxiu.snippet",
    # "叮咚买菜": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partD/DingDongMaiCai.snippet",
    "汽车之家": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partQ/Autohome.snippet",
    "锦江荟": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partJ/JinJiangHuiAPP.snippet",
    # "爱奇艺": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partA/iQIYI.snippet",
    # "优酷": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partY/Youku.snippet",
    # "芒果TV": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partM/MangoTV.snippet",
    "云闪付": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partY/UnionPayCloudPay.snippet",
    "微信解除链接限制": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/QuantumultX/rewrite/split/partW/WeChatUnlockLinkRestrict.snippet",
    "SOUL": "https://raw.githubusercontent.com/Xo776/byead/refs/heads/main/soul_ads.conf"
}

# Extra domains that we want to reject via Rules (like QQ Music)
EXTRA_REWRITE_DOMAINS = {
    "蜻蜓FM": [
        "ad.qingting.fm",
        "admgr.qingting.fm",
        "dload.qd.qingting.fm",
        "logger.qingting.fm",
        "s.qd.qingting.fm",
        "s.qd.qingtingfm.com",
        "adlaunch.qtfm.cn",
        "ad.qtfm.cn",
        "adlog.qingting.fm"
    ]
}

# Universal Ad SDK domains to reject unconditionally via Rules
ALWAYS_INJECT_DOMAINS = [
    # Tencent GDT Ads
    "mi.gdt.qq.com",
    "win.gdt.qq.com",
    "v.gdt.qq.com",
    "v2.gdt.qq.com",
    "t.gdt.qq.com",
    "gdt.qq.com",
    "pgdt.gtimg.cn",
    "pgdt.ugdtimg.com",
    "sdk.e.qq.com",
    "adsmind.tc.qq.com",
    "p.l.qq.com",
    "us.l.qq.com",
    "tangram.e.qq.com",
    "oth.str.mdt.qq.com",
    
    # Baidu Mobads
    "mobads.baidu.com",
    "mobads-logs.baidu.com",
    "union.baidu.com",
    "ada.baidu.com",
    "als.baidu.com",
    "bdbus-turbonet.baidu.com",
    "bgg.baidu.com",
    "gsp0.baidu.com",
    
    # ByteDance Pangle
    "api-access.pangolin-sdk-toutiao-b.com",
    "pangle.io",
    
    # Beizi Ads (倍孜广告)
    "sdk.beizi.biz",
    "api-htp.beizi.biz",
    
    # HubCloud Ads (汇量广告)
    "sdktmp.hubcloud.com.cn",
    "v.adx.hubcloud.com.cn",
    "api.htp.hubcloud.com.cn",
    
    # Ad-Plus & Ad-Scope
    "dsp-tracer.adn-plus.com.cn",
    "resource.ad-scope.com.cn",
    
    # Partner Search Ads (神马)
    "sdk-log.partner.sm.cn",
    
    # Baidu Mobads config
    "mobads-pre-config.cdn.bcebos.com",
    
    # Zztfly Ads (浙报/其他广告)
    "cdn-api-auth.zztfly.com",
    "upc.zztfly.com",
    "cfgc.zztfly.com",
    "log-auth.zztfly.com",
    
    # Kuaishou Ads (快手联盟)
    "gdfp.gifshow.com",
    "open.e.kuaishou.com",
    
    # Pangolin Additions (字节穿山甲补充)
    "api-access.pangolin-sdk-toutiao1.com",
    "api-access.pangolin-sdk-toutiao.com",
    
    # Sensors Data Analytics (神策分析数据埋点 - 阻断广告个性化追踪并加速)
    "sensors-collect-prod.bestwehotel.com",
    "sensors-ma.bestwehotel.com",
    "sensors-ab.bestwehotel.com",
    # NetEase Cloud Music Ad Materials & CDN (网易云音乐广告素材与CDN)
    "iadmusicmat.music.126.net",
    "iadmatapk.nosdn.127.net",
    
    # Ctrip Ad Retargeting (携程广告重定向追踪)
    "retargeting.ctrip.com",

    # 2026-07-05 双端对齐补齐的去广告拦截域名
    "ads.twitter.com",
    "ads-api.x.com",
    "tanx.com",
    "adm.10jqka.com.cn",
    "fc-.cdn.bcebos.com"
]

ALWAYS_KEEP_KEYWORDS = [
    "pangle", "pangolin", "gdt.qq.com", "ugdtimg", "mobads.baidu.com", "mobads-logs", 
    "admobile", "ranfenghd", "tianmu", "anythinktech", "1rtb.net",
    "advert", "advertise", "telemetry", "analytics", "tracker", "doubleclick",
    "beizi", "hubcloud", "zztfly", "adn-plus", "ad-scope"
]

# High risk domains to completely exclude from MITM to avoid security and app issues
HIGH_RISK_MITM_DOMAINS = [
    # Banks & Payments
    "cmbchina.com", "cmbimg.com", "alipay.com", "alipayobjects.com", "95516.com", "unionpay.com",
    "ccb.com", "spdb.com.cn", "ecitic.com", "bankofbeijing.com.cn", "bankofshanghai.com",
    "cebbank.com", "hxb.com.cn", "icbc.com.cn", "abchina.com", "boc.cn", "bankcomm.com",
    # Meituan & Dianping (Wind control & network crashed issues)
    "meituan.com", "meituan.net", "dianping.com", "dpfile.com", "maoyan.com",
    # China Unicom (Affects cellular one-key login)
    "10010.com", "chinaunicom.com",
    # Spotify
    "spotify.com", "wg.spotify.com",
    # Finance/Crypto
    "binance.com", "bitget.com", "bybit.com", "wise.com",
    # Baidu Netdisk (SSL Pinning prevents logins if decrypted)
    "pan.baidu.com"
]

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

SDK_BLOCK_RULES = [
    # 限制性阻止 QUIC 流量以防绕过去广告（仅针对特定广告及目标域名，避免干扰银行等 App）
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,baidu.com)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,baidupcs.com)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,douban.com)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,weibo.com)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,weibo.cn)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,gdt.qq.com)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,ugdtimg.com)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,pangle.io)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,mobads.baidu.com)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,bestwehotel.com)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,feidee.com)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,qingting.fm)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,qingtingfm.com)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,beizi.biz)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,hubcloud.com.cn)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,zztfly.com)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,qtfm.cn)),REJECT-NO-DROP",
    "AND,((protocol,udp),(dest-port,443),(domain-suffix,sofire.baidu.com)),REJECT-NO-DROP",
    
    # 大厂打点与 SDK 隐私遥测 REJECT-NO-DROP 拦截（防重试发热）
    "DOMAIN,log.snssdk.com,REJECT-NO-DROP",
    "DOMAIN,rtlog.snssdk.com,REJECT-NO-DROP",
    "DOMAIN,mcs.snssdk.com,REJECT-NO-DROP",
    "DOMAIN,dm.snssdk.com,REJECT-NO-DROP",
    "DOMAIN,mcs.zijieapi.com,REJECT-NO-DROP",
    "DOMAIN,toblog.ctobsnssdk.com,REJECT-NO-DROP",
    "DOMAIN-SUFFIX,apmplus.volces.com,REJECT-NO-DROP",
    "DOMAIN,log-api.pangolin-sdk-toutiao.com,REJECT-NO-DROP",
    "DOMAIN,beacon.qq.com,REJECT-NO-DROP",
    "DOMAIN,rqd.qq.com,REJECT-NO-DROP",
    "DOMAIN,ios.bugly.qq.com,REJECT-NO-DROP",
    "DOMAIN,mdap.alipay.com,REJECT-NO-DROP",
    "DOMAIN,wn.pos.baidu.com,REJECT-NO-DROP",
    "DOMAIN,afd.baidu.com,REJECT-NO-DROP",
    "DOMAIN,afdconf.baidu.com,REJECT-NO-DROP",
    "DOMAIN,stats.jpush.cn,REJECT-NO-DROP",
    "DOMAIN,crashlytics.com,REJECT-NO-DROP",
    "DOMAIN-SUFFIX,adjust.com,REJECT-NO-DROP",
    "DOMAIN-SUFFIX,appsflyersdk.com,REJECT-NO-DROP",
    "DOMAIN,app-log-lab.tantanapp.com,REJECT-NO-DROP",
    "DOMAIN,io-sm-log.tantanapp.com,REJECT-NO-DROP",
    "DOMAIN,client-monitor.tantanapp.com,REJECT-NO-DROP",
    "DOMAIN,f10.baidu.com,REJECT-NO-DROP",

    # 穿山甲
    "DOMAIN-KEYWORD,pangle,REJECT-200",
    "DOMAIN-SUFFIX,pangle.io,REJECT-200",
    "DOMAIN-SUFFIX,pangolin-sdk-toutiao,REJECT-200",
    # 腾讯广点通
    "DOMAIN-SUFFIX,gdt.qq.com,REJECT-200",
    "DOMAIN-SUFFIX,ugdtimg.com,REJECT-200",
    # 百度联盟
    "DOMAIN-SUFFIX,mobads.baidu.com,REJECT-200",
    "DOMAIN-SUFFIX,mobads-logs.baidu.com,REJECT-200",
    # 天目/快手/广告聚合
    "DOMAIN-SUFFIX,tianmu.mobi,REJECT-200",
    "DOMAIN-SUFFIX,1rtb.net,REJECT-200",
    
    # 百度 HTTPDNS 拦截（防贴吧等 App 绕过域名规则，使用 REJECT-NO-DROP/REJECT 拒绝以触发系统 DNS 降级回退）
    "IP-CIDR,180.76.76.200/32,REJECT-NO-DROP",
    "IP-CIDR,180.76.76.112/32,REJECT-NO-DROP",
    "DOMAIN,httpdns.baidu.com,REJECT",
    "DOMAIN,httpdns.baidubce.com,REJECT",
    
    # 新增联盟与广告物料、追踪封锁（基于贴吧代理日志的精准收网）
    "DOMAIN-SUFFIX,ubixioe.com,REJECT",
    "DOMAIN-SUFFIX,pangolin-dsp-toutiao.com,REJECT",
    "DOMAIN-SUFFIX,pglstatp-toutiao.com,REJECT",
    "DOMAIN-SUFFIX,xdplt.com,REJECT",
    
    # PCDN / 视频上传劫持 拦截
    "DOMAIN-SUFFIX,pkoplink.com,REJECT",
    "DOMAIN-SUFFIX,sjxydc.com,REJECT"
]

MANDATORY_MITM_DOMAINS = [
    # 豆瓣
    "api.douban.com",
    "m.douban.com",
    "frodo.douban.com",
    
    # 锦江荟 (bestwehotel)
    "booking.bestwehotel.com",
    "wxapp.bestwehotel.com",
    "web-opin.bestwehotel.com",
    "hwy-gapi.bestwehotel.com",
    
    # 随手记 (feidee)
    "tg.feidee.com",
    
    # 航旅/美团/知乎/微博/Didi 等核心 App 的补充解密
    "adproxy.autohome.com.cn",
    "y.gtimg.cn",                    # QQ音乐开屏
    "tqt.weibo.cn",                  # 微博
    "boot.weibo.com",                # 微博
    "preload-click.uve.weibo.com",   # 微博
    "preload-impression.uve.weibo.com", # 微博
    "weathercn.com",                 # 天气通
    "ads-img-al.xhscdn.com",         # 小红书
    "zhstatic.zhihu.com",            # 知乎
    "zhuanlan.zhihu.com",            # 知乎
    "didapinche.com",                # 嘀嗒出行 (后缀匹配，涵盖 capis, www 等子域)
    "ct.xiaojukeji.com",             # 滴滴出行
    "ndstatic.cdn.bcebos.com",       # 百度网盘广告
    "staticsns.cdn.bcebos.com",      # 百度网盘广告
    "issuecdn.baidupcs.com",         # 百度网盘广告
    "fc-video.cdn.bcebos.com",       # 百度网盘视频广告
    "rp.hpplay.cn",                  # 投屏广告
    "oss.umetrip.com",               # 航旅纵横
    "mea.meitudata.com",             # 美图秀秀
    "mobileapi-v6.elong.com",        # 艺龙旅行
    "gateway.shouqiev.com",          # 首汽约车
    "gw-passenger.01zhuanche.com",   # 首汽约车
    "pinggai.caixin.com",            # 财新
    "eastmoney.com",                 # 东方财富 (后缀匹配，涵盖 choicegw2 等子域)
    "zdmimg.com",                    # 值得买
    
    # 新增开屏解密以防绕过
    "babytree.com",                  # 宝宝树孕育
    "jianying.com",                  # 剪映
    
    "maicai.api.ddxq.mobi"           # 叮咚买菜开屏域名
]

CUSTOM_REWRITE_RULES = [
    # 叮咚买菜 App 开屏广告拦截（使用标准小火箭 reject 动作以保证 100% 兼容）
    {'text': '^https?:\/\/maicai\.api\.ddxq\.mobi\/advert\/ reject', 'pattern': '^https?:\/\/maicai\.api\.ddxq\.mobi\/advert\/', 'priority': 0, 'app': '叮咚买菜'},
    # 百度贴吧 App 开屏与广告接口静态拦截补充 (防绕过，修正斜杠脱靶与语法兼容)
    {'text': '^https?:\/\/c\.tieba\.baidu\.com\/c\/s\/(ad|splashSchedule|splash) reject-dict', 'pattern': '^https?:\/\/c\.tieba\.baidu\.com\/c\/s\/(ad|splashSchedule|splash)', 'priority': 0, 'app': '百度贴吧'},
    {'text': '^https?:\/\/c\.tieba\.baidu\.com\/c\/f\/ad\/ reject-dict', 'pattern': '^https?:\/\/c\.tieba\.baidu\.com\/c\/f\/ad\/', 'priority': 0, 'app': '百度贴吧'},
    {'text': '^https?:\/\/tbapi\.baidu\.com\/c\/s\/(ad|splashSchedule|splash) reject-dict', 'pattern': '^https?:\/\/tbapi\.baidu\.com\/c\/s\/(ad|splashSchedule|splash)', 'priority': 0, 'app': '百度贴吧'},
    {'text': '^https?:\/\/tbapi\.baidu\.com\/c\/f\/ad\/ reject-dict', 'pattern': '^https?:\/\/tbapi\.baidu\.com\/c\/f\/ad\/', 'priority': 0, 'app': '百度贴吧'},
    # 百度移动广告联盟重写拦截 (解决贴吧及其他百度系开屏广告顽疾，以 reject-200 响应空包)
    {'text': '^https?:\/\/mobads\.baidu\.com\/ads\/pa\/ reject-200', 'pattern': '^https?:\/\/mobads\.baidu\.com\/ads\/pa\/', 'priority': 0, 'app': '百度联盟广告'},
    {'text': '^https?:\/\/mobads\.baidu\.com\/[a-zA-Z0-9_\/]+\.php reject-200', 'pattern': '^https?:\/\/mobads\.baidu\.com\/[a-zA-Z0-9_\/]+\.php', 'priority': 0, 'app': '百度联盟广告'},
    # 豆瓣 App 开屏与内含广告 (改回标准的 reject 动作以保证模块完美读取)
    {'text': '^https:\/\/api\.douban\.com\/v\d\/app_ads\/splash reject', 'pattern': '^https:\/\/api\.douban\.com\/v\d\/app_ads\/splash', 'priority': 0, 'app': '豆瓣'},
    {'text': '^https:\/\/frodo\.douban\.com\/api\/v\d\/app_ads\/splash reject', 'pattern': '^https:\/\/frodo\.douban\.com\/api\/v\d\/app_ads\/splash', 'priority': 0, 'app': '豆瓣'},
    {'text': '^https:\/\/frodo\.douban\.com\/api\/v\d\/erebor\/feed_ad reject', 'pattern': '^https:\/\/frodo\.douban\.com\/api\/v\d\/erebor\/feed_ad', 'priority': 0, 'app': '豆瓣'},
    {'text': '^https:\/\/frodo\.douban\.com\/api\/v\d\/home_banner reject', 'pattern': '^https:\/\/frodo\.douban\.com\/api\/v\d\/home_banner', 'priority': 0, 'app': '豆瓣'},
    {'text': '^https:\/\/frodo\.douban\.com\/api\/v\d\/search\/found_words reject', 'pattern': '^https:\/\/frodo\.douban\.com\/api\/v\d\/search\/found_words', 'priority': 0, 'app': '豆瓣'},
    
    # 锦江荟 App 开屏广告拦截补充
    {'text': '^https?:\\/\\/wxapp\\.bestwehotel\\.com\\/gw3\\/app-mini\\/trip-hotel-banner\\/activity\\/getActivityInfo reject', 'pattern': '^https?:\\/\\/wxapp\\.bestwehotel\\.com\\/gw3\\/app-mini\\/trip-hotel-banner\\/activity\\/getActivityInfo', 'priority': 0, 'app': '锦江荟'},
    {'text': '^https?:\\/\\/booking\\.bestwehotel\\.com\\/proxy\\/trip-hotel-banner\\/activity\\/getActivityInfo reject', 'pattern': '^https?:\\/\\/booking\\.bestwehotel\\.com\\/proxy\\/trip-hotel-banner\\/activity\\/getActivityInfo', 'priority': 0, 'app': '锦江荟'},
    {'text': '^https?:\\/\\/hwy-gapi\\.bestwehotel\\.com\\/gw3\\/app-mini\\/trip-hotel-banner\\/activity\\/getActivityInfo reject', 'pattern': '^https?:\\/\\/hwy-gapi\\.bestwehotel\\.com\\/gw3\\/app-mini\\/trip-hotel-banner\\/activity\\/getActivityInfo', 'priority': 0, 'app': '锦江荟'},
    {'text': '^https?:\\/\\/hwy-gapi\\.bestwehotel\\.com\\/proxy\\/trip-hotel-banner\\/activity\\/getActivityInfo reject', 'pattern': '^https?:\\/\\/hwy-gapi\\.bestwehotel\\.com\\/proxy\\/trip-hotel-banner\\/activity\\/getActivityInfo', 'priority': 0, 'app': '锦江荟'},
    {'text': '^https?:\\/\\/hwy-gapi\\.bestwehotel\\.com\\/message\\/adLabel\\/v2\\/getAdList reject', 'pattern': '^https?:\\/\\/hwy-gapi\\.bestwehotel\\.com\\/message\\/adLabel\\/v2\\/getAdList', 'priority': 0, 'app': '锦江荟'},
    {'text': '^https?:\\/\\/hwy-gapi\\.bestwehotel\\.com\\/adSettlement\\/app\\/idfa\\/v1\\/collect reject', 'pattern': '^https?:\\/\\/hwy-gapi\\.bestwehotel\\.com\\/adSettlement\\/app\\/idfa\\/v1\\/collect', 'priority': 0, 'app': '锦江荟'},
    {'text': '^https?:\\/\\/hwy-gapi\\.bestwehotel\\.com\\/applog\\/requestPage\\/request reject', 'pattern': '^https?:\\/\\/hwy-gapi\\.bestwehotel\\.com\\/applog\\/requestPage\\/request', 'priority': 0, 'app': '锦江荟'},
    {'text': '^https?:\\/\\/hwy-gapi\\.bestwehotel\\.com\\/proxy\\/trip-client-monitor\\/log\\/monitor reject', 'pattern': '^https?:\\/\\/hwy-gapi\\.bestwehotel\\.com\\/proxy\\/trip-client-monitor\\/log\\/monitor', 'priority': 0, 'app': '锦江荟'},
    
    # 随手记 App 广告拦截补充
    {'text': '^https?:\/\/tg\.feidee\.com\/online_ad\/ reject', 'pattern': '^https?:\/\/tg\.feidee\.com\/online_ad\/', 'priority': 0, 'app': '随手记'},
    {'text': '^https?:\/\/tg\.feidee\.com\/vis-ad-engine-ws\/api\/ reject', 'pattern': '^https?:\/\/tg\.feidee\.com\/vis-ad-engine-ws\/api\/', 'priority': 0, 'app': '随手记'}
]

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
    output_path = os.path.join(script_dir, "custom_adblock.sgmodule")
    
    import datetime
    utc_now = datetime.datetime.utcnow()
    beijing_now = utc_now + datetime.timedelta(hours=8)
    beijing_time_str = beijing_now.strftime('%Y-%m-%d %H:%M:%S')
    
    BYPASS_RULES = [
        "# === Bypass Rules for WeChat, Alipay, Bank and Login App anomalies ===",
        "DOMAIN,amdc.alipay.com,DIRECT",
        "DOMAIN,enrichgw.10010.com,DIRECT",
        "DOMAIN,wxa.wxs.qq.com,DIRECT",
        "DOMAIN,wximg.wxs.qq.com,DIRECT",
        "DOMAIN,aedns.weixin.qq.com,DIRECT",
        "DOMAIN,apd-pcdnwxlogin.teg.tencent-cloud.net,DIRECT",
        "DOMAIN,mazu.m.qq.com,DIRECT",
        "DOMAIN,msmp.abchina.com.cn,DIRECT",
        "DOMAIN,log.cmbchina.com,DIRECT",
        "DOMAIN,httpdns.music.163.com,DIRECT",
        "DOMAIN,smartad.10010.com,DIRECT",
        # 解决宝宝知道等百度系 App 误杀，恢复推荐和视频加载
        "DOMAIN,sofire.baidu.com,DIRECT",
        "DOMAIN,nsclick.baidu.com,DIRECT",
        # 解决亚马逊海外购加载报错问题，绕过代理解密风控
        "DOMAIN-SUFFIX,amazon.com,DIRECT",
        "DOMAIN-SUFFIX,amazon.cn,DIRECT",
        "DOMAIN-SUFFIX,media-amazon.com,DIRECT",
        "DOMAIN-SUFFIX,ssl-images-amazon.com,DIRECT",
        "DOMAIN-SUFFIX,amazon-adsystem.com,DIRECT",
        # 解决百度系 App 代理风控（登录频繁要求、设置失效、推荐无内容等）
        "DOMAIN-SUFFIX,baidu.com,DIRECT",
        "DOMAIN-SUFFIX,baidupcs.com,DIRECT",
        "DOMAIN-SUFFIX,bdstatic.com,DIRECT",
        "DOMAIN-SUFFIX,tieba.com,DIRECT",
        "DOMAIN-SUFFIX,tbapi.baidu.com,DIRECT",
        # 解决极光长连接被拦截引发 App 判定无网的异常（如宝宝知道）
        "DOMAIN-SUFFIX,jiguang.cn,DIRECT",
        "DOMAIN-SUFFIX,jpush.cn,DIRECT",
        # 彻底解决百度广告联盟强证书校验导致死循环重连发热的异常
        "DOMAIN-SUFFIX,mobads.baidu.com,DIRECT",
        "DOMAIN-SUFFIX,mobads-logs.baidu.com,DIRECT",
        # 彻底解决崩溃统计、打点与归因阻断引发后台重试发热的异常
        "DOMAIN-SUFFIX,umeng.com,DIRECT",
        "DOMAIN-SUFFIX,umengcloud.com,DIRECT",
        # 2026-07-05 联动加白：防客户端重试发热与地图/验证码误杀
        "DOMAIN,apikey.map.qq.com,DIRECT",
        "DOMAIN,cdn.ynuf.aliapp.org,DIRECT",
        # 彻底解决百度/穿山甲广告埋点上报失败引起的高频重连发热
        # 2026-07-07 联动加白：解决字节/抖音核心及打点上报重试引发的发热 (不放行根域名)
        "DOMAIN,aweme.snssdk.com,DIRECT",
        "DOMAIN,i.snssdk.com,DIRECT",
        "DOMAIN,api.snssdk.com,DIRECT",
        "DOMAIN,api-access.snssdk.com,DIRECT",
        "DOMAIN,security.snssdk.com,DIRECT",
        "DOMAIN,verify.snssdk.com,DIRECT",
        "DOMAIN,lf.snssdk.com,DIRECT",
        "DOMAIN,vcs.zijieapi.com,DIRECT",
        "DOMAIN-SUFFIX,mssdk.bytedance.com,DIRECT",
        "DOMAIN-SUFFIX,mssdk.volces.com,DIRECT",
        "DOMAIN-SUFFIX,mssdk.zijieapi.com,DIRECT",
        "DOMAIN-SUFFIX,tnc.zijieapi.com,DIRECT",
        "DOMAIN-SUFFIX,tnc3-sz.zijieapi.com,DIRECT",
        "DOMAIN-SUFFIX,tnc3-alipay.zijieapi.com,DIRECT",
        "DOMAIN-SUFFIX,tnc11.zijieapi.com,DIRECT",
        "DOMAIN,is.snssdk.com,DIRECT",
        "DOMAIN,applog.snssdk.com,DIRECT",
        "DOMAIN-KEYWORD,dy.snssdk,DIRECT"
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("#!name=custom apps adblock.sgmodule\n")
        f.write(f"#!desc=最近更新: {beijing_time_str} | Deep ad block & UI purification customized for user's installed apps.\n")
        f.write(f"#!total={len(final_rules) + len(SDK_BLOCK_RULES) + len(final_rewrites) + len(final_scripts) + len(BYPASS_RULES)}\n\n")
        
        if final_rules or SDK_BLOCK_RULES or BYPASS_RULES:
            f.write("[Rule]\n")
            for line in BYPASS_RULES:
                f.write(line + "\n")
            f.write("# === SDK Core REJECT Rules ===\n")
            for line in SDK_BLOCK_RULES:
                f.write(line + "\n")
            f.write("# === Compiled App Rules ===\n")
            for line in final_rules:
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
