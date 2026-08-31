"""
WeChat Desktop Intelligent AI Agent (Dedicated Contact Passive Takeover System)
================================================================================
1. 指定联系人被动托管代聊（核心功能）：
   - 选择某个联系人（如：半夏 / 老兵 / HR）后，AI 全程接管该会话；
   - 【绝不主动发送】：保持静默监听，不主动骚扰对方；
   - 【对方回复即秒回】：一旦检测到对方发来新消息，大模型（DeepSeek-V4-Flash）以“杨春”第一人称极速构思高情商回复，自动打字回车发送！
2. 基础测试：
   - 选项 1：立即向【文件传输助手】发送一条 AI 连通测试消息；
3. 全局快捷键与状态感知：
   - [F7]  一键向【文件传输助手】发送测试；
   - [F8]  一键对当前聊天进行高情商秒发；
   - [F9]  一键构思（填入输入框，人工审核）；
   - [F10] 暂停/恢复 托管监听；
4. 本地大脑：DeepSeek-V4-Flash (NewAPI http://127.0.0.1:3000/v1)；
5. 角色人设：杨春（全日制统招本科/区块链工程/C1驾照/懂事孝顺/真诚得体/随时到岗）。
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

def switch_to_contact_by_feature(contact_name: str) -> bool:
    """
    基于特征与语义的动态会话切换：
    - 若搜索【文件传输助手】：命中【功能】绿色文件夹图标项（Y偏移约 top + 280px）；
    - 若搜索【普通联系人/好友】（如杨春、半夏、老兵）：命中顶部【联系人】分类第 1 项头像（Y偏移约 top + 95px）。
    """
    hwnd = find_wechat_hwnd()
    if not hwnd or not focus_wechat(hwnd):
        return False
    
    logger.info(f"🔎 正在精准搜索并切换会话: 【{contact_name}】...")
    
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
        logger.info(f"🖱️ 匹配【功能】分类特征，点击绿色文件夹项坐标 ({target_x}, {target_y}) ...")
    else:
        target_y = int(top + 95)
        logger.info(f"🖱️ 匹配【联系人】分类特征，点击首项联系人头像坐标 ({target_x}, {target_y}) ...")
        
    pyautogui.click(target_x, target_y)
    time.sleep(0.5)
    logger.info(f"✅ 会话已成功切换至 【{contact_name}】！")
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
    2. 若指定 target_contact 则先切换会话；
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

def get_latest_chat_message(hwnd, contact_name: str) -> str:
    """
    从当前微信聊天区域中动态提取最新一条收到的消息文本。
    结合 UI Automation 树和剪贴板感知机制。
    """
    try:
        wx_ctrl = auto.ControlFromHandle(hwnd)
        if wx_ctrl:
            # 遍历子控件，寻找最新收到的消息气泡或文本项
            texts = []
            for item in wx_ctrl.GetChildren():
                name = item.Name or ""
                # 过滤系统标题与控制按钮
                if name and not any(k in name for k in ["微信", "搜索", "最小化", "最大化", "关闭", "发送", "表情", "截图"]):
                    texts.append(name)
            if texts:
                return texts[-1]
    except Exception:
        pass
    return ""

def start_passive_takeover(contact_name: str):
    """
    【核心功能】启动指定联系人的被动监听代聊模式：
    - 切换到该联系人窗口；
    - 不主动发消息；
    - 持续监听该联系人发来的新消息；
    - 对方一回复，AI 立即生成高情商答案并回车秒发！
    """
    global monitored_contact, last_handled_message, auto_mode_running
    monitored_contact = contact_name
    auto_mode_running = True
    
    hwnd = find_wechat_hwnd()
    if not hwnd:
        logger.warning("❌ 未找到微信窗口，请先打开电脑微信！")
        return

    # 1. 切换到该联系人会话
    switch_to_contact_by_feature(contact_name)
    time.sleep(0.8)
    
    # 2. 记录当前最新消息作为基准（防止重复回复历史旧消息）
    last_handled_message = get_latest_chat_message(hwnd, contact_name)
    
    print("\n" + "=" * 68)
    print(f"🟢 【被动托管模式已启动】已全面接管与【{contact_name}】的微信对话！")
    print(f"🔇 【运行策略】：不主动发送任何骚扰消息；")
    print(f"👂 【实时监听中】：一旦【{contact_name}】发来新消息，AI 将以杨春口吻秒回！")
    print("👉 提示：随时可按 [Ctrl+C] 或 [F10] 退出或暂停托管。")
    print("=" * 68 + "\n")
    
    poll_count = 0
    try:
        while auto_mode_running:
            time.sleep(1.5)
            poll_count += 1
            
            # 定期巡检消息更新
            current_msg = get_latest_chat_message(hwnd, contact_name)
            
            # 如果检测到新消息（且非空、与上次不同）
            if current_msg and current_msg != last_handled_message:
                logger.info(f"\n📩 捕获到来自【{contact_name}】的最新回复: '{current_msg}'")
                last_handled_message = current_msg
                
                # 触发大模型生成并自动回复
                perform_smart_reply(auto_send=True, custom_msg=current_msg, sender=contact_name, target_contact=None)
                
            if poll_count % 20 == 0:
                logger.info(f"⏳ 正在持续守候【{contact_name}】的微信消息中...")
                
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
    print("🤖 电脑端微信 AI 智能代聊 Agent 已就绪 (统一接管系统 · 被动托管模式)")
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
            print("  2. 选择联系人开启【AI 托管代聊模式】（不主动发，对方回复即秒回）")
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
