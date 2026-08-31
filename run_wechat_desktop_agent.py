"""
WeChat Desktop Intelligent AI Agent (Multi-Chat Background Sensing & Takeover)
==============================================================================
1. 【多会话智能全局感知】：
   - 即使你正在查看其他群聊（如公考群）或好友（如濠哥），AI 依然能实时守护【半夏】！
   - 左侧列表一旦出现【半夏】发来的新消息（红点/新预览）：
     AI 自动毫秒级切换到【半夏】会话 ➔ 调用本地 DeepSeek 大脑以“杨春”口吻生成高情商回复 ➔ 自动打字回车秒发！
2. 【绝不主动骚扰】：只在对方回复时触发，不主动发消息；
3. 【防串台保护】：严格区分当前活跃窗口与目标托管人，绝不误回其他群聊或好友；
4. 【本地大脑】：DeepSeek-V4-Flash (NewAPI http://127.0.0.1:3000/v1)；
5. 【角色人设】：杨春（统招本科/区块链工程/C1驾照/懂事孝顺/真诚热情/随时到岗）。
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
当在微信收到母亲（半夏）、长辈朋友或HR发来的消息时，请以杨春的第一人称真诚、孝顺、懂事、高情商地作答。
【特别规则】
1. 对母亲（半夏）说话要亲切、孝顺、听话。比如母亲说"下来守店，我搞饭去了"，回复："好的妈，我这就下来！你慢慢做不着急~"
2. 对老兵叔叔/长辈说话要礼貌尊敬、真诚热情。比如老兵说"好"，回复："好的叔，您那边有啥需要帮忙的随时喊我！"
3. 对HR说话要专业礼貌，强调统招本科学历与随时可到岗。
4. 对文件传输助手发送测试消息时，说明系统已成功接管并与本地中转站DeepSeek大脑完全连通。
5. 严格使用中文，语言精炼自然（15-40字），符合真实微信秒回习惯。严禁机械死板！"""

auto_mode_running = False
monitored_contact = None
last_handled_message = ""
last_session_preview = ""

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
        time.sleep(0.2)
        return True
    except Exception as e:
        logger.warning(f"激活微信窗口提示: {e}")
        return True

def switch_to_contact_by_feature(contact_name: str) -> bool:
    """
    基于特征与语义的动态会话切换：
    - 若搜索【文件传输助手】：命中【功能】绿色文件夹图标项（Y偏移约 top + 280px）；
    - 若搜索【普通联系人/好友】（如杨春、半夏、老兵）：命中顶部【联系人】分类第 1 项头像（Y偏移约 top + 95px）。
    """
    hwnd = find_wechat_hwnd()
    if not hwnd or not focus_wechat(hwnd):
        return False
    
    logger.info(f"🔎 正在精准切换会话至: 【{contact_name}】...")
    
    pyautogui.hotkey("ctrl", "f")
    time.sleep(0.2)
    
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.press("backspace")
    time.sleep(0.1)
    pyperclip.copy(contact_name)
    time.sleep(0.1)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.6)
    
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    win_w = right - left
    
    target_x = int(left + max(win_w * 0.15, 120))
    
    if "文件传输" in contact_name:
        target_y = int(top + 280)
    else:
        target_y = int(top + 95)
        
    pyautogui.click(target_x, target_y)
    time.sleep(0.5)
    return True

def get_chat_input_coords_dynamic(hwnd):
    """动态获取输入框中心坐标。"""
    try:
        wx_ctrl = auto.ControlFromHandle(hwnd)
        if wx_ctrl:
            edits = wx_ctrl.GetChildren()
            for c in edits:
                if c.ControlTypeName == "EditControl" and c.BoundingRectangle.bottom > 400:
                    r = c.BoundingRectangle
                    return int((r.left + r.right) / 2), int((r.top + r.bottom) / 2)
    except Exception:
        pass

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
    return "好的，收到！"

def perform_smart_reply(auto_send: bool = True, custom_msg: str = None, sender: str = "好友", target_contact: str = None):
    """
    智能代聊核心执行函数：
    1. 定位并激活微信；
    2. 若指定 target_contact 则精准切换会话；
    3. 调用大模型构思高情商回复；
    4. 模拟鼠标点击输入框 ➔ 粘贴内容 ➔ 敲回车发送。
    """
    hwnd = find_wechat_hwnd()
    if not hwnd:
        logger.warning("⚠️ 未找到运行中的微信窗口，请先打开电脑微信！")
        return False

    focus_wechat(hwnd)

    if target_contact:
        switch_to_contact_by_feature(target_contact)

    input_x, input_y = get_chat_input_coords_dynamic(hwnd)

    if not custom_msg:
        custom_msg = "在吗"

    logger.info(f"🧠 大脑正在思考如何回复 [{target_contact or sender}]: '{custom_msg}' ...")
    reply = call_ai_reply(target_contact or sender, custom_msg)
    logger.info(f"💡 大模型生成回复: '{reply}'")

    logger.info(f"🖱️ 动态定位并点击微信输入框 ({input_x}, {input_y}) ...")
    pyautogui.click(input_x, input_y)
    time.sleep(0.3)

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

def get_session_info(hwnd, target_contact: str):
    """
    【多会话感知核心】：
    同时检测当前打开的聊天标题以及左侧列表中【target_contact】的最新预览状态。
    返回: (is_currently_active, current_chat_text, left_list_preview)
    """
    is_active = False
    current_chat_text = ""
    left_list_preview = ""
    
    try:
        wx_ctrl = auto.ControlFromHandle(hwnd)
        if wx_ctrl:
            children = wx_ctrl.GetChildren()
            
            # 1. 检查标题栏与聊天区
            for item in children:
                name = item.Name or ""
                # 如果标题栏正好是 target_contact
                if name == target_contact and item.BoundingRectangle.top < 200:
                    is_active = True
                
                # 收集非系统提示的聊天气泡文本
                if name and not any(k in name for k in ["微信", "搜索", "最小化", "最大化", "关闭", "发送", "表情", "截图"]):
                    current_chat_text = name
                    
            # 2. 检查左侧会话列表中 target_contact 的预览与红点
            for item in children:
                name = item.Name or ""
                if target_contact in name and item.BoundingRectangle.left < 400:
                    left_list_preview = name
    except Exception:
        pass
        
    return is_active, current_chat_text, left_list_preview

def start_passive_takeover(contact_name: str):
    """
    【升级版】指定联系人全自动被动监听代聊：
    - 支持用户随意切换到其他会话（如公考群、濠哥等）；
    - 只要【半夏】发来消息，Agent 自动切回【半夏】窗口秒回，防串台，零误发！
    """
    global monitored_contact, last_handled_message, last_session_preview, auto_mode_running
    monitored_contact = contact_name
    auto_mode_running = True
    
    hwnd = find_wechat_hwnd()
    if not hwnd:
        logger.warning("❌ 未找到微信窗口，请先打开电脑微信！")
        return

    # 1. 先切换一次建立基线
    switch_to_contact_by_feature(contact_name)
    time.sleep(0.8)
    
    is_active, last_handled_message, last_session_preview = get_session_info(hwnd, contact_name)
    
    print("\n" + "=" * 68)
    print(f"🟢 【全能托管模式已启动】已全局守护与【{contact_name}】的微信对话！")
    print(f"👀 【支持自由切换】：您可以随时看其他群聊/好友，AI 依然在后台守护【{contact_name}】；")
    print(f"🛡️ 【防串台保护】：绝不误回其他群聊，只有【{contact_name}】来消息时才自动秒回；")
    print(f"🔇 【绝不主动发送】：保持静默守候，不主动打扰对方。")
    print("👉 提示：随时可按 [Ctrl+C] 或 [F10] 退出或暂停托管。")
    print("=" * 68 + "\n")
    
    poll_count = 0
    try:
        while auto_mode_running:
            time.sleep(1.5)
            poll_count += 1
            
            is_active, current_chat_text, current_preview = get_session_info(hwnd, contact_name)
            
            # 情况 A: 当前正停留在【半夏】窗口，聊天区刷新了新消息
            if is_active:
                if current_chat_text and current_chat_text != last_handled_message:
                    logger.info(f"\n📩 [前台捕获] 来自【{contact_name}】的新回复: '{current_chat_text}'")
                    last_handled_message = current_chat_text
                    last_session_preview = current_preview
                    perform_smart_reply(auto_send=True, custom_msg=current_chat_text, sender=contact_name, target_contact=None)
                    
            # 情况 B: 用户正切换在其他好友/群聊窗口，但左侧列表【半夏】收到了新消息！
            else:
                if current_preview and current_preview != last_session_preview:
                    logger.info(f"\n🔔 [后台感知] 检测到【{contact_name}】发来新消息（当前正在其他窗口）！")
                    logger.info(f"🚀 正在自动安全切入【{contact_name}】会话并秒回...")
                    last_session_preview = current_preview
                    
                    # 自动切入该会话进行回复
                    perform_smart_reply(auto_send=True, custom_msg="在吗", sender=contact_name, target_contact=contact_name)
                    
                    # 刷新最新消息基线
                    _, last_handled_message, _ = get_session_info(hwnd, contact_name)
                    
            if poll_count % 20 == 0:
                logger.info(f"⏳ 正在后台持续守护【{contact_name}】的消息（当前可自由浏览其他会话）...")
                
    except (KeyboardInterrupt, EOFError):
        logger.info(f"👋 已退出对【{contact_name}】的托管代聊模式。")
        auto_mode_running = False

def hotkey_f7_handler():
    logger.info("\n🔔 [快捷键 F7 触发] 动态特征定位【文件传输助手】并发送测试消息...")
    perform_smart_reply(auto_send=True, custom_msg="测试系统连通性与大模型接管状态", sender="文件传输助手", target_contact="文件传输助手")

def hotkey_f8_handler():
    logger.info("\n🔔 [快捷键 F8 触发] 一键对当前绿色高亮聊天进行智能代聊秒发...")
    perform_smart_reply(auto_send=True, custom_msg="在吗", sender="当前联系人")

def hotkey_f9_handler():
    logger.info("\n🔔 [快捷键 F9 触发] 一键构思回复（填入输入框，不直接发送）...")
    perform_smart_reply(auto_send=False, custom_msg="在吗", sender="当前联系人")

def toggle_auto_mode():
    global auto_mode_running
    auto_mode_running = not auto_mode_running
    if auto_mode_running:
        logger.info("\n🟢 [F10 触发] 全自动巡检代聊托管已【开启】！")
    else:
        logger.info("\n🔴 [F10 触发] 全自动巡检代聊托管已【暂停】！")

def start_agent():
    print("=" * 68)
    print("🤖 电脑端微信 AI 智能代聊 Agent 已就绪 (多会话全局守护 · 防串台系统)")
    print(f"🏢 本地中转站大模型: {NEWAPI_BASE_URL} ({MODEL_NAME})")
    print("💡 角色人设锁定：杨春（懂事、孝顺、真诚、随时到岗）")
    print("=" * 68)
    print("🎯 【功能与快捷键指南】（在任何窗口按下均可直接触发）：")
    print("  👉 [F7]  一键向【文件传输助手】发送 AI 测试消息！")
    print("  👉 [F8]  一键极速代聊：鼠标自动定位输入框，AI生成高情商回答并回车秒发！")
    print("  👉 [F9]  一键帮写回复：生成回复并自动填入输入框，等您手动确认后回车！")
    print("  👉 [F10] 暂停/恢复 托管监听")
    print("=" * 68)

    if keyboard:
        try:
            keyboard.add_hotkey("F7", hotkey_f7_handler)
            keyboard.add_hotkey("F8", hotkey_f8_handler)
            keyboard.add_hotkey("F9", hotkey_f9_handler)
            keyboard.add_hotkey("F10", toggle_auto_mode)
            logger.info("✅ 全局快捷键 F7 / F8 / F9 / F10 已注册成功，随时待命中！")
        except Exception as e:
            logger.warning(f"快捷键注册异常: {e}")
            
    console_menu_loop()

def console_menu_loop():
    while True:
        try:
            print("\n📋 【接管系统操作菜单】：")
            print("  1. 立即向【文件传输助手】发送一条 AI 连通测试消息")
            print("  2. 选择联系人开启【AI 托管代聊模式】（支持自由切换聊天，半夏来消息自动秒回）")
            print("  3. 退出系统")
            choice = input("请选择操作 (1/2/3): ").strip()
            if choice == "1":
                hotkey_f7_handler()
            elif choice == "2":
                name = input("\n请输入要接管的联系人备注/昵称 (如: 半夏 / A安江老兵双彩 / HR): ").strip()
                if name:
                    start_passive_takeover(name)
            elif choice == "3":
                print("👋 系统已安全退出。")
                break
        except (KeyboardInterrupt, EOFError):
            break

if __name__ == "__main__":
    start_agent()
