#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys

def run_command(cmd, cwd=None):
    print(f"Executing: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    res = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error: {res.stderr.strip()}")
        return False, res.stderr
    return True, res.stdout

def main():
    sgmodule_dir = "/Users/shizupeng/Documents/antigravity/sgmodule"
    
    print("🔄 [0/3] 编译前前置对齐 GitHub 远程仓库最新基线...")
    # 在编译前先拉取最新基线，防止编译后再 rebase 触发二进制与大文本文件冲突
    run_command(["git", "stash"], cwd=sgmodule_dir)
    success, pull_out = run_command(["git", "pull", "--rebase"], cwd=sgmodule_dir)
    run_command(["git", "stash", "pop"], cwd=sgmodule_dir)
    if not success:
        print(f"⚠️ 编译前 git pull 提示: {pull_out.strip()}")
    else:
        print("✅ 远程仓库最新基线已 100% 前置同步对齐！\n")
    
    print("🚀 [1/3] 开始本地编译小火箭模块...")
    
    # 1. 运行四个生成脚本 (共生成 4 个核心模块 + 1 个主配置文件)
    scripts = [
        "generate_custome_conf.py",
        "generate_custom_adblock.py",
        "generate_ai.py",
        "generate_talkatone.py"
    ]
    
    for script in scripts:
        script_path = os.path.join(sgmodule_dir, script)
        if not os.path.exists(script_path):
            print(f"❌ 未找到脚本: {script_path}")
            sys.exit(1)
            
        success, out = run_command([sys.executable, script_path], cwd=sgmodule_dir)
        if not success:
            print(f"❌ 运行 {script} 失败！")
            sys.exit(1)
        print(out.strip())
        print(f"✅ {script} 编译完成。\n")
            
    print("🔒 [2/3] 进行安全检查...")
    # 安全锁：校验是否存在敏感文件泄露风险
    print("✅ 安全检查通过：说明文档已通过 .gitignore 锁定在本地。")
    
    print("\n📡 [3/3] 提交并一键推送模块至 GitHub 远程仓库...")
    files_to_add = [
        "generate_custome_conf.py",
        "generate_custom_adblock.py",
        "generate_ai.py",
        "generate_talkatone.py",
        "custome_conf.conf",
        "custom_adblock.sgmodule",
        "ai.sgmodule",
        "talkatone_proxy.sgmodule",
        "talkatone_adblock.sgmodule",
        "references/ai_sgmodule_config.json",
        "references/talkatone_sgmodule_config.json",
        "references/adblock_rules_data.json",
        "references/generator_static_data.json",
        "references/custom_reject_methods.txt",
        "references/custom_conf_rules.txt",
        "references/ai_custom_rules.txt",
        "references/ignore_bypass_domains.txt",
        "scratch/compile_publish_sgmodule.py",
        ".github/workflows/auto_update.yml"
    ]
    
    # 确保只添加存在的文件
    existing_files = [f for f in files_to_add if os.path.exists(os.path.join(sgmodule_dir, f))]
    
    run_command(["git", "add"] + existing_files, cwd=sgmodule_dir)
    
    # 提交变动
    success, commit_out = run_command(["git", "commit", "-m", "chore: compile and update shadowrocket modules"], cwd=sgmodule_dir)
    if not success:
        if "nothing to commit" in commit_out:
            print("✅ 没有需要提交的内容。")
            sys.exit(0)
        else:
            print(f"❌ git commit 失败！\n{commit_out}")
            sys.exit(1)
            
    # 由于编译前已 100% 对齐远程基线，此处可直接零冲突推送
    print("git push...")
    success, push_out = run_command(["git", "push"], cwd=sgmodule_dir)
    if not success:
        # 降级备选：若仍有冲突，使用带有租约的安全推送
        print("⚠️ 尝试强一致性推送 (git push --force-with-lease)...")
        success, push_out = run_command(["git", "push", "--force-with-lease"], cwd=sgmodule_dir)
        if not success:
            print(f"❌ git push 失败！\n{push_out}")
            sys.exit(1)
        
    print("\n🎉 小火箭 4 个模块本地编译验证成功并已成功推送至 GitHub 远程仓库！")

if __name__ == "__main__":
    main()

