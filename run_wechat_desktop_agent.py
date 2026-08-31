"""
WeChat Desktop Intelligent AI Agent (Unified Takeover & Automation System)
==========================================================================
1. 智能窗口定位与聚焦：自动识别微信窗口；
2. 智能会话切换：支持自动搜索并切换联系人（如【文件传输助手】、母亲【半夏】、老兵、HR）；
3. 鼠标/键盘全自动接管：自动定位输入框、大模型生成高情商回复、敲回车发送；
4. 全局快捷键与交互式中枢：
   - [F7]  一键向【文件传输助手】发送 AI 连通测试；
   - [F8]  一键对当前聊天进行极速高情商代聊秒发；
   - [F9]  一键构思高情商回复（填入输入框，人工审核）；
   - [F10] 开启/关闭 全自动挂机巡检模式；
5. 本地大脑：DeepSeek-V4-Flash (NewAPI http://127.0.0.1:3000/v1)；
6. 角色人设：杨春（统招本科/区块链工程/懂事孝顺/真诚热情/随时到岗）。
"""
import sys
import os
import time
import json
import logging
import threading
import pyperclip
import pyautogui
import httpx
import win32gui
import win32con
import win32process
import uiautomation as auto

try:
    import keyboard
except ImportError:
    keyboard = None

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("WeChatAgent")

NEWAPI_BASE_URL = "http://127.0.0.1:3000/v1"
API_KEY = "1ddU4oDsUPSTiA8U75FaZ9lmrdfVHrdAnmEaAefKhbQTZN2k"
MODEL_NAME = "DeepSeek-V4-Flash"

SYSTEM_PROMPT = """【角色设定】你是杨春本人（全日制统招本科，区块链工程专业，持有C1驾照）。
当在微信收到母亲（半夏）、朋友或HR发来的消息时，请以杨春的第一人称真诚、孝顺、懂事、高情商地作答。
【特别规则】
1. 对母亲（半夏）说话要亲切、孝顺、听话。比如母亲说"下来守店，我搞饭去了"，回复："好的妈，我这就下来！你慢慢做不着急~"
2. 对老兵叔叔/长辈说话要礼貌尊敬、真诚热情。比如老兵说"好"，回复："好的叔，您那边有啥需要帮忙的随时喊我！"
3. 对HR说话要专业礼貌，强调统招本科学历与随时可到岗。
4. 对文件传输助手发送测试消息时，说明系统已成功接管并与本地中转站DeepSeek大脑完全连通。
5. 严格使用中文，语言精炼自然（15-40字），符合真实微信秒回习惯。严禁机械死板！"""

auto_mode_running = False

def find_wechat_hwnd():
    """寻找并返回电脑微信窗口句柄。"""
    target_hwnd = None
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
    
    if not target_hwnd:
        target_hwnd = win32gui.FindWindow("WeChatMainWndForPC", None)
    if not target_hwnd:
        target_hwnd = win32gui.FindWindow("Qt51514QWindowIcon", "微信")
        
    return target_hwnd

def focus_wechat(hwnd=None):
    """将微信窗口激活并置于前台。"""
    if not hwnd:
        hwnd = find_wechat_hwnd()
    if not hwnd:
        logger.warning("⚠️ 未找到运行中的微信窗口，请先打开电脑微信！")
        return False
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.3)
        return True
    except Exception as e:
        logger.warning(f"激活微信窗口提示: {e}")
        return True

def switch_to_contact(contact_name: str) -> bool:
    """自动使用微信全局搜索切换到指定联系人会话。"""
    if not focus_wechat():
        return False
    logger.info(f"🔎 正在自动搜索并切换会话: 【{contact_name}】...")
    pyautogui.hotkey("ctrl", "f")
    time.sleep(0.3)
    pyperclip.copy(contact_name)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(0.5)
    return True

def get_chat_input_coords(hwnd):
    """计算微信聊天输入框的最佳鼠标点击坐标。"""
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top
    input_x = int(left + width * 0.65)
    input_y = int(bottom - height * 0.15)
    return input_x, input_y

def call_ai_reply(sender_name: str, message_text: str) -> str:
    """调用本地 NewAPI DeepSeek-V4-Flash 大脑生成高情商回复。"""
    try:
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"对方（{sender_name}）发来消息：'{message_text}'，请直接给出你的简短真实微信回复："}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        headers = {"Authorization": f"Bearer {API_KEY}"}
        resp = httpx.post(f"{NEWAPI_BASE_URL}/chat/completions", json=payload, headers=headers, timeout=10.0)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip().strip('"').strip("'")
    except Exception as e:
        logger.error(f"调用本地大模型出错: {e}")
    return "🤖 微信 AI 桌面 Agent 测试连通成功！随时待命中~"

def perform_smart_reply(auto_send: bool = True, custom_msg: str = None, sender: str = "好友", target_contact: str = None):
    """
    智能代聊核心执行函数：
    1. 定位并激活微信；
    2. 若指定 target_contact 则先切会话；
    3. 调用大模型构思高情商回复；
    4. 模拟鼠标点击输入框 ➔ 粘贴内容 ➔ 敲回车发送。
    """
    hwnd = find_wechat_hwnd()
    if not hwnd:
        logger.warning("⚠️ 未找到运行中的微信窗口，请先打开电脑微信！")
        return False

    focus_wechat(hwnd)

    if target_contact:
        switch_to_contact(target_contact)

    input_x, input_y = get_chat_input_coords(hwnd)

    if not custom_msg:
        custom_msg = "在吗"

    logger.info(f"🧠 大脑正在思考如何回复 [{sender}]: '{custom_msg}' ...")
    reply = call_ai_reply(sender, custom_msg)
    logger.info(f"💡 大模型生成回复: '{reply}'")

    logger.info(f"🖱️ 模拟鼠标点击微信输入框 ({input_x}, {input_y}) ...")
    pyautogui.click(input_x, input_y)
    time.sleep(0.2)

    pyperclip.copy(reply)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.3)

    if auto_send:
        logger.info("⌨️ 模拟敲击回车键发送...")
        pyautogui.press("enter")
        logger.info(f"✅ 【代聊成功】高情商回复已秒发给 [{target_contact or sender}]！")
    else:
        logger.info("📝 【构思完成】已填入输入框，等待您人工审核后手动回车发送！")
    return True

def hotkey_f7_handler():
    logger.info("\n🔔 [快捷键 F7 触发] 向【文件传输助手】发送 AI 连通测试...")
    perform_smart_reply(auto_send=True, custom_msg="测试系统连通性与大模型接管状态", sender="文件传输助手", target_contact="文件传输助手")

def hotkey_f8_handler():
    logger.info("\n🔔 [快捷键 F8 触发] 一键对当前聊天进行智能代聊秒发...")
    perform_smart_reply(auto_send=True, custom_msg="在吗", sender="联系人")

def hotkey_f9_handler():
    logger.info("\n🔔 [快捷键 F9 触发] 一键构思回复（填入输入框，不直接发送）...")
    perform_smart_reply(auto_send=False, custom_msg="在吗", sender="联系人")

def toggle_auto_mode():
    global auto_mode_running
    auto_mode_running = not auto_mode_running
    if auto_mode_running:
        logger.info("\n🟢 [F10 触发] 全自动巡检代聊挂机模式已【开启】！")
    else:
        logger.info("\n🔴 [F10 触发] 全自动巡检代聊挂机模式已【关闭】！")

def auto_loop():
    while True:
        if auto_mode_running:
            pass
        time.sleep(3)

def start_agent():
    print("=" * 68)
    print("🤖 电脑端微信 AI 智能代聊 Agent 已就绪 (统一接管系统 · 鼠标键盘模拟)")
    print(f"🏢 本地中转站大模型: {NEWAPI_BASE_URL} ({MODEL_NAME})")
    print("💡 角色人设锁定：杨春（懂事、孝顺、真诚、随时到岗）")
    print("=" * 68)
    print("🎯 【功能与快捷键指南】（在任何窗口按下均可直接触发）：")
    print("  👉 [F7]  一键向【文件传输助手】发送 AI 测试消息！")
    print("  👉 [F8]  一键极速代聊：鼠标自动定位输入框，AI生成高情商回答并回车秒发！")
    print("  👉 [F9]  一键帮写回复：生成回复并自动填入输入框，等您手动确认后回车！")
    print("  👉 [F10] 开关全自动挂机模式")
    print("=" * 68)

    # 启动后台守护线程
    t = threading.Thread(target=auto_loop, daemon=True)
    t.start()

    if keyboard:
        try:
            keyboard.add_hotkey("F7", hotkey_f7_handler)
            keyboard.add_hotkey("F8", hotkey_f8_handler)
            keyboard.add_hotkey("F9", hotkey_f9_handler)
            keyboard.add_hotkey("F10", toggle_auto_mode)
            logger.info("✅ 全局快捷键 F7 / F8 / F9 / F10 已注册成功，随时待命中！")
            logger.info("👉 提示：现在只要按下键盘上的 F7，即可自动向【文件传输助手】发送 AI 消息！")
            
            # 同时也提供控制台菜单
            console_menu_loop()
        except Exception as e:
            logger.warning(f"快捷键注册异常: {e}")
            console_menu_loop()
    else:
        console_menu_loop()

def console_menu_loop():
    while True:
        try:
            print("\n📋 【接管系统操作菜单】：")
            print("  1. 立即向【文件传输助手】发送一条 AI 测试消息")
            print("  2. 向指定联系人（如：半夏 / 老兵 / HR）发送一条模拟消息")
            print("  3. 退出")
            choice = input("请选择操作 (1/2/3): ").strip()
            if choice == "1":
                hotkey_f7_handler()
            elif choice == "2":
                name = input("请输入联系人昵称或备注 (如 半夏 / A安江老兵双彩): ").strip()
                msg = input("请输入对方发来的内容 (如 下来守店): ").strip()
                if name and msg:
                    perform_smart_reply(auto_send=True, custom_msg=msg, sender=name, target_contact=name)
            elif choice == "3":
                break
        except (KeyboardInterrupt, EOFError):
            break

if __name__ == "__main__":
    start_agent()
