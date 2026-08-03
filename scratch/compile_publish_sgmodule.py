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
    
    print("🚀 [1/3] 开始本地编译小火箭模块...")
    
    # 1. 运行三个生成脚本 (共生成 4 个核心模块)
    scripts = [
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

    # 2. 安全检查 .gitignore 是否锁定 md 说明文档
    print("🔒 [2/3] 进行安全检查...")
    gitignore_path = os.path.join(sgmodule_dir, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "*.md" in content:
            print("✅ 安全检查通过：说明文档已通过 .gitignore 锁定在本地。")
        else:
            print("⚠️ 警告：.gitignore 未发现 *.md 过滤规则，可能存在敏感文档泄漏风险！")
    else:
        print("⚠️ 警告：未找到 .gitignore 文件！")

    # 3. 自动提交并推送至 GitHub 远程仓库
    print("\n📡 [3/3] 自动提交并推送模块至 GitHub 远程仓库...")
    
    # 检查是否有文件改动
    success, status_out = run_command(["git", "status", "--porcelain"], cwd=sgmodule_dir)
    if not success:
        print("❌ 获取 git 状态失败！")
        sys.exit(1)
        
    if not status_out.strip():
        print("✅ 无任何文件变动，无需推送 GitHub。")
        print("\n🎉 小火箭模块本地编译验证已完成！")
        return

    # 添加需要提交的小火箭相关文件与解耦配置文件
    files_to_add = [
        "generate_custom_adblock.py",
        "generate_ai.py",
        "generate_talkatone.py",
        "custom_adblock.sgmodule",
        "ai.sgmodule",
        "talkatone_proxy.sgmodule",
        "talkatone_adblock.sgmodule",
        "references/ai_sgmodule_config.json",
        "references/talkatone_sgmodule_config.json",
        "references/adblock_rules_data.json",
        "references/generator_static_data.json",
        ".github/workflows/auto_update.yml"
    ]



    
    # 确保只添加存在的文件
    existing_files = [f for f in files_to_add if os.path.exists(os.path.join(sgmodule_dir, f))]
    
    print("git add...")
    success, _ = run_command(["git", "add"] + existing_files, cwd=sgmodule_dir)
    if not success:
        print("❌ git add 失败！")
        sys.exit(1)
        
    # 提交变动
    print("git commit...")
    success, commit_out = run_command(["git", "commit", "-m", "chore: compile and update shadowrocket modules"], cwd=sgmodule_dir)
    if not success:
        # 如果是因为没东西提交报错，可以忽略
        if "nothing to commit" in commit_out:
            print("✅ 没有需要提交的内容。")
        else:
            print(f"❌ git commit 失败！\n{commit_out}")
            sys.exit(1)
            
    # 拉取并变基以防冲突（自动以本地编译结果解决冲突）
    print("git pull --rebase -X ours...")
    run_command(["git", "pull", "--rebase", "-X", "ours"], cwd=sgmodule_dir)
            
    # 推送至 GitHub
    print("git push...")
    success, push_out = run_command(["git", "push"], cwd=sgmodule_dir)
    if not success:
        print(f"❌ git push 失败！\n{push_out}")
        sys.exit(1)
        
    print("\n🎉 小火箭 4 个模块本地编译验证成功并已推送至 GitHub 远程仓库！")

if __name__ == "__main__":
    main()
