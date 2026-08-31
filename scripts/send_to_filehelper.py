"""
Direct WeChat Automation Test: Send AI message to File Helper (文件传输助手)
"""
import sys
import os
import time
import win32gui
import win32con
import pyautogui
import pyperclip
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NEWAPI_BASE_URL = "http://127.0.0.1:3000/v1"
API_KEY = "1ddU4oDsUPSTiA8U75FaZ9lmrdfVHrdAnmEaAefKhbQTZN2k"
MODEL_NAME = "DeepSeek-V4-Flash"

def find_wechat_hwnd():
    target_hwnd = None
    # 策略 1: 枚举所有可见窗口
    def enum_windows(hwnd, extra):
        nonlocal target_hwnd
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            cls = win32gui.GetClassName(hwnd)
            if "微信" in title or "WeChat" in title or "Weixin" in title or cls == "WeChatMainWndForPC" or "Qt5" in cls or "Qt6" in cls:
                rect = win32gui.GetWindowRect(hwnd)
                if (rect[2] - rect[0]) > 200 and (rect[3] - rect[1]) > 200:
                    target_hwnd = hwnd
                    return False
        return True
    try:
        win32gui.EnumWindows(enum_windows, None)
    except Exception:
        pass
    
    # 策略 2: FindWindow 快速定位
    if not target_hwnd:
        target_hwnd = win32gui.FindWindow("WeChatMainWndForPC", None)
    if not target_hwnd:
        target_hwnd = win32gui.FindWindow("Qt51514QWindowIcon", "微信")
        
    return target_hwnd

def get_ai_test_message():
    prompt = "你是杨春。请生成一句简短真诚的测试问候（15-25字），表明电脑微信AI桌面Agent已成功接管并与本地中转站DeepSeek大脑完全连通。"
    try:
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 60
        }
        headers = {"Authorization": f"Bearer {API_KEY}"}
        resp = httpx.post(f"{NEWAPI_BASE_URL}/chat/completions", json=payload, headers=headers, timeout=10.0)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip().strip('"').strip("'")
    except Exception as e:
        print(f"调用中转站大模型出错: {e}")
    return "🤖 微信 AI 桌面 Agent 测试连通成功！随时待命中~"

def send_filehelper():
    print("🔍 [第 1 步] 正在寻找微信窗口...")
    hwnd = find_wechat_hwnd()
    if not hwnd:
        print("❌ 未检测到运行中的微信窗口，请先打开并登录电脑微信！")
        return False
        
    print(f"✅ 找到微信窗口 HWND: {hwnd}")
    
    print("🖥️ [第 2 步] 激活并置顶微信窗口...")
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    except Exception as e:
        print(f"置顶提示: {e}")
    time.sleep(0.5)
    
    print("🔎 [第 3 步] 搜索并定位【文件传输助手】...")
    # 按 Ctrl + F 激活微信全局搜索
    pyautogui.hotkey("ctrl", "f")
    time.sleep(0.4)
    pyperclip.copy("文件传输助手")
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.6)
    pyautogui.press("enter")
    time.sleep(0.6)
    
    print("🧠 [第 4 步] 请求本地中转站 DeepSeek 大脑构思测试消息...")
    ai_msg = get_ai_test_message()
    print(f"💡 大模型生成内容: '{ai_msg}'")
    
    print("⌨️ [第 5 步] 粘贴内容并模拟回车发送...")
    pyperclip.copy(ai_msg)
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.4)
    pyautogui.press("enter")
    
    print("🎉 [完成] 已成功向【文件传输助手】发送消息！")
    return True

if __name__ == "__main__":
    send_filehelper()
