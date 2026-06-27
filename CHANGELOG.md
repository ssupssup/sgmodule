# 小火箭模块 (Shadowrocket sgmodule) 规则演进纪要 (CHANGELOG)

本纪要记录了 `sgmodule/` 目录下小火箭分流与广告拦截模块的历史演进逻辑，以保留核心“回忆”。

## 模块设计演进

### 🛠 动态模块化生成时代（当前最新）
* **代表文件**：
  * `ai.sgmodule` (由 `generate_ai.py` 动态生成)
  * `talkatone_proxy.sgmodule` & `talkatone_adblock.sgmodule` (由 `generate_talkatone.py` 动态生成)
  * `custom_adblock.sgmodule` (由 `generate_custom_adblock.py` 动态生成)
* **核心改进**：
  * **2026年6月（当前）**：优化 `custom_adblock.sgmodule` 的 `[Script]` 部分去重逻辑。若 App 已在 `OVERRIDE_APPS` 中定义专属高级规则（如知乎、哔哩哔哩），则在生成时自动过滤跳过其在 BlackMatrix7 基础库中的脚本规则，彻底消除双重 JS 篡改导致的回包数据损坏和 App 闪退/白屏隐患。
  * 摒弃了早期庞大杂乱的单体静态文件，转为通过 Python 脚本从最新的远程列表（例如 ssupssup/ini 的对应分流 list）拉取规则并格式化生成最新的 `.sgmodule` 模块。
  * 细分了 AI 分流、Talkatone 代理与广告拦截、以及通用自定义去广告模块，实现随用随挂。

### 📅 2026年1月
* **代表文件**：`custom_static_talkatone_adblock260119.sgmodule` (静态备份)
* **核心特征**：
  * 将 Talkatone 在 iOS 端的应用去广告域名进行静态打包，用于本地小火箭载入。

### 📅 2025年12月
* **代表文件**：`custom_static_talkatone_proxy251213.sgmodule` (静态备份)
* **核心特征**：
  * 初版 Talkatone 代理规则静态配置，解决 Talkatone 在 iOS 端的代理分流和登录问题。
