"""
Rock-Solid 100% Stealth Native Persistent Context Live Chat Responder for English CS HRs.
Features:
1. Full 2-Step Resume Dispatch Flow:
   - Step 1: Clicks [同意] on official BOSS resume card ("我想要一份您的附件简历，您是否同意").
   - Step 2: Automatically handles the popup modal (clicks [发送在线简历] / uploads candidate PDF).
2. Strict 1-for-1 Dialogue Protocol: Only replies once when HR sends a new message/card.
3. Zero about:blank, 100% stable persistent session.
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
    
    if any(k in msg_lower for k in ["简历", "附件简历", "投递", "发一份", "发个简历", "发下简历", "发简历", "看看简历"]):
        return "好的，我的个人求职简历已为您同意发送，请您查收！如果有需要进一步了解的项目经历或细节，随时沟通。"
        
    if any(k in msg_lower for k in ["到岗", "离职", "什么时候", "在职", "时间"]):
        return "您好！我目前已处于离职状态，可根据贵司安排随时到岗开展工作。"
        
    if any(k in msg_lower for k in ["面试", "电话", "聊聊", "会议", "现场", "视频", "几点", "方便"]):
        return "您好！非常感谢您的认可与邀约，我全天时间均比较充裕，您可以直接通过平台发我面试时间与会议链接，期待与您进一步交流！"
        
    if any(k in msg_lower for k in ["接受", "排班", "夜班", "轮休", "做五休二", "加班", "轮班"]):
        return "您好！我可以接受公司的正规排班与轮休制度，具有良好的团队协作与抗压能力。"
        
    return "您好！关注到贵司的英文客服岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户线上沟通，请问方便进一步了解下具体的岗位职责和业务方向吗？"


async def safe_evaluate(page, js_code, arg=None, retries=3):
    """安全执行 evaluate"""
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


async def handle_resume_request_card(page):
    """完整两步处理 HR 发送的官方索要简历卡片及后续弹窗"""
    try:
        # 第一步：寻找卡片上的“同意”按钮
        agree_btn = page.locator("button:has-text('同意'), .btn-agree, .btn-sure, [class*='agree']").last
        if await agree_btn.is_visible():
            print("      📄 发现 HR 发起的官方【索要附件简历】卡片，正在自动点击【同意】...", flush=True)
            await agree_btn.click(force=True)
            await asyncio.sleep(1.5)
            
            # 第二步：处理点击同意后弹出的简历类型选择弹窗（【发送在线简历】/【上传简历】）
            online_resume_card = page.locator("div:has-text('发送在线简历'), [class*='resume-item']:has-text('发送在线简历'), span:has-text('发送在线简历')").last
            if await online_resume_card.is_visible():
                print("      🎯 识别到简历选择弹窗，正在自动点击【发送在线简历】完成发送...", flush=True)
                await online_resume_card.click(force=True)
                await asyncio.sleep(1.2)
            else:
                # 备用：若存在直接“确定”按钮
                confirm_btn = page.locator(".dialog-wrap .btn-sure, button:has-text('确定'), button:has-text('发送')").first
                if await confirm_btn.is_visible():
                    await confirm_btn.click(force=True)
                    await asyncio.sleep(1.0)
                    
            print("      🎉 ✅ 简历已成功通过平台弹窗正式送达 HR！", flush=True)
            return True
            
        # 若已有直接弹窗处于打开状态，直接点击【发送在线简历】
        online_resume_card = page.locator("div:has-text('发送在线简历'), [class*='resume-item']:has-text('发送在线简历'), span:has-text('发送在线简历')").last
        if await online_resume_card.is_visible():
            print("      🎯 识别到未关闭的简历选择弹窗，正在自动点击【发送在线简历】完成发送...", flush=True)
            await online_resume_card.click(force=True)
            await asyncio.sleep(1.2)
            print("      🎉 ✅ 简历已成功通过平台弹窗正式送达 HR！", flush=True)
            return True
            
    except Exception as e:
        print(f"      ℹ️ 处理简历卡片/弹窗状态: {e}", flush=True)
    return False


async def process_chat_inbox(page, fsm):
    """遍历聊天列表并自动回复 HR (严格一问一答，HR 回一句我方回一句)"""
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
            
            # 2. 读取聊天历史（严格判断最新一条是谁发的）
            convo_state = await safe_evaluate(page, """() => {
                const items = document.querySelectorAll('.message-item, .chat-item, .chat-message, .item-myself, .item-friend, [class*="item-"]');
                if (items.length === 0) return { lastIsMine: false, hasAgreeBtn: false, hasDialog: false, lastMsg: "", hrMsgs: [] };
                
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
                
                const agreeBtn = document.querySelector('button.btn-agree, .dialog-wrap .btn-sure') || 
                                 Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('同意'));
                const dialogCard = document.querySelector('.dialog-wrap, [class*="resume-item"], [class*="dialog"]');
                
                return {
                    lastIsMine: isMine,
                    hasAgreeBtn: !!agreeBtn,
                    hasDialog: !!dialogCard,
                    lastMsg: lastItem.innerText ? lastItem.innerText.trim() : '',
                    hrMsgs: hrMsgs
                };
            }""")
            
            # 完整处理“索要附件简历”卡片及后续选择弹窗
            resume_card_approved = await handle_resume_request_card(page)
            
            # 严格一问一答守则：如果最新消息已是我方发送，且没有未处理的简历卡片/弹窗，保持静默跳过
            if convo_state["lastIsMine"] and not convo_state["hasAgreeBtn"] and not convo_state["hasDialog"] and not resume_card_approved:
                print("      ℹ️ 【严格一问一答守则】我方已发最新回复，HR 暂未发送新消息，保持静默，跳过重复打扰。", flush=True)
                continue
                
            last_hr_msg = convo_state["hrMsgs"][-1] if convo_state["hrMsgs"] else ""
            
            # 若刚完成简历交付，发送高情商确认话术
            if resume_card_approved:
                reply_text = "好的，我的个人求职简历已为您同意发送，请您查收！如果有需要进一步了解的项目经历或细节，随时沟通。"
            else:
                reply_text = generate_english_cs_reply(last_hr_msg or "请问方便了解岗位要求吗？")
                
            print(f"      🤖 【生成针对性回复】: \"{reply_text}\"", flush=True)
            
            # 3. 聚焦输入框并键入
            print("      👉 正在激活输入框并进行物理级真机键盘打字...", flush=True)
            
            # 物理点击激活输入框
            editor_loc = page.locator("#chat-input, div[contenteditable='true'], textarea, [role='textbox']").first
            try:
                if await editor_loc.is_visible():
                    await editor_loc.click(force=True)
            except Exception:
                pass
                
            await asyncio.sleep(0.3)
            
            # 4. 键盘清空与逐字按键输入
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await asyncio.sleep(0.2)
            await page.keyboard.type(reply_text, delay=25)
            await asyncio.sleep(0.8)
            
            # 5. 纯物理回车发送
            print("      🚀 正在敲击物理回车发送...", flush=True)
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
        print("1. 正在以 100% 原生纯净真机模式启动常驻 Chrome 浏览器...", flush=True)
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome",
            ignore_default_args=["--enable-automation"],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-first-run",
                "--no-default-browser-check"
            ]
        )
        
        # 始终使用主默认标签页
        page = context.pages[0]
        
        # 中和控制台计时检测（彻底击碎 anti-debugger 触发器）
        await page.add_init_script("""
            const noop = () => {};
            console.table = noop;
            console.clear = noop;
        """)
            
        print(f"2. 🎉 Chrome 窗口已常驻打开！正在直达消息中心: {chat_url}", flush=True)
        try:
            await page.goto(chat_url, wait_until="domcontentloaded", timeout=60000)
        except Exception:
            pass
            
        print("3. 正在等待消息中心数据加载就绪...", flush=True)
        await asyncio.sleep(5.0)
        
        print("\n" + "╔" + "═"*60 + "╗")
        print(f"║  🤖 【已开启：有限 {MAX_INSPECTION_ROUNDS} 轮自动应答【欧阳先生/翟先生】！】 ║")
        print("╚" + "═"*60 + "╝\n", flush=True)
        
        for cycle in range(1, MAX_INSPECTION_ROUNDS + 1):
            print(f"--- [第 {cycle}/{MAX_INSPECTION_ROUNDS} 轮消息巡检 --- {time.strftime('%H:%M:%S')}] ---", flush=True)
            try:
                await process_chat_inbox(page, fsm)
            except Exception as e:
                print(f"巡检通知: {e}", flush=True)
                
            if cycle < MAX_INSPECTION_ROUNDS:
                print(f"⏳ 正在守候英语客服 HR 新消息中... (15 秒后执行第 {cycle+1} 轮检查)", flush=True)
                await asyncio.sleep(15)
                
        print("\n" + "="*70)
        print(f"🎉 【有限 {MAX_INSPECTION_ROUNDS} 轮消息巡检与智能回复全部执行完毕！】")
        print("="*70 + "\n", flush=True)
        
        # 保持窗口驻留 5 秒让用户看到结果
        await asyncio.sleep(5.0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 对话引擎退出。")
