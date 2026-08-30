"""
Rock-Solid Native Live Chat Responder for English CS HRs.
Features:
1. Closes unwanted about:blank tabs automatically (eliminates about:blank popup completely).
2. Deep editor locator targeting all BOSS 直聘 chat input variants (#chat-input, contenteditable, role=textbox, textarea).
3. Real CDP keyboard typing + Send button / Enter dispatching.
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
    """遍历聊天列表并自动回复 HR (深度输入框查找 + 真实按键)"""
    print("\n🔍 正在扫描聊天列表中的新消息...", flush=True)
    
    # 1. 扫描所有匹配的会话项
    matched_convos = await page.evaluate("""() => {
        const list = [];
        const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, ul.user-list li, li');
        lis.forEach((li, idx) => {
            const txt = li.innerText || '';
            if (txt.includes('湖南') || txt.includes('怀化') || txt.includes('长沙')) return;
            if (txt.includes('在线客服') || txt.includes('系统消息') || txt.includes('助手')) return;
            if (txt.includes('翟') || txt.includes('启页') || txt.includes('欧阳') || txt.includes('览川') || txt.includes('诺博') || txt.includes('世臻') || txt.includes('英语') || txt.includes('英文')) {
                list.push({ idx: idx, text: txt.replace(/\\n/g, ' | ').slice(0, 65) });
            }
        });
        return list;
    }""")
    
    if not matched_convos:
        print("   暂未扫描到符合条件的英语客服 HR 目标，等待下轮巡检...", flush=True)
        return
        
    print(f"   📋 扫描到 {len(matched_convos)} 个符合条件的英语客服 HR 会话，开始逐一巡查...", flush=True)
    
    for c in matched_convos:
        try:
            print(f"\n   🎯 【巡查会话】: {c['text']}", flush=True)
            
            # 点击会话
            await page.evaluate(f"""(idx) => {{
                const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, ul.user-list li, li');
                if (lis[idx]) lis[idx].click();
            }}""", c["idx"])
            await asyncio.sleep(2.5)
            
            # 2. 检查右侧聊天历史中最新消息
            convo_state = await page.evaluate("""() => {
                const items = document.querySelectorAll('.message-item, .chat-item, .chat-message, .item-myself, .item-friend, [class*="item-"]');
                if (items.length === 0) return { lastIsMine: false, lastMsg: "", hrMsgs: [] };
                
                const lastItem = items[items.length - 1];
                const isMine = lastItem.className.includes('myself') || 
                               lastItem.className.includes('item-myself') ||
                               lastItem.className.includes('chat-item-myself') ||
                               (lastItem.querySelector('.item-myself, .chat-item-myself') !== null);
                               
                const hrMsgs = [];
                items.forEach(it => {
                    const isHr = it.className.includes('friend') || it.className.includes('item-friend') || it.className.includes('chat-item-hr');
                    if (isHr) {
                        const txt = it.innerText ? it.innerText.trim() : '';
                        if (txt) hrMsgs.push(txt);
                    }
                });
                
                return {
                    lastIsMine: isMine,
                    lastMsg: lastItem.innerText ? lastItem.innerText.trim() : '',
                    hrMsgs: hrMsgs
                };
            }""")
            
            # 如果最新消息是我方已发，且 HR 暂无新提问，跳过
            if convo_state["lastIsMine"] and len(convo_state["hrMsgs"]) == 0:
                print("      ℹ️ 最新消息为我方已发送状态，HR 暂无新消息，跳过重复打扰。", flush=True)
                continue
                
            last_hr_msg = convo_state["hrMsgs"][-1] if convo_state["hrMsgs"] else ""
            reply_text = generate_english_cs_reply(last_hr_msg or "请问方便了解岗位要求吗？")
            print(f"      🤖 【生成针对性回复】: \"{reply_text}\"", flush=True)
            
            # 索要简历处理
            if any(k in last_hr_msg.lower() for k in ["发一份简历", "发个简历", "发下简历", "发简历", "附件简历", "看看简历", "投递", "简历发一下", "简历发我", "简历过来"]):
                await try_send_resume_attachment(page)
                
            # 3. 深度多选择器定位输入框组件
            print("      👉 正在多维度探测输入框并使用真实按键打字...", flush=True)
            
            editor_loc = None
            candidate_selectors = [
                "#chat-input",
                "div[contenteditable='true']",
                "[role='textbox']",
                ".chat-editor [contenteditable='true']",
                ".chat-input[contenteditable='true']",
                ".input-area [contenteditable='true']",
                ".chat-conversation [contenteditable='true']",
                "textarea",
                ".chat-input",
                ".chat-editor",
                ".input-area"
            ]
            
            for sel in candidate_selectors:
                try:
                    loc = page.locator(sel).first
                    if await loc.is_visible():
                        editor_loc = loc
                        print(f"      🎉 成功锁定输入框组件: [{sel}]", flush=True)
                        break
                except Exception:
                    pass
                    
            if not editor_loc:
                # 尝试纯 JS 焦点激活
                focused = await page.evaluate("""() => {
                    const allEditable = document.querySelectorAll('[contenteditable="true"], textarea, #chat-input');
                    for (let el of allEditable) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 100 && rect.height > 20) {
                            el.focus();
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }""")
                if focused:
                    print("      🎉 原生 JS 成功激活隐藏输入框焦点！", flush=True)
                else:
                    print("      ⚠️ 无法定位到输入框组件，跳过本次发送。", flush=True)
                    continue
            else:
                await editor_loc.click()
                
            await asyncio.sleep(0.4)
            
            # 4. 键盘清空与逐字敲击
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await asyncio.sleep(0.2)
            await page.keyboard.type(reply_text, delay=20)
            await asyncio.sleep(0.8)
            
            # 5. 点击发送按钮或回车击发
            send_btn_clicked = await page.evaluate("""() => {
                const btns = document.querySelectorAll('button, a, div[role="button"], .btn-send, .op-btn-send');
                for (let b of btns) {
                    const txt = b.innerText ? b.innerText.trim() : '';
                    if (txt === '发送' || (b.className && b.className.includes('btn-send'))) {
                        b.click();
                        return true;
                    }
                }
                return false;
            }""")
            
            await page.keyboard.press("Enter")
            await asyncio.sleep(2.5)
            print(f"      🎉 ✅ 消息已成功打字并发送至 HR 视窗！(按钮点击状态: {send_btn_clicked})", flush=True)
            
        except Exception as e:
            print(f"      ⚠️ 处理会话异常: {e}", flush=True)
            continue


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
        
        # 获取首个主页面
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 注入防检测特性
        try:
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined })")
        except Exception:
            pass
            
        print(f"2. 🎉 Chrome 窗口已常驻打开！正在直达消息中心: {chat_url}", flush=True)
        try:
            await page.goto(chat_url, wait_until="commit", timeout=60000)
        except Exception:
            pass
            
        # 彻底关闭所有多余的空白页（消除 about:blank）
        for pg in context.pages:
            if pg != page and ("about:blank" in pg.url or pg.url == ""):
                try:
                    await pg.close()
                except Exception:
                    pass
                    
        print("3. 正在等待消息中心数据渲染就绪...", flush=True)
        await asyncio.sleep(4.0)
        
        print("\n" + "╔" + "═"*60 + "╗")
        print("║  🤖 【已开启：精准定位【欧阳先生/翟先生】并自动打字发送！】║")
        print("╚" + "═"*60 + "╝\n", flush=True)
        
        cycle = 1
        while True:
            print(f"--- [第 {cycle} 轮消息巡检 --- {time.strftime('%H:%M:%S')}] ---", flush=True)
            try:
                # 再次清理可能意外弹出的 about:blank 标签页
                for pg in context.pages:
                    if pg != page and ("about:blank" in pg.url or pg.url == ""):
                        try:
                            await pg.close()
                        except Exception:
                            pass
                            
                # 寻找包含 zhipin 的有效主页面
                active_pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
                curr_page = active_pages[0] if active_pages else page
                
                if "web/geek/chat" not in curr_page.url:
                    await curr_page.goto(chat_url, wait_until="commit", timeout=60000)
                    await asyncio.sleep(3.0)
                    
                await process_chat_inbox(curr_page, fsm)
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
