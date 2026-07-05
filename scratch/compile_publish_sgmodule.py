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
    
    # 1. 运行三个生成脚本
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

    # 3. 远程发布到 iStoreOS 静态服务器
    print("\n📡 [3/3] 远程发布模块至 iStoreOS (192.168.2.1:2200)...")
    
    router_host = "root@192.168.2.1"
    router_port = "2200"
    ssh_key = "/Users/shizupeng/.ssh/id_ed25519_istoreos"
    remote_dir = "/www/sgmodule"
    
    # 创建远程目录
    mkdir_cmd = f"ssh -i {ssh_key} -p {router_port} -o ConnectTimeout=5 {router_host} 'mkdir -p {remote_dir}'"
    success, err = run_command(mkdir_cmd)
    if not success:
        print("❌ 远程连接软路由失败，请检查是否处于局域网环境、SSH 2200 端口以及公钥免密登录。")
        sys.exit(1)
        
    # 上传模块文件
    sgmodule_files = [
        "custom_adblock.sgmodule",
        "ai.sgmodule",
        "talkatone_proxy.sgmodule",
        "talkatone_adblock.sgmodule"
    ]
    
    upload_success = True
    for f in sgmodule_files:
        local_file = os.path.join(sgmodule_dir, f)
        if not os.path.exists(local_file):
            print(f"❌ 未找到生成的模块文件: {local_file}")
            upload_success = False
            continue
            
        scp_cmd = f"scp -O -i {ssh_key} -P {router_port} -o ConnectTimeout=5 {local_file} {router_host}:{remote_dir}/"
        ok, err = run_command(scp_cmd)
        if not ok:
            print(f"❌ 上传 {f} 失败！")
            upload_success = False
        else:
            print(f"✅ 成功发布: {f}")
            
    if upload_success:
        print("\n🎉 小火箭模块本地编译并远程发布成功！")
        print("📱 手机端本地订阅地址如下：")
        print(f"   - 定制去广告模块: http://192.168.2.1/sgmodule/custom_adblock.sgmodule")
        print(f"   - AI 分流代理模块: http://192.168.2.1/sgmodule/ai.sgmodule")
        print(f"   - Talkatone 代理模块: http://192.168.2.1/sgmodule/talkatone_proxy.sgmodule")
        print(f"   - Talkatone 拦截模块: http://192.168.2.1/sgmodule/talkatone_adblock.sgmodule")
    else:
        print("❌ 部分模块发布失败，请检查错误日志。")
        sys.exit(1)

if __name__ == "__main__":
    main()
