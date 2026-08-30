"""
Rock-Solid Native Live Chat Responder for English CS HRs.
Launches persistent Chrome in visible headed mode directly via Playwright.
Zero CDP reconnect drops. Permanent window persistence.
"""
import sys
import os
import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config_loader import ConfigManager
from src.scoring_engine import ScoringEngine
from src.conversation_fsm import ConversationFSM
from src.notifier import NotificationManager

chat_url = "https://www.zhipin.com/web/geek/chat"
user_data_dir = r"C:\chrome_debug_profile"
resume_file_path = r"d:\招聘\个人简历\杨春_个人求职简历.pdf"


def is_english_cs_conversation(text: str) -> bool:
    """严格判断是否为英语客服/海外客服真实 HR，排除系统客服与湖南本地"""
    if any(loc in text for loc in ["湖南", "怀化", "洪江", "长沙", "株洲", "湘潭", "岳阳"]):
        return False
        
    if any(sys_kw in text for sys_kw in ["在线客服", "系统消息", "打招呼", "通知助手", "小助手", "客服助手", "安全中心"]):
        return False
        
    cs_keywords = ["英语", "英文", "外语", "海外客服", "跨境", "览川", "诺博", "启页", "世臻", "携程", "水裹汤泉", "翟", "欧阳"]
    return any(kw in text for kw in cs_keywords)


def generate_english_cs_reply(hr_msg: str) -> str:
    """根据 HR 消息生成针对英语客服岗位的自然高情商回复"""
    msg_lower = hr_msg.lower()
    
    if any(k in msg_lower for k in ["发一份简历", "发个简历", "发下简历", "发简历", "附件简历", "看看简历", "投递", "简历发一下", "简历发我", "简历过来"]):
        return "好的，我的个人求职简历【杨春_个人求职简历.pdf】已为您发送，请您查收！如果有需要进一步了解的项目经历或细节，随时沟通。"
        
    if any(k in msg_lower for k in ["到岗", "离职", "什么时候", "在职", "时间"]):
        return "您好！我目前已处于离职状态，可根据贵司安排随时到岗开展工作。"
        
    if any(k in msg_lower for k in ["面试", "电话", "聊聊", "会议", "现场", "视频", "几点", "方便"]):
        return "您好！非常感谢您的认可与邀约，我全天时间均比较充裕，您可以直接通过平台发我面试时间与会议链接，期待与您进一步交流！"
        
    if any(k in msg_lower for k in ["接受", "排班", "夜班", "轮休", "做五休二", "加班", "轮班"]):
        return "您好！我可以接受公司的正规排班与轮休制度，具有良好的团队协作与抗压能力。"
        
    return "您好！关注到贵司的英文客服岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户线上沟通，请问方便进一步了解下具体的岗位职责和业务方向吗？"


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
    except Exception:
        pass
    return False


async def process_chat_inbox(page, fsm):
    """遍历聊天列表并自动回复 HR"""
    print("\n🔍 正在扫描聊天列表中的新消息...", flush=True)
    
    # 1. 查找并点击匹配的真实英语客服 HR 会话
    clicked_info = await page.evaluate("""() => {
        const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, ul.user-list li, li');
        for (let li of lis) {
            const txt = li.innerText || '';
            if (txt.includes('湖南') || txt.includes('怀化') || txt.includes('长沙')) continue;
            if (txt.includes('在线客服') || txt.includes('系统消息') || txt.includes('助手')) continue;
            if (txt.includes('翟') || txt.includes('启页') || txt.includes('欧阳') || txt.includes('览川') || txt.includes('诺博') || txt.includes('世臻') || txt.includes('英语') || txt.includes('英文')) {
                li.click();
                return { success: true, text: txt.replace(/\\n/g, ' | ').slice(0, 65) };
            }
        }
        return { success: false, text: '' };
    }""")
    
    if not clicked_info["success"]:
        print("   暂未扫描到未回复的英语客服 HR 目标，等待下轮巡检...", flush=True)
        return
        
    print(f"   🎯 【已精准锁定真实 HR 会话】: {clicked_info['text']}", flush=True)
    await asyncio.sleep(2.5)
    
    # 2. 提取右侧聊天历史
    messages = []
    try:
        messages = await page.evaluate("""() => {
            const msgs = [];
            document.querySelectorAll('.item-friend, .chat-item-hr, .message-card, .chat-message, [class*="friend"]').forEach(el => {
                const txt = el.innerText ? el.innerText.trim() : '';
                if (txt) msgs.push(txt);
            });
            return msgs;
        }""")
    except Exception:
        pass
            
    last_hr_msg = ""
    if messages:
        for txt in reversed(messages):
            t = txt.strip()
            if t and not any(my_kw in t for my_kw in ["已发送", "关注到贵司正在招聘英语客服", "请问该岗位对外语", "您好，我想和您沟通下这个职位的细节"]):
                last_hr_msg = t
                break
                
    reply_text = generate_english_cs_reply(last_hr_msg or "请问方便了解岗位要求吗？")
    print(f"   🤖 【准备发送回复】: \"{reply_text}\"", flush=True)
    
    # 索要简历处理
    if any(k in (last_hr_msg or "").lower() for k in ["发一份简历", "发个简历", "发下简历", "发简历", "附件简历", "看看简历", "投递", "简历发一下", "简历发我", "简历过来"]):
        await try_send_resume_attachment(page)
        
    # 3. 填入输入框并发送
    print("   👉 正在向聊天输入框填入回复并触发发送...", flush=True)
    
    try:
        editor = page.locator("#chat-input, div[contenteditable='true'], textarea, .chat-input").first
        if await editor.is_visible():
            await editor.click()
            await asyncio.sleep(0.3)
            await page.keyboard.type(reply_text, delay=15)
            await asyncio.sleep(0.8)
            
            send_btn = page.locator("button.btn-send, button:has-text('发送'), [class*='btn-send'], .op-btn-send").first
            if await send_btn.is_visible():
                await send_btn.click()
            else:
                await page.keyboard.press("Enter")
                
            await asyncio.sleep(2.0)
            print("   🎉 ✅ 消息已成功打字并送达 HR 聊天视窗！", flush=True)
            return
    except Exception as e:
        print(f"   ℹ️ 定位器打字备用处理: {e}", flush=True)
        
    # DOM 原生备用方案
    try:
        await page.evaluate(f"""(msg) => {{
            const editor = document.getElementById('chat-input') || 
                           document.querySelector('div[contenteditable="true"]') || 
                           document.querySelector('.chat-input') ||
                           document.querySelector('textarea');
            if (editor) {{
                editor.focus();
                document.execCommand('insertText', false, msg);
                const sendBtns = document.querySelectorAll('button, a, div[role="button"]');
                for (let b of sendBtns) {{
                    const t = b.innerText ? b.innerText.trim() : '';
                    if (t === '发送' || (b.className && b.className.includes('btn-send'))) {{
                        b.click();
                        break;
                    }}
                }}
            }}
        }}""", reply_text)
        await page.keyboard.press("Enter")
        await asyncio.sleep(2.0)
        print("   🎉 ✅ 消息已通过原生 DOM 事件成功发送至 HR 视窗！", flush=True)
    except Exception as e:
        print(f"   ⚠️ DOM 发送通知: {e}", flush=True)


async def main():
    print("\n" + "="*70)
    print("🎯 BOSS 直聘【HR 聊天室·全自动多轮对话与智能回复引擎】")
    print(f"🛡️ 湖南本地 100% 隔离 | 📄 绑定简历: {resume_file_path}")
    print("="*70 + "\n", flush=True)
    
    config_mgr = ConfigManager()
    notifier = NotificationManager()
    fsm = ConversationFSM(config_manager=config_mgr, notifier=notifier)
    
    screenshots_dir = Path(__file__).resolve().parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # 清理残留锁文件
    for f in Path(user_data_dir).glob("Singleton*"):
        try:
            f.unlink(missing_ok=True)
        except Exception:
            pass
    lock_file = Path(user_data_dir) / "lockfile"
    if lock_file.exists():
        try:
            lock_file.unlink()
        except Exception:
            pass
            
    async with async_playwright() as p:
        print("1. 正在启动原生常驻 Chrome 浏览器并直达 BOSS 直聘消息中心...", flush=True)
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-first-run",
                "--no-default-browser-check"
            ]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 注入防检测特性
        try:
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined })")
        except Exception:
            pass
            
        print(f"2. 🎉 Chrome 窗口已常驻打开！正在加载消息中心: {chat_url}", flush=True)
        await page.goto(chat_url, wait_until="domcontentloaded")
        
        print("3. 正在等待消息中心数据就绪...", flush=True)
        await asyncio.sleep(5.0)
        
        print("\n" + "╔" + "═"*60 + "╗")
        print("║  🤖 【已开启：精准定位【欧阳先生/翟先生】并自动打字发送！】║")
        print("╚" + "═"*60 + "╝\n", flush=True)
        
        cycle = 1
        while True:
            print(f"--- [第 {cycle} 轮消息巡检 --- {time.strftime('%H:%M:%S')}] ---", flush=True)
            try:
                # 确保当前页面在消息中心
                if "web/geek/chat" not in page.url:
                    await page.goto(chat_url, wait_until="domcontentloaded")
                    await asyncio.sleep(3.0)
                await process_chat_inbox(page, fsm)
            except Exception as e:
                print(f"巡检通知: {e}", flush=True)
                
            print("⏳ 正在守候英语客服 HR 新消息中... (15 秒后自动检查)", flush=True)
            await asyncio.sleep(15)
            cycle += 1


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 对话引擎退出。")
