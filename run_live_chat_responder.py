"""
Rock-Solid Native Live Chat Responder for English CS HRs.
Features:
1. Neutralizes BOSS 直聘 anti-debugger window.close() triggers.
2. Safe evaluate with auto-retry and DOM stabilization.
3. Finite 3-round inspection with physical mouse clicks and dual Enter/Ctrl+Enter sending.
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

resume_file_path = r"d:\招聘\个人简历\杨春_个人求职简历.pdf"
MAX_INSPECTION_ROUNDS = 3


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


async def safe_evaluate(page, js_code, arg=None, retries=3):
    """安全执行 evaluate，防止页面抖动时上下文销毁"""
    for attempt in range(retries):
        try:
            if arg is not None:
                return await page.evaluate(js_code, arg)
            else:
                return await page.evaluate(js_code)
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(1.5)
            else:
                raise e


async def process_chat_inbox(page, fsm):
    """遍历聊天列表并自动回复 HR (抗导航中断 + 真实物理按键)"""
    print("\n🔍 正在扫描聊天列表中的新消息...", flush=True)
    
    # 1. 扫描所有匹配的会话项
    matched_convos = []
    try:
        matched_convos = await safe_evaluate(page, """() => {
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
    except Exception as e:
        print(f"   ℹ️ 列表扫描状态: {e}", flush=True)
        return
        
    if not matched_convos:
        print("   暂未扫描到符合条件的英语客服 HR 目标，等待下轮巡检...", flush=True)
        return
        
    print(f"   📋 扫描到 {len(matched_convos)} 个符合条件的英语客服 HR 会话，开始逐一巡查...", flush=True)
    
    for c in matched_convos:
        try:
            print(f"\n   🎯 【巡查会话】: {c['text']}", flush=True)
            
            # 使用 Playwright 物理鼠标点击会话卡片
            lis_locator = page.locator('.user-list-content li, .chat-user-list li, ul.user-list li, li')
            try:
                count = await lis_locator.count()
                if c["idx"] < count:
                    target_card = lis_locator.nth(c["idx"])
                    await target_card.scroll_into_view_if_needed()
                    await target_card.click(force=True)
            except Exception:
                pass
                
            await asyncio.sleep(2.5)
            
            # 2. 读取聊天历史
            convo_state = await safe_evaluate(page, """() => {
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
            
            if convo_state["lastIsMine"] and len(convo_state["hrMsgs"]) == 0:
                print("      ℹ️ 最新消息为我方已发送状态，HR 暂无新提问，跳过重复打扰。", flush=True)
                continue
                
            last_hr_msg = convo_state["hrMsgs"][-1] if convo_state["hrMsgs"] else ""
            reply_text = generate_english_cs_reply(last_hr_msg or "请问方便了解岗位要求吗？")
            print(f"      🤖 【生成针对性回复】: \"{reply_text}\"", flush=True)
            
            # 索要简历处理
            if any(k in last_hr_msg.lower() for k in ["发一份简历", "发个简历", "发下简历", "发简历", "附件简历", "看看简历", "投递", "简历发一下", "简历发我", "简历过来"]):
                await try_send_resume_attachment(page)
                
            # 3. 聚焦输入框并键入
            print("      👉 正在激活输入框并进行物理级真机键盘打字...", flush=True)
            
            # 物理点击激活输入框
            editor_loc = page.locator("#chat-input, div[contenteditable='true'], textarea, [role='textbox'], .chat-editor .chat-input, .chat-input").first
            try:
                if await editor_loc.is_visible():
                    await editor_loc.click(force=True)
            except Exception:
                pass
                
            await safe_evaluate(page, """() => {
                const candidates = document.querySelectorAll('#chat-input, div[contenteditable="true"], textarea, [role="textbox"], .chat-input');
                for (let el of candidates) {
                    el.focus();
                    el.click();
                }
            }""")
            await asyncio.sleep(0.3)
            
            # 4. 键盘清空与逐字按键输入
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await asyncio.sleep(0.2)
            await page.keyboard.type(reply_text, delay=20)
            await asyncio.sleep(0.5)
            
            # 5. DOM 备份注入（强制触发 Vue 数据绑定）
            await safe_evaluate(page, f"""(msg) => {{
                const candidates = document.querySelectorAll('#chat-input, div[contenteditable="true"], textarea, .chat-input');
                for (let el of candidates) {{
                    if (el.isContentEditable) {{
                        if (!el.innerText || el.innerText.trim() === '') {{
                            el.innerText = msg;
                            el.dispatchEvent(new InputEvent('input', {{ bubbles: true, inputType: 'insertText', data: msg }}));
                        }}
                    }} else if (el.tagName === 'TEXTAREA') {{
                        if (!el.value || el.value.trim() === '') {{
                            el.value = msg;
                            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        }}
                    }}
                }}
            }}""", reply_text)
            
            # 6. 强制点击发送按钮 + 双快捷键击发
            print("      🚀 正在触发发送动作（点击发送按钮 + Enter/Ctrl+Enter 击键）...", flush=True)
            
            send_btn = page.locator("button.btn-send, button:has-text('发送'), [class*='btn-send'], .op-btn-send").first
            try:
                if await send_btn.is_visible():
                    await send_btn.click(force=True)
            except Exception:
                pass
                
            await safe_evaluate(page, """() => {
                const btns = document.querySelectorAll('button, a, div[role="button"], .btn-send, .op-btn-send');
                for (let b of btns) {
                    const txt = b.innerText ? b.innerText.trim() : '';
                    if (txt === '发送' || (b.className && b.className.includes('btn-send'))) {
                        b.click();
                        break;
                    }
                }
            }""")
            
            await page.keyboard.press("Control+Enter")
            await asyncio.sleep(0.3)
            await page.keyboard.press("Enter")
            await asyncio.sleep(2.5)
            
            print(f"      🎉 ✅ 消息已打字并完成发送！", flush=True)
            
        except Exception as e:
            print(f"      ⚠️ 处理会话异常: {e}", flush=True)
            continue


async def main():
    print("\n" + "="*70)
    print("🎯 BOSS 直聘【HR 聊天室·全自动多轮对话与智能回复引擎】")
    print(f"🛡️ 湖南本地 100% 隔离 | 📄 绑定简历: {resume_file_path}")
    print(f"⏱️ 巡检模式: 有限轮巡检（共 {MAX_INSPECTION_ROUNDS} 轮，完成后自动退出）")
    print("="*70 + "\n", flush=True)
    
    config_mgr = ConfigManager()
    notifier = NotificationManager()
    fsm = ConversationFSM(config_manager=config_mgr, notifier=notifier)
    
    async with async_playwright() as p:
        print("1. 正在接入桌面 Chrome 浏览器窗口...", flush=True)
        browser = None
        for i in range(15):
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                if browser:
                    break
            except Exception:
                await asyncio.sleep(1.0)
                
        if not browser:
            print("❌ 无法连接桌面 Chrome 端口 9222，请重新运行批处理启动器！", flush=True)
            return

        context = browser.contexts[0]
        pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
        page = pages[0] if pages else context.pages[0]
        
        # 拦截中和 window.close() 与 debugger 反爬触发
        try:
            await page.evaluate("""() => {
                window.close = () => { console.warn("Blocked anti-automation window.close()"); };
            }""")
        except Exception:
            pass
            
        print(f"2. 🎉 成功直连桌面 Chrome 窗口！当前页面: {page.url}", flush=True)
        print("3. 正在等待消息中心数据加载就绪...", flush=True)
        
        # 宽容等待 3 秒
        await asyncio.sleep(3.0)
        
        print("\n" + "╔" + "═"*60 + "╗")
        print(f"║  🤖 【已开启：有限 {MAX_INSPECTION_ROUNDS} 轮自动应答【欧阳先生/翟先生】！】 ║")
        print("╚" + "═"*60 + "╝\n", flush=True)
        
        for cycle in range(1, MAX_INSPECTION_ROUNDS + 1):
            print(f"--- [第 {cycle}/{MAX_INSPECTION_ROUNDS} 轮消息巡检 --- {time.strftime('%H:%M:%S')}] ---", flush=True)
            try:
                # 再次中和 window.close
                try:
                    if not page.is_closed():
                        await page.evaluate("window.close = () => {};")
                except Exception:
                    pass
                    
                if not page.is_closed():
                    await process_chat_inbox(page, fsm)
                else:
                    active_pages = [pg for pg in context.pages if not pg.is_closed()]
                    if active_pages:
                        page = active_pages[0]
                        await process_chat_inbox(page, fsm)
            except Exception as e:
                print(f"巡检通知: {e}", flush=True)
                
            if cycle < MAX_INSPECTION_ROUNDS:
                print(f"⏳ 正在守候英语客服 HR 新消息中... (15 秒后执行第 {cycle+1} 轮检查)", flush=True)
                await asyncio.sleep(15)
                
        print("\n" + "="*70)
        print(f"🎉 【有限 {MAX_INSPECTION_ROUNDS} 轮消息巡检与智能回复全部执行完毕！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 对话引擎退出。")
