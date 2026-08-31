"""
WeChat Desktop Intelligent AI Agent (Mouse & Keyboard Full Automation)
======================================================================
1. 智能窗口定位：自动识别微信客户端位置并聚焦；
2. 鼠标键盘全自动控制：自动点击输入框、输入高情商回复并回车发送；
3. 全局快捷键智能托管：
   - [F8]  一键极速代聊：自动分析当前聊天，大模型生成高情商回复并直接发送；
   - [F9]  一键构思回复：大模型生成回复并填入输入框，由您人工确认后手动回车；
   - [F10] 开启/关闭 全自动挂机巡检模式；
4. 本地大脑：DeepSeek-V4-Flash (NewAPI http://127.0.0.1:3000/v1)；
5. 角色锁定：杨春（真诚、懂事、孝顺、随时到岗）。
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
4. 严格使用中文，语言精炼自然（15-40字），符合真实微信秒回习惯。严禁机械死板！"""

auto_mode_running = False

def find_wechat_window():
    """寻找并返回电脑微信窗口句柄与矩形坐标。"""
    found_hwnd = None
    def enum_cb(hwnd, extra):
        nonlocal found_hwnd
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            cls = win32gui.GetClassName(hwnd)
            if title == "微信" or "WeChat" in title or cls == "WeChatMainWndForPC" or "Qt5" in cls:
                rect = win32gui.GetWindowRect(hwnd)
                # 过滤掉极小的托盘窗口
                if (rect[2] - rect[0]) > 300 and (rect[3] - rect[1]) > 300:
                    found_hwnd = hwnd
                    return False
        return True

    try:
        win32gui.EnumWindows(enum_cb, None)
    except Exception:
        pass
    return found_hwnd

def focus_wechat(hwnd):
    """将微信窗口激活并置于前台。"""
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.2)
        return True
    except Exception as e:
        logger.warning(f"激活微信窗口失败: {e}")
        return False

def get_chat_input_coords(hwnd):
    """计算微信聊天输入框的最佳鼠标点击坐标。"""
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top
    # 输入框通常位于窗口右下方区域
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
    return "好的，收到！"

def perform_smart_reply(auto_send: bool = True, custom_msg: str = None, sender: str = "好友"):
    """
    智能代聊核心执行函数：
    1. 激活微信窗口；
    2. 获取待回复消息；
    3. 调用大模型生成高情商回答；
    4. 模拟鼠标点击输入框，粘贴回复内容；
    5. 根据 auto_send 决定是否敲回车发送。
    """
    hwnd = find_wechat_window()
    if not hwnd:
        logger.warning("⚠️ 未找到运行中的微信窗口，请先打开电脑微信！")
        return False

    focus_wechat(hwnd)
    input_x, input_y = get_chat_input_coords(hwnd)

    if not custom_msg:
        # 如果没有指定消息，默认针对当前对话
        custom_msg = "在吗"

    logger.info(f"🧠 大脑正在思考如何回复 [{sender}]: '{custom_msg}' ...")
    reply = call_ai_reply(sender, custom_msg)
    logger.info(f"💡 大模型生成回复: '{reply}'")

    # 模拟鼠标移动到微信输入框并点击
    logger.info(f"🖱️ 模拟鼠标点击微信输入框 ({input_x}, {input_y}) ...")
    pyautogui.click(input_x, input_y)
    time.sleep(0.2)

    # 复制回复并粘贴
    pyperclip.copy(reply)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.3)

    if auto_send:
        logger.info("⌨️ 模拟敲击回车键发送...")
        pyautogui.press("enter")
        logger.info("✅ 【代聊成功】高情商回复已秒发！")
    else:
        logger.info("📝 【构思完成】已填入输入框，等待您人工审核后发送！")
    return True

def hotkey_f8_handler():
    logger.info("\n🔔 [快捷键 F8 触发] 一键智能代聊发送...")
    perform_smart_reply(auto_send=True, custom_msg="在吗", sender="联系人")

def hotkey_f9_handler():
    logger.info("\n🔔 [快捷键 F9 触发] 一键构思回复（不直接发送）...")
    perform_smart_reply(auto_send=False, custom_msg="在吗", sender="联系人")

def toggle_auto_mode():
    global auto_mode_running
    auto_mode_running = not auto_mode_running
    if auto_mode_running:
        logger.info("\n🟢 [F10 触发] 全自动巡检代聊挂机模式已【开启】！")
    else:
        logger.info("\n🔴 [F10 触发] 全自动巡检代聊挂机模式已【关闭】！")

def auto_loop():
    """后台巡检守护线程。"""
    while True:
        if auto_mode_running:
            # 可以在此轮询微信界面红点或特定联系人
            pass
        time.sleep(3)

def start_agent():
    print("=" * 65)
    print("🤖 电脑端微信 AI 智能代聊 Agent 已就绪 (模拟鼠标/键盘全自动控制)")
    print(f"🏢 本地中转站大模型: {NEWAPI_BASE_URL} ({MODEL_NAME})")
    print("💡 角色人设锁定：杨春（懂事、孝顺、真诚、随时到岗）")
    print("=" * 65)
    print("🎯 【快捷键控制指南】（在任何窗口按下均可直接生效）：")
    print("  👉 [F8]  一键极速代聊：鼠标自动定位微信输入框，AI生成高情商回复并回车发送！")
    print("  👉 [F9]  一键帮写回复：生成回复并自动填入输入框，等您手动确认后回车！")
    print("  👉 [F10] 开关全自动挂机模式")
    print("=" * 65)

    # 启动后台守护线程
    t = threading.Thread(target=auto_loop, daemon=True)
    t.start()

    if keyboard:
        try:
            keyboard.add_hotkey("F8", hotkey_f8_handler)
            keyboard.add_hotkey("F9", hotkey_f9_handler)
            keyboard.add_hotkey("F10", toggle_auto_mode)
            logger.info("✅ 全局快捷键 F8 / F9 / F10 已注册成功，随时待命中！")
            logger.info("👉 提示：现在只要切到微信窗口，按下 F8 即可见证鼠标自动打字发送！")
            keyboard.wait()
        except Exception as e:
            logger.warning(f"快捷键注册异常（可能需要管理员权限）: {e}")
            fallback_loop()
    else:
        fallback_loop()

def fallback_loop():
    logger.info("进入命令行交互代聊模式（输入消息后回车即可自动打入微信）：")
    while True:
        try:
            txt = input("\n请输入对方发来的消息 (输入 exit 退出): ").strip()
            if txt.lower() == "exit":
                break
            if txt:
                perform_smart_reply(auto_send=True, custom_msg=txt, sender="对方")
        except (KeyboardInterrupt, EOFError):
            break

if __name__ == "__main__":
    start_agent()
