"""
Neuro 智能体服务管理控制台 (CLI & 桌面交互)
支持：status (巡检) | stop (停止) | start (启动) | restart (重启)
"""

import sys
import os
import time
import subprocess
import requests
import psutil
import ctypes

def check_ollama() -> bool:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

def find_listener_process():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline') or []
            cmd_str = " ".join(cmdline)
            if "wechat_silent_listener.py" in cmd_str:
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None

def find_wechat_window():
    user32 = ctypes.windll.user32
    hDesk = user32.OpenInputDesktop(0, False, 0x01FF)
    if hDesk:
        user32.SetThreadDesktop(hDesk)
    hwnd = user32.FindWindowW("Qt51514QWindowIcon", "微信")
    if hwnd and user32.IsWindow(hwnd):
        return hwnd
    return None

def do_status():
    print("=" * 65)
    print("      🤖 Neuro 微信智能体系统 · 运行状态巡检")
    print("=" * 65)
    print()

    # 1. 微信客户端
    hwnd = find_wechat_window()
    if hwnd:
        print("  [1] 电脑微信 4.1 客户端:")
        print(f"      🟢 运行中 (窗口句柄: 0x{hwnd:X})")
    else:
        print("  [1] 电脑微信 4.1 客户端:")
        print("      🔴 未检测到微信窗口！请先打开电脑微信并登录。")
    print()

    # 2. 本地大模型服务
    ollama_ok = check_ollama()
    if ollama_ok:
        print("  [2] 本地大脑推理服务 (Ollama / DeepSeek-R1 8B):")
        print("      🟢 运行中 (http://localhost:11434 响应正常，AMD ROCm GPU 加速)")
    else:
        print("  [2] 本地大脑推理服务 (Ollama / DeepSeek-R1 8B):")
        print("      🔴 未运行 (端口 11434 无响应)")
    print()

    # 3. 微信静默监听器
    proc = find_listener_process()
    if proc:
        try:
            mem_mb = proc.memory_info().rss / 1024 / 1024
            create_time = time.strftime('%H:%M:%S', time.localtime(proc.create_time()))
            print("  [3] 微信 4.1 静默监听服务 (WeChat Silent Gateway):")
            print(f"      🟢 正在后台监听中 (PID: {proc.pid}, 内存: {mem_mb:.1f}MB, 启动于 {create_time})")
            print("      💡 状态良好！您在手机微信【文件传输助手】发送消息即可随时交互。")
        except Exception:
            print("  [3] 微信 4.1 静默监听服务 (WeChat Silent Gateway):")
            print("      🟢 正在后台监听中")
    else:
        print("  [3] 微信 4.1 静默监听服务 (WeChat Silent Gateway):")
        print("      🔴 未运行 (当前未监听微信消息)")
    print()

    print("=" * 65)

def do_stop():
    print("=" * 65)
    print("      🛑 正在停止 Neuro 微信监听服务...")
    print("=" * 65)
    stopped_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline') or []
            cmd_str = " ".join(cmdline)
            if "wechat_silent_listener.py" in cmd_str:
                print(f"  正在终止监听进程 PID {proc.pid} ...")
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except psutil.TimeoutExpired:
                    proc.kill()
                stopped_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if stopped_count > 0:
        print(f"  ✅ 已成功停止 {stopped_count} 个 Neuro 监听进程！")
        print("  💡 微信自动监听已解除，不再自动回复文件传输助手。")
    else:
        print("  ℹ️ 当前没有正在运行的 Neuro 微信监听服务。")
    print("=" * 65)

def do_start():
    print("=" * 65)
    print("      🚀 正在启动 Neuro 微信监听服务...")
    print("=" * 65)

    existing = find_listener_process()
    if existing:
        print(f"  ⚠️ Neuro 监听服务已经在运行中 (PID: {existing.pid})，无需重复启动。")
        print("=" * 65)
        return

    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wechat_silent_listener.py")
    if not os.path.isfile(script_path):
        print(f"  ❌ 未找到脚本: {script_path}")
        print("=" * 65)
        return

    # 启动后台无窗口进程
    creationflags = 0x08000000 # CREATE_NO_WINDOW
    proc = subprocess.Popen(
        [sys.executable, script_path],
        cwd=os.path.dirname(script_path),
        creationflags=creationflags
    )
    time.sleep(1.5)

    if proc.poll() is None:
        print(f"  ✅ Neuro 微信静默监听服务已成功在后台启动 (PID: {proc.pid})！")
        print("  💡 您现在可以在手机端微信【文件传输助手】发送消息测试。")
    else:
        print(f"  ❌ 启动失败，进程退出码: {proc.returncode}")
    print("=" * 65)

if __name__ == "__main__":
    action = sys.argv[1].lower() if len(sys.argv) > 1 else "status"
    if action == "status":
        do_status()
    elif action == "stop":
        do_stop()
    elif action == "start":
        do_start()
    elif action == "restart":
        do_stop()
        time.sleep(1)
        do_start()
    else:
        print(f"未知指令: {action}。支持: status | start | stop | restart")
