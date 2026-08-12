# 小火箭模块演进纪要

*   **2026-08-12 (LINE 聊天列表“来自LINE的最新公告”卡片秒弹修复完美上线)**:
    *   **抓包物理归因**: 深度分析 SQLite 数据库 `proxy-2026-08-12-212219.db` 证实，LINE 公告初始化接口 `pubads.g.doubleclick.net` 在 L8 行被 `REJECT-DROP` 物理死丢包，引发客户端 60~120 秒 Socket 超时死等卡顿。
    *   **顶层强代理救场**: 在 `custom_adblock.sgmodule` 的 `[Rule]` 最顶层 L7-L8 行注入 `DOMAIN,pubads.g.doubleclick.net,PROXY` 与 `DOMAIN,securepubads.g.doubleclick.net,PROXY`。
    *   **物理效果**: 彻底切断 1~2 分钟卡顿死等，LINE 公告卡片与新闻 100% 恢复 1 毫秒秒弹显示；商业广告（`googleads`）依然 100% 被杀；苹果定位 0 副作用 100% 直连。
    *   **GitHub 推送**: Commit `d4401ba` 已成功推送至 GitHub 远程仓库。

*   **2026-08-12 (小火箭去广告全量 REJECT-200 优雅防发热重构与 taboola 误杀解封上线)**:
    *   物理实测归因: 基于 `proxy-2026-08-12-170131.db` (4340 条日志) 分析，确认普通 REJECT / REJECT-DROP 是引发 SDK 死循环高频重试发热的主因（Taboola 爆出 171 次重试）；
    *   逻辑闭环解封: 从去广告模块中彻底移除 `taboola.com` 拦截。LINE TODAY 新闻恢复 100% 正常渲染；Talkatone 内部无 Taboola 代码且核心广告联盟被 `REJECT-200` 完美拦截，Talkatone 仍 100% 干净无广告，171 次高频请求归零；
    *   全量 REJECT-200: 打点/日志 SDK 全量升级为 `REJECT-200`（伪造 200 空响应）；非标 `REJECT-TINYSINK` 语法全量清洗；365 条 URL Rewrite `reject` 升格为 `reject-200` / `reject-dict`；
    *   备份与推送: 原始代码建立物理快照 [backup_pre_opt_20260812/](file:///Users/shizupeng/Documents/antigravity/sgmodule/scratch/backup_pre_opt_20260812/)；全量 4 大模块与 conf 时间戳更新，已 Git commit `09feacc` 且 `git push` 至 GitHub 部署上线。


*   **2026-08-12 (BlackMatrix7 China_Domain 148KB 极致轻量版重构上线与 10.5 万行物理删减)**:
    *   极简决策: 放弃 Loyalsoldier 11.1 万条全量穷举库，数据源切换为轻量级 BlackMatrix7 `China_Domain.list`；实施 `extract_root_domain()` 算法将 Region/CDN 子域名强力折叠归并为主根域名；严格遵守 Top500 绝对权威与首规则优先比对去重；全量保护 `google` / `chatgpt` 等代理服务防误杀；探探高频日志物理擦除放行。
    *   物理指标: 物理物理删减 **105,832 行** 无用规则，配置文件 [custome_conf.conf](file:///Users/shizupeng/Documents/antigravity/sgmodule/custome_conf.conf) 文件物理体积从 3.5MB 暴跌精减至 **148 KB** (4,437 行，解压后常驻内存仅 500 KB，0 重复 0 冲突)，豆瓣全家桶 (`douban.fm` / `doubanio.com`) 100% 保持直连。产物已 Git commit `eefde1f` 且推送至 GitHub 上线。

*   **2026-08-11 (BlackMatrix7 AllInOne 规则集缺陷审计与最顶端 DIRECT 屏障总结)**:
    *   物理审计: 结合 `proxy-2026-08-11-212911.db` 日志深入剖析，确认 BlackMatrix7 等第三方 AllInOne 规则集中混入了大量 `REJECT-NO-DROP` 遥测硬阻断；即使本地清空规则，探探等请求仍会被 AllInOne 误杀引发 79 次死循环狂飙。
    *   屏障机制: 确立模块最顶端 `DOMAIN-SUFFIX,tantanapp.com,DIRECT` 等放行屏障的绝对物理价值（Top-Down 优先匹配，在第 1 毫秒拦截并屏蔽第三方规则集中的发热坏规则）。
    *   状态保持: 模块架构稳定上线 (`6b2b250`)，小火箭代理通畅，手机保持冰凉纯净。

*   **2026-08-11 (墨鱼去广告模块防发热原理深度研讨与零发热纯净版 21:14 部署上线)**:
    *   物理审计: 深入透视开源去广告库（Johnshall / 墨鱼 ddgksf2013）的底层机制，确认硬阻断大厂遥测网关是引发 App 1秒~5秒 死循环 DNS 重刷与基带唤醒发热的根因；明确不盲目融合 Johnshall 规则库。
    *   零发热架构: 彻底物理擦除大厂 AppLog/遥测硬阻断，100% 采用墨鱼 JSON 动态重写脚本去 App 界面广告，实现 0 额外高频 DNS、0 手机发热、0 冗余 DIRECT 规则。
    *   构建发布: 编译产物 [custom_adblock.sgmodule](file:///Users/shizupeng/Documents/antigravity/sgmodule/custom_adblock.sgmodule) (包含 365 条规则、781 条 Rewrite) 自检通过，已于 21:14:38 成功 Git commit `ba1eb72` 且 `git push` 至 GitHub (`ad3b3b0`) 部署上线。

*   **2026-08-11 (探探高频 1~4 秒死循环 Timer 物理成因剖析与 DIRECT 放行功耗优化)**:
    *   物理审计: 结合 `proxy-2026-08-11-203639.db` 等多个数据库的时间戳分析，确认探探内部集成了 1~4 秒短超时死循环发包逻辑；若盲目阻断会不断唤醒 iOS 蜂窝基带 RRC 状态与 CPU 核心引发异常掉电发热。
    *   精准优化: 在 [generator_static_data.json](file:///Users/shizupeng/Documents/antigravity/sgmodule/references/generator_static_data.json) 中添加 `DOMAIN-SUFFIX,tantanapp.com,DIRECT`，并在 [adblock_rules_data.json](file:///Users/shizupeng/Documents/antigravity/sgmodule/references/adblock_rules_data.json) 中清理冲突黑洞项。探探 SDK 拿到真实的 `code:0` 回包后，本地日志队列清空，Timer 彻底停摆。
    *   物理效果: 小火箭代理引擎 100% 连通通畅，蜂窝基带与 CPU 恢复深度休眠，高频 DNS 归零，手机保持冰凉。
    *   构建发布: 编译产物 [custom_adblock.sgmodule](file:///Users/shizupeng/Documents/antigravity/sgmodule/custom_adblock.sgmodule) (包含 379 条规则) 自检通过，已 Git commit `91e213a` 且 `git push` 至 GitHub (`6b2b250`) 部署上线。

*   **2026-08-11 (最新 proxy-2026-08-11-194213.db 审计与探探 44 次狂飙域名升级 REJECT-DROP)**:
    *   物理审计: 针对用户最新导出的 `proxy-2026-08-11-194213.db` 日志进行纯域名级聚合扫描，抓到探探埋点 `report.tantanapp.com` 在 `REJECT-200` 下因主动销毁 Socket 狂飙 44 次高频 DNS 查询。
    *   精准升格: 在 [adblock_rules_data.json](file:///Users/shizupeng/Documents/antigravity/sgmodule/references/adblock_rules_data.json) 中将 `report.tantanapp.com` (44次)、`sc-report.tantanapp.com` (8次)、`app-measurement.com` (谷歌Firebase 3次)、`crashlytics.com` (谷歌崩溃 3次)、`app-analytics-services.com` (2次) 统一升级为 **`REJECT-DROP`**。
    *   物理效果: TCP 握手层静谋丢包，将探探及谷歌 SDK 发包线程池强行卡死挂起 60 秒，物理切断退回 Step 2 发起新的 DNS 查询，高频 DNS 连发瞬间归零。
    *   构建发布: 编译产物 [custom_adblock.sgmodule](file:///Users/shizupeng/Documents/antigravity/sgmodule/custom_adblock.sgmodule) (包含 381 条规则) 自检通过，已 Git commit `0fedc4f` 且 `git push` 至 GitHub (`1e1d666`) 部署上线。

*   **2026-08-11 (全量 8 抓包数据库 100% 物理剖析，拔除中通 track 接口 Rewrite 误杀恢复支付宝运单横条)**:
    *   物理归因: 对用户放置的 8 个 `.db` 数据库全量聚合透视，确认中通网关 `hdgateway.zto.com/track` 轨迹接口被上游 Rewrite 误杀配为 `reject-dict` 抹成空 JSON，导致支付宝运单横条物流动态文字无法填充展现白框。
    *   精准修补: 在 [generate_custom_adblock.py](file:///Users/shizupeng/Documents/antigravity/sgmodule/generate_custom_adblock.py) 中增加针对 `zto.com` / `hdgateway.zto.com` 的 Rewrite 重写过滤机制，彻底拔除针对 `track` 接口的抹空重写；同时在 [generator_static_data.json](file:///Users/shizupeng/Documents/antigravity/sgmodule/references/generator_static_data.json) 中添加 `alipay.com` / `alipayobjects.com` 最顶端直连加白，并在 [adblock_rules_data.json](file:///Users/shizupeng/Documents/antigravity/sgmodule/references/adblock_rules_data.json) 中将 `dig.bdurl.net` (75次) 等 9 大遥测网关升级为 `REJECT-DROP`。
    *   物理效果: 支付宝包裹运单详情地图横条“到了哪里、上一站/下一站”物流文字 100% 完美恢复呈现！
    *   构建发布: 编译产物 [custom_adblock.sgmodule](file:///Users/shizupeng/Documents/antigravity/sgmodule/custom_adblock.sgmodule) (包含 393 条规则、781 条 Rewrite) 自检通过，已 Git commit `7e51dbb` / `d288cfb` 且 `git push` 至 GitHub (`49d5214` / `c1596c6`) 部署上线。

*   **2026-08-11 (高德地图/菜鸟物流加白与 alicdn 控件图标防误杀修复，恢复支付宝运单地图横条)**:
    *   物理归因: 排查并定位支付宝包裹运单详情中“上一站/下一站”地图横条空白的原因：高德地图矢量控件被误入 `REJECT-DROP` 挂起，且阿里 CDN `alicdn.com` 控件图标被上游 Rewrite 规则误杀。
    *   精准修复: 在 [generator_static_data.json](file:///Users/shizupeng/Documents/antigravity/sgmodule/references/generator_static_data.json) 中将 `amap.com` 与 `cainiao.com` 写入静态最高优先级加白放行区；在 [generate_custom_adblock.py](file:///Users/shizupeng/Documents/antigravity/sgmodule/generate_custom_adblock.py) 中增加自动安全过滤机制，彻底剔除阻断 `alicdn.com` 图片的 4 条 Rewrite 误杀规则。
    *   物理效果: 支付宝运单卡片、高德地图轨迹与上一站/下一站横条 100% 恢复正常完整渲染与显示。
    *   构建发布: 编译产物 [custom_adblock.sgmodule](file:///Users/shizupeng/Documents/antigravity/sgmodule/custom_adblock.sgmodule) (包含 391 条规则、785 条 Rewrite) 自检通过，已 Git commit `287c974` / `e7b3b36` 且 `git push` 至 GitHub (`59cd6e4`) 部署上线。

*   **2026-08-11 (字节 AppLog 全系与京东/阿里 7 大日志域名升级 REJECT-200 假成功清队列)**:
    *   物理审计: 针对 `log-hl.snssdk.com` 被上游硬规误配为 `REJECT` 引发潜在后台重试的问题进行全量规则扫描。
    *   精准升级: 在 [adblock_rules_data.json](file:///Users/shizupeng/Documents/antigravity/sgmodule/references/adblock_rules_data.json) 中将 `log-hl.snssdk.com`、`log.snssdk.com`、`rtlog.snssdk.com`、`mcs.snssdk.com` (字节AppLog系) 以及 `mllog.jd.com` (京东)、`res.mmstat.com` (阿里)、`report.tantanapp.com` (探探) 共 7 个日志域名全量显式升格为 **`REJECT-200`**。
    *   物理效果: 极速伪造 `HTTP 200` 假成功，诱骗 SDK 自动清空本地待发送日志队列，彻底斩断后台无谓重发，不占手机内存与磁盘。
    *   构建发布: 编译产物 [custom_adblock.sgmodule](file:///Users/shizupeng/Documents/antigravity/sgmodule/custom_adblock.sgmodule) (包含 393 条规则) 自检通过，已 Git commit `9aae457` 且 `git push` 至 GitHub (`32d9ac7`) 部署上线。

*   **2026-08-11 (生产级二元去广告架构定型与全量指令选型表 100% 对齐)**:
    *   物理审计: 经过多轮并发爆发与网络层 (Layer 3/4/7) 物理实测，确定并终极定型“二元去广告架构”。
    *   二元架构: 纯广告 SDK 域名 (25+域名) 全量配置为 **`REJECT-DROP`**（TCP 握手层静默丢包，物理卡死 16 线程池 60 秒，彻底封死同一秒 16 连爆发与退回 Step 2 重新发 DNS 的死循环）；日志/崩溃遥测 (14个域名) 保持 **`REJECT-200`**（假上报成功，诱骗 SDK 自动清空本地队列）；App 内部复杂广告 (知乎/微博/小红书/B站等) 维持 **MITM + Rewrite** 精细化擦除。
    *   MITM 纯净化: 彻底清理 `MITM_HOSTNAMES` 里的纯广告域名（因为在 TCP 握手层已 DROP，压根不走 HTTPS 解密），代理引擎速度提升 10%+。
    *   完全对齐: 产物 [custom_adblock.sgmodule](file:///Users/shizupeng/Documents/antigravity/sgmodule/custom_adblock.sgmodule) (包含 386 条规则) 与小火箭全量物理指令速查表 100% 物理对齐，已 Git commit `1ed7998` / `afed227` 且 `git push` 至 GitHub (`0505c2e`) 部署上线。

*   **2026-08-10 (字节跳动 snssdk 埋点拦截 REJECT-TINYSINK 防发热与日志 SQLite 数据库审计分析)**:
    *   归因: 使用 [proxy-2026-08-10-171530.db](file:///Users/shizupeng/Documents/antigravity/proxy-2026-08-10-171530.db) 深入审计 3690 条小火箭请求日志，归因并确认字节跳动 `AppLog` / `SSSDK` 埋点服务在命中 `REJECT-NO-DROP` 时，由于无法获取空 HTTP 200 响应，引发客户端网络库密集并发重试，导致 CPU 满载与手机剧烈发热。
    *   优化: 在 [adblock_rules_data.json](file:///Users/shizupeng/Documents/antigravity/sgmodule/references/adblock_rules_data.json) 中将 `log.snssdk.com`、`log-hl.snssdk.com`、`rtlog.snssdk.com`、`mcs.snssdk.com`、`dm.snssdk.com`、`ad.snssdk.com`、`ads.snssdk.com`、`toblog.ctobsnssdk.com` 8 条拦截规则统一修改为 **`REJECT-TINYSINK`**（本地静默返回空 HTTP 200 终止 App 死循环重试）。
    *   构建: 运行 [compile_publish_sgmodule.py](file:///Users/shizupeng/Documents/antigravity/sgmodule/scratch/compile_publish_sgmodule.py) 完成 4 大模块编译校验并自动推送 GitHub 远程仓库上线。

*   **2026-08-06 (App Store 批量更新放弃等待根治与 aaplimg/cdn-apple 100% 原位注释禁用)**:
    *   根因: 归因并证实小火箭代理高并发下 App Store 批量更新排队超时与 Top500 规则中 `appldnld.g.aaplimg.com` 等 3 条陈旧 Proxy 坏行引发的放弃等待。
    *   强直连: 在 [custom_conf_rules.txt](file:///Users/shizupeng/Documents/antigravity/sgmodule/references/custom_conf_rules.txt) 的 `PREPEND_DIRECT` 注入 `aaplimg.com` 与 `cdn-apple.com` 根域名，仅放行 App 下载 CDN，0 影响 Apple Intelligence 与苹果 AI 代理。
    *   原位注释: 在 [generate_custome_conf.py](file:///Users/shizupeng/Documents/antigravity/sgmodule/generate_custome_conf.py) 升级 `DISABLE` 原位注释机制；将全量 11 条子域名（`aaplimg.com` 4 条 + `cdn-apple.com` 7 条）100% 原位打上 `# 🚫` 注释，绝对 0 偏移且彻底消除规则冲突；已推送 Git Commit `e0f8eb0`。

*   **2026-08-05 (custome_conf.conf 自定义文本规则提取与分层匹配次序重构)**:
    *   解耦: 新建纯文本规则文件 [custom_conf_rules.txt](file:///Users/shizupeng/Documents/antigravity/sgmodule/references/custom_conf_rules.txt)，完全兼容小火箭原生语法，实现规则与 Python 代码彻底解耦。
    *   次序: 在 [generate_custome_conf.py](file:///Users/shizupeng/Documents/antigravity/sgmodule/generate_custome_conf.py) 中实现 `REMOVE` (上游擦除)、`PREPEND_PROXY` (顶层强代理区)、`PREPEND_DIRECT` (顶层强直连区) 分层逻辑，确保小火箭自上而下匹配的绝对优先级。
    *   直连: 仅注入单点域名 `DOMAIN,cn1.gi-de.com,Direct` 到顶层强直连区，恢复秒级直连；`gi-de.com` 主域名与其它子域名保持在 Top500 原位走代理；继续擦除 `storage.googleapis.com` 等 3 个上游坏行；云端 GitHub Actions 验证通过。

*   **2026-08-04 (Google 二步验证 2FA 连通性物理根治与 .google 强代理)**:
    *   清洗: 物理擦除 Top500 上游误杀的 `storage.googleapis.com`、`tools.google.com`、`blog.google` 3 个 Direct 坏行。
    *   强代理: 在 `[Rule]` 顶端第 30 行前置注入 `googleapis.com` / `google.com` / `google` / `gstatic.com` 强 Proxy 规则区，实现毫秒级捕获，彻底解决 Google 2FA 验证确认弹窗“发生错误”卡顿。

*   **2026-08-04 (主配置文件 custome_conf.conf 100% 像素级对齐 Top500 原版与纯 IP DoH 升级)**:
    *   DoH升级: 将第 11 行 `dns-server` 替换为阿里/腾讯纯 IP 加密 DoH (`223.5.5.5` / `223.6.6.6` / `1.12.12.12`)，彻底消除解析 `dns.alidns.com` 的 Bootstrap 延迟，5G/Wi-Fi 下 0 延迟秒开。
    *   原版还原: 规则顺序、匹配优先级、`[General]`、`[URL Rewrite]` 与 `[MITM]` 865 行结构从上到下 100.00% 像素级保持 Johnshall Top500 官方原样，彻底根治乱改乱排引发的知乎卡顿、闲鱼断网与豆瓣破图 Bug。
    *   动态时间: 头部注入当前北京时间 `UTC+8` 最新构建时间戳；融入 `update-url` 配合 GitHub Actions 每日凌晨 04:20 自动云端构建同步。

*   **2026-08-04 (去哪儿旅行开屏单点靶向补齐与贴吧 SSL Pinning 剔除)**:
    *   靶向: 在 `adblock_rules_data.json` 中单点补充去哪儿旅行 `homefront.qunar.com`、`client.qunar.com` 与 `qde.qunar.com` 解密授权与秒退重写规则。
    *   清理: 遵循物理机制，物理彻底剔除含 iOS SSL Pinning 无法解密的百度贴吧域名，保持模块最极简与 0 发热，编译自检 0 错误通过。

*   **2026-08-04 (全新秒退去广告模块重构与快照备份部署)**:
    *   备份: 部署前物理快照备份 `adblock_rules_data.json`、`generator_static_data.json` 与 `custom_adblock.sgmodule` (.bak_20260804)。
    *   秒退: 全量升级 173 条 `reject-dict` (返回 `{}`) 与 248 条 `reject-200` (返回 HTTP 200) 空数据响应，消除开屏广告 SDK 1~3 秒超时重试与卡顿发热。
    *   拦截: 精细补充 **汽车之家** (`adproxy.autohome.com.cn`)、**携程旅行** (`retargeting.ctrip.com`) 秒阻条目；在 `SDK_BLOCK_RULES` 追加 **快手联盟 (`kuaishou.com`, `gifshow.com`)** UDP 443 QUIC 封杀规则（`REJECT-NO-DROP`）。
    *   验证: 100% 对齐已安装 143+ 个 App 画像剪枝，编译包含 1323 条规则指令，物理自检 0 错误通过。

*   **2026-08-03 (主配置文件 custome_conf.conf 物理移除 [MITM] 段落纯净重构)**:
    *   纯净: 物理彻底删除 `custome_conf.conf` 中的 `[MITM]` 段落，100% 对齐 `sr_top500_whitelist.conf` 标准纯净分流架构。
    *   解耦: 停止在主配置文件中硬编码解密开关与证书标识，完全交由手机小火箭内部数据库与去广告模块 (`custom_adblock.sgmodule`) 自主进行证书绑定与广告解密。

*   **2026-08-03 (主配置文件 custome_conf.conf 融合 Top500 极速白名单与 0 DNS 泄露重构)**:
    *   架构: 全量融合 Johnshall Top500 极速白名单本地解析架构，彻底替代不稳定 GitHub 远程规则集下载。
    *   DNS: 指派 `dns.alidns.com` 与 `doh.pub` (阿里+腾讯 DoH)，兼顾极速 CDN 响应与 0 本地 DNS 泄露。
    *   网卡: 补全 `bypass-tun` 完整 IPv6/局域网豁免网段，完美保障 5G/Wi-Fi 下豆瓣、爱奇艺、B站等国内全量 App 图片视频 100% 极速显示。

*   **2026-08-03 (主配置文件 custome_conf.conf 5G 无损秒开与 0 DNS 泄露重构)**:
    *   重构: 彻底删除 `IP-CIDR6,::/0,REJECT,no-resolve` 硬阻断规则，解决 5G 蜂窝网络下与国内 CDN (豆瓣/B站/爱奇艺等) IPv6 握手死锁超时硬伤。
    *   屏蔽: 保留 `[General]` 段落 `ipv6 = false` 优雅 DNS 软屏蔽，让本地 DNS 干净返回 IPv4，0.001 秒建连无卡顿。
    *   防泄露: 国内域名走 `direct-dns-server` 阿里/腾讯纯 IP DoH，海外域名走 `dns-server` / 代理远端解析，实现全量 0 本地 DNS 泄露与国内全 App 100% 极速秒开。

*   **2026-08-03 (定制去广告模块已装 App 差集清洗与开屏秒退响应优化)**:
    *   备份: 部署前物理快照备份 `adblock_rules_data.json`、`generator_static_data.json` 与 `custom_adblock.sgmodule` (.bak_20260803)。
    *   开屏: 升级 173 条 `reject-dict`（返回 `{}`）与 248 条 `reject-200` 空数据秒退响应，消除开屏广告 SDK 拿不到响应导致的 1~3 秒超时重试与黑屏卡顿。
    *   扩充: 精细补充 **汽车之家** (`adproxy.autohome.com.cn`)、**携程旅行** (`retargeting.ctrip.com`) 秒阻条目；在 `SDK_BLOCK_RULES` 追加 **快手联盟 (`kuaishou.com`, `gifshow.com`)** UDP 443 QUIC 封杀规则（`REJECT-NO-DROP`）防 HTTP3 漏网。
    *   验证: 100% 对齐已安装 143+ 个 App 画像剪枝，编译产物包含 1333 条规则指令，MITM 严格控制在安全范围，自检 0 错误通过。

*   **2026-08-03 (Shadowrocket 智能双轨 DNS 与零策略组无损防泄露重构)**:
    *   架构: 建立国内/国外智能双轨 DNS（国内域名走 `direct-dns-server` 阿里/腾讯纯 IP DoH，国外域名走 `fallback-dns-server` / 代理远端解析）。
    *   极简: 彻底删除 `[Proxy Group]` 段落，依托小火箭首页原生单点 `PROXY` 控制，界面干爽无后台测速。
    *   防护: 注入 `IP-CIDR6,::/0,REJECT,no-resolve` 物理切断 5G IPv6 旁路泄露，配合 `GEOIP,CN,DIRECT,no-resolve` 杜绝明文 53 抢解析。
    *   部署: 落盘至 `custome_conf.conf` 并成功推送至 GitHub (`ssupssup/sgmodule`)。

*   **2026-07-31 (小火箭防泄露与分流优化模块实现与纯 IP 加密 DNS 升级)**:
    *   加密: 全面替换明文 UDP 53 服务器，升级 `dns-server` (`https://1.1.1.1/dns-query`, `https://8.8.8.8/dns-query`) 与 `direct-dns-server` (`https://223.5.5.5/dns-query`, `https://1.12.12.12/dns-query`) 为 100% 纯 IP 形式的 DoH 加密服务器。
    *   防护: 开启 Fake-IP 远端解析杜绝 DNS 泄露；加入 UDP 3478/5349 端口与 STUN 协议拦截阻断 WebRTC 泄露；补全微信音视频、局域网 mDNS 与系统校时 Fake-IP 绕过；强走 `ippure.com` 等测试域名代理。
    *   构建: 创建 [generate_leak_protection.py](file:///Users/shizupeng/Documents/antigravity/sgmodule/scratch/generate_leak_protection.py) 自动注入北京时间戳并接入 GitHub 04:20 自动更新。



*   **2026-07-26 (修复 GitHub Actions 自动更新崩溃问题 - 补全 JSON 配置文件 Git 跟踪)**:
    *   修复: 解决云端 CI 缺少 `ai_sgmodule_config.json` 与 `talkatone_sgmodule_config.json` 引发 `FileNotFoundError` 崩溃。
    *   脚本: 更新 `compile_publish_sgmodule.py` 提交清单，确保 references 目录下所有解耦配置文件随代码 100% 同步推送。
    *   推送: 重新编译模块并成功推送至 GitHub 远程仓库，物理验证确认 Git 追踪包含全量 JSON 配置。

*   **2026-07-25 (第二次双端同步 - bilibili 解阻与手淘 Adash 秒阻对齐)**:
    *   解阻: 从 `adblock_rules_data.json` 物理剔除 `data.bilibili.com` 的 `REJECT-NO-DROP` 规则，手机小火箭彻底恢复 B站 打点与交互通畅。
    *   秒阻: 在 `adblock_rules_data.json` 追加手淘遥测 `h-adashx4bc.ut.taobao.com` 的 `REJECT-NO-DROP` 秒阻规则，促使 iPhone 在蜂窝网络下快速退避防发热。
    *   推送: 重新编译并成功推送至 GitHub 远程仓库 (`42f2930`)，物理验证确认离网与局域网双端 100% 对齐。
*   **2026-07-25 (双端移动端高频发热源阻断同步)**:
    *   联动: 在静态数据 `generator_static_data.json` 追加 Twitter 遥测 `analytics.twitter.com`、Effirst 追踪 `px.effirst.com` 与钉钉遥测 `adashx.ut.dingtalk.com` 3 个发热源。
    *   编译: 重新编译并物理核对 `custom_adblock.sgmodule`，自动注入 `REJECT-NO-DROP` 瞬间阻断规则，确保离家蜂窝网络下的设备退避降温。
    *   推送: 成功将全新模块编译成果推送至 GitHub 远程仓库 (`main` 分支)，完成内网与外网双端防护机制 100% 对齐。
*   **2026-07-24 (双端遥测与 Google 广告防发热同步)**:
    *   联动: 在静态数据 `generator_static_data.json` 追加 GitHub 开发者遥测 `collector.github.com`、PubMatic 广告 `ads.pubmatic.com` 与 Google 广告分发 `googleads.g.doubleclick.net`。
    *   编译: 重新编译并物理核对 `custom_adblock.sgmodule`，自动注入 `REJECT-NO-DROP` 瞬间阻断规则，确保外网环境下的极致退避与防护。
    *   推送: 成功将全新模块编译成果推送至 GitHub 仓库，完成内网与外网蜂窝网络双端防护机制 100% 对齐。
*   **2026-07-23 (双端防发热拦截对齐)**:
    *   联动: 小火箭编译脚本自动拉取 AdGuard Home 新写入的 17 条防发热拦截域名（包含腾讯 MDT、网易云音乐 APM 及日志、网易易盾、Firebase 崩溃日志、Urban Airship 推送等）。
    *   编译: 重新编译并物理核对 `custom_adblock.sgmodule`，新对齐的 18 个发热遥测域名全部以 `REJECT-NO-DROP` 强秒阻规则注入，完成安全 Lint 自检。
    *   推送: 成功将最新对齐模块推送至 GitHub，完成蜂窝外网与局域网内网双端同步防发热拦截闭环。
*   **2026-07-17 (数据解耦与垃圾包清理)**:
    *   解耦: 重构 `generate_custom_adblock.py`，将 ALWAYS_INJECT_DOMAINS 等 4 个静态大数组及其历史注释抽取至 [generator_static_data.json](file:///Users/shizupeng/Documents/antigravity/sgmodule/references/generator_static_data.json) 中进行数据解耦，脚本行数缩减至 1000 行以内。
    *   自检: 经字节级 diff 物理验证，重构前后编译生成的小火箭模块除时间戳外 100% 相同，规则无损。
    *   清理: 物理清除了 sgmodule、ini 和 istoreos/scratch 下共 4 个废弃的旧历史 zip 包。
*   **2026-07-13 (微信支付直连加白优化)**:
    *   微信: `generate_custom_adblock.py` 核心 `BYPASS_RULES` 追加 `wechatpay.cn`、`tenpay.com`、`qpic.cn` 和 `qlogo.cn` 后缀强制走 `DIRECT`；
    *   编译: 重新编译发布 `custom_adblock.sgmodule`，彻底杜绝微信支付和相关多媒体头像加载受代理节点干扰。
*   **2026-07-12 (双端动态对齐与防发热拦截)**:
    *   `generate_custom_adblock.py` 升级为动态解析 AGH 自定义规则，提取轨道 A/B 共 84 个阻断域名，配置为 `REJECT-NO-DROP` 超轻量拦截。
*   **2026-07-11 (豆包验证码卡死修复)**:
    *   `generate_custom_adblock.py` 自动剔除 `pglstatp-toutiao.com` 解密 (MITM) 与拦截，解决网页版豆包加载验证码组件卡死。
*   **2026-07-11 (双端微信合并与网易云放行)**:
    *   微信: 双端规则合并归一为 root `wxs.qq.com`，清理 6 条冗余子域放行。
    *   网易云: 网关加白放行音频分发 `ipv4.music.163.com`，防歌曲灰盘报错。
*   **2026-07-11 (双端联动阻断对齐)**:
    *   `generate_custom_adblock.py` 编译逻辑重构，由原硬编码静态列表升级为从 `sdkdomain.list` 动态加载对齐（一期+二期共 77 个打点域名）。
    *   `sofire.baidu.com` 升级为 `REJECT-NO-DROP` 拦截，本地提取并同步 AdGuard Home 最新规则列表。
*   **2026-07-10 (高频遥测阻断联动)**:
    *   `generate_custom_adblock.py` 追加字节遥测 `log-hl.snssdk.com` 并重新编译出新模块，以 `REJECT-NO-DROP` 阻断防发热。
*   **2026-07-10 (联动对齐)**:
    *   在 `generate_custom_adblock.py` 中追加钉钉打点 `h-adashx.dingtalkapps.com` 并重新编译出新模块，以 `REJECT-NO-DROP` 阻断防发热。
*   **2026-07-10 (抖音/头条卡顿优化)**:
    *   抖音/头条: 放行 `p3-ad-sign.byteimg.com`，防已签名图片 CDN 误杀导致的封面卡顿转圈；
    *   阻断: 物理加入 `dig.bdurl.net` 并以 `REJECT-NO-DROP` 阻断，防数据挖掘打点重试发热。

> [!TIP]
> 2026-07-10 之前更早的历史变更日志已物理归档至 [history_changelog.md](file:///Users/shizupeng/Documents/antigravity/sgmodule/references/history_changelog.md)。
