"""
Dedicated Multi-Turn Live Chat Responder for English CS HRs.
Features:
1. Pure JS evaluation & click interaction (100% resilient, no stale element exceptions).
2. Auto-waits for IM WebSocket and conversation list hydration.
3. Detects new messages from English CS HRs.
4. Automatically responds with intelligent multi-turn dialogue.
5. Auto-dispatches resume file: 'd:\\招聘\\个人简历\\杨春_个人求职简历.pdf' when requested by HR!
"""
import sys
import os
import subprocess
import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config_loader import ConfigManager
from src.scoring_engine import ScoringEngine
from src.schemas import RawJobCard
from src.battle_logger import log_event
from src.conversation_fsm import ConversationFSM
from src.notifier import NotificationManager

chat_url = "https://www.zhipin.com/web/geek/chat"
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data_dir = r"C:\chrome_debug_profile"
resume_file_path = r"d:\招聘\个人简历\杨春_个人求职简历.pdf"


def generate_english_cs_reply(hr_msg: str) -> str:
    """根据 HR 消息生成针对英语客服岗位的自然高情商回复"""
    msg_lower = hr_msg.lower()
    
    if any(k in msg_lower for k in ["英语", "外语", "口语", "四级", "六级", "专八", "熟练", "水平", "流畅", "沟通能力"]):
        return "您好！我的英语具备良好的听说读写能力，能够熟练使用英文进行邮件往来、工单处理及日常客户线上沟通，日常业务沟通无障碍。请问贵司该岗位主要对接哪些区域的客户呢？"
        
    if any(k in msg_lower for k in ["发一份简历", "发个简历", "发下简历", "发简历", "附件简历", "看看简历", "投递", "简历发一下", "简历发我", "简历过来"]):
        return "好的，我的个人求职简历【杨春_个人求职简历.pdf】已为您发送，请您查收！如果有需要进一步了解的项目经历或细节，随时沟通。"
        
    if any(k in msg_lower for k in ["到岗", "离职", "什么时候", "在职", "时间"]):
        return "您好！我目前已处于离职状态，可根据贵司安排随时到岗开展工作。"
        
    if any(k in msg_lower for k in ["面试", "电话", "聊聊", "会议", "现场", "视频", "几点", "方便"]):
        return "您好！非常感谢您的认可与邀约，我全天时间均比较充裕，您可以直接通过平台发我面试时间与会议链接，期待与您进一步交流！"
        
    if any(k in msg_lower for k in ["接受", "排班", "夜班", "轮休", "做五休二", "加班", "轮班"]):
        return "您好！我可以接受公司的正规排班与轮休制度，具有良好的团队协作与抗压能力。"
        
    return "您好！感谢您的回复，我对贵司的英语客服岗位非常感兴趣，请问方便进一步了解下具体的岗位职责和业务方向吗？"


async def try_send_resume_attachment(page):
    """尝试通过聊天工具栏发送附件简历"""
    if not os.path.exists(resume_file_path):
        return False
        
    try:
        send_resume_btn = page.locator("button:has-text('发简历'), button:has-text('发送简历'), [ka*='send_resume'], .chat-op .btn-resume").first
        if await send_resume_btn.is_visible():
            print("      📎 正在自动点击工具栏【发送附件简历】按钮...", flush=True)
            await send_resume_btn.click(timeout=3000)
            await asyncio.sleep(1.5)
            sure_btn = page.locator(".dialog-wrap .btn-sure, button:has-text('确定'), button:has-text('发送简历')").first
            if await sure_btn.is_visible():
                await sure_btn.click(timeout=3000)
                print("      🎉 ✅ 附件简历已通过平台一键成功送达！", flush=True)
                await asyncio.sleep(1.5)
                return True
                
        file_input = page.locator("input[type='file']").first
        if await file_input.is_visible():
            print(f"      📎 正在上传简历文件: {resume_file_path} ...", flush=True)
            await file_input.set_input_files(resume_file_path)
            await asyncio.sleep(2.0)
            print("      🎉 ✅ 简历文件已成功上传至聊天窗口！", flush=True)
            return True
    except Exception as e:
        pass
    return False


async def process_chat_inbox(page, fsm):
    """遍历聊天列表并自动回复 HR (基于 JS 内存数据与原生点击，绝对不产生过期异常)"""
    print("\n🔍 正在扫描聊天列表中的新消息...", flush=True)
    
    # 1. 一次性获取所有会话列表
    conv_list = await page.evaluate("""() => {
        const list = [];
        const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, .geek-chat-list li, ul.user-list li, [class*="user-item"]');
        lis.forEach((li, idx) => {
            const text = li.innerText ? li.innerText.replace(/\\n/g, ' | ').trim() : '';
            if (text.length > 3) {
                list.push({ idx: idx, text: text });
            }
        });
        return list;
    }""")
    
    if not conv_list:
        print("   暂未读取到左侧会话列表，正在等待渲染...", flush=True)
        return
        
    print(f"   📋 发现 {len(conv_list)} 个历史对话记录，开始检查 HR 互动...", flush=True)
    
    for c in conv_list[:8]:
        try:
            item_text = c["text"]
            
            # 严格跳过湖南本地
            if any(loc in item_text for loc in ["湖南", "怀化", "洪江", "长沙", "株洲"]):
                continue
                
            print(f"\n   👉 [会话 {c['idx']+1}] {item_text[:70]}", flush=True)
            
            # JS 原生触发点击，绝对不超时、不抛异常
            await page.evaluate(f"""(index) => {{
                const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, .geek-chat-list li, ul.user-list li, [class*="user-item"]');
                if (lis[index]) {{
                    lis[index].click();
                }}
            }}""", c["idx"])
            
            await asyncio.sleep(2.0)
            
            # 读取右侧聊天消息
            messages = await page.evaluate("""() => {
                const msgs = [];
                document.querySelectorAll('.item-friend, .chat-item-hr, .message-card, .chat-message, [class*="friend"]').forEach(el => {
                    const txt = el.innerText ? el.innerText.trim() : '';
                    if (txt) {
                        msgs.push(txt);
                    }
                });
                return msgs;
            }""")
            
            if not messages:
                print("      ℹ️ 该会话暂无 HR 历史回复。", flush=True)
                continue
                
            last_hr_msg = ""
            for txt in reversed(messages):
                t = txt.strip()
                if t and not any(my_kw in t for my_kw in ["已发送", "关注到贵司正在招聘英语客服", "请问该岗位对外语"]):
                    last_hr_msg = t
                    break
                    
            if not last_hr_msg:
                print("      ℹ️ 该会话暂无未回复的 HR 消息。", flush=True)
                continue
                
            print(f"      💬 【捕获到 HR 最新回复】: \"{last_hr_msg}\"", flush=True)
            
            # 检查高危涉诈词汇
            is_risky, risk_reason = fsm.check_high_risk_hr_message(last_hr_msg)
            if is_risky:
                print(f"      🚨 【触发高危风控防火墙拦截】: {risk_reason}，已自动停止回复该会话！", flush=True)
                continue
                
            # 索要简历处理
            if any(k in last_hr_msg.lower() for k in ["发一份简历", "发个简历", "发下简历", "发简历", "附件简历", "看看简历", "投递", "简历发一下", "简历发我", "简历过来"]):
                await try_send_resume_attachment(page)
                
            reply_text = generate_english_cs_reply(last_hr_msg)
            print(f"      🤖 【生成智能应答】: \"{reply_text}\"", flush=True)
            
            # 填入聊天输入框并回车发送
            input_box = page.locator(".chat-input, textarea, .chat-editor, [contenteditable='true'], .input-area").first
            if await input_box.is_visible():
                await input_box.click(timeout=3000)
                await input_box.fill(reply_text)
                await page.keyboard.press("Enter")
                print("      🎉 ✅ 消息已成功发送至 HR！", flush=True)
                log_event("HR_CHAT_REPLY_SENT", f"成功回复 HR: {reply_text[:30]}")
                await asyncio.sleep(2.0)
                
                try:
                    await page.screenshot(path="tests/test_screenshots/live_chat_replied.png")
                    await page.screenshot(path="tests/test_screenshots/live_chat_verified.png")
                except Exception:
                    pass
        except Exception as e:
            print(f"      ⚠️ 处理会话异常: {e}", flush=True)
            continue


async def main():
    print("\n" + "="*70)
    print("🎯 BOSS 直聘【HR 聊天室·实时双向多轮智能对话引擎】启动")
    print(f"📄 绑定简历: {resume_file_path}")
    print("="*70 + "\n", flush=True)
    
    config_mgr = ConfigManager()
    notifier = NotificationManager()
    fsm = ConversationFSM(config_manager=config_mgr, notifier=notifier)
    
    async with async_playwright() as p:
        browser = None
        for _ in range(3):
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                break
            except Exception:
                await asyncio.sleep(1.0)
                
        if not browser:
            print("1. 正在启动 Chrome 浏览器并进入消息聊天室...", flush=True)
            subprocess.Popen([
                chrome_path,
                "--remote-debugging-port=9222",
                f"--user-data-dir={user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                chat_url
            ])
            for _ in range(12):
                await asyncio.sleep(1.0)
                try:
                    browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                    break
                except Exception:
                    pass

        if not browser:
            print("❌ 无法直连 Chrome，请双击 start_auto_chat_responder.bat 后重试！", flush=True)
            return

        context = browser.contexts[0]
        pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
        page = pages[0] if pages else context.pages[0]
            
        print(f"1. 🎉 成功直连桌面 Chrome 窗口！当前 URL: {page.url}", flush=True)
        
        # 进入聊天消息中心
        if "web/geek/chat" not in page.url:
            print("2. 正在进入 BOSS 直聘消息沟通中心 (https://www.zhipin.com/web/geek/chat)...", flush=True)
            try:
                await page.goto(chat_url, wait_until="domcontentloaded", timeout=25000)
            except Exception:
                pass
        
        print("2. 正在等待消息中心数据加载就绪...", flush=True)
        for _ in range(12):
            await asyncio.sleep(1.0)
            try:
                body_txt = await page.evaluate("() => document.body ? document.body.innerText : ''")
                if "加载中" not in body_txt and len(body_txt) > 20:
                    print("   🎉 消息中心已彻底加载就绪！", flush=True)
                    break
            except Exception:
                pass
        
        print("\n" + "╔" + "═"*60 + "╗")
        print("║  🤖 【已开启 HR 消息常驻实时监听，有问必答，自动发简历！】║")
        print("╚" + "═"*60 + "╝\n", flush=True)
        
        cycle = 1
        while True:
            print(f"--- [第 {cycle} 轮消息巡检 --- {time.strftime('%H:%M:%S')}] ---", flush=True)
            try:
                pages = [pg for pg in context.pages if not pg.is_closed()]
                if pages:
                    page = pages[0]
                    await process_chat_inbox(page, fsm)
            except Exception as e:
                print(f"巡检通知: {e}", flush=True)
                
            print("⏳ 正在守候 HR 新消息中... (15 秒后自动检查)", flush=True)
            await asyncio.sleep(15)
            cycle += 1


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 对话引擎退出。")
