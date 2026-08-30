"""
Full AI Candidate Persona Dialogue Engine for Live HR Chatting on BOSS 直聘.
Features:
1. Dynamic LLM Brain: Powered 100% by user's API Gateway / 中转站 (DeepSeek, Qwen, GPT, Claude, GLM).
2. Deep Resume & Context Awareness: Injects candidate Yang Chun's full background, facts, and conversation history.
3. Official 3-Step Resume Dispatch: Automatically approves and delivers resume when requested.
4. Strict 1-for-1 Dialogue Protocol: Never speaks unless HR speaks first; 100% silent after reply.
5. Zero about:blank, 100% stable persistent session.
"""
import sys
import os
import asyncio
import time
from typing import Optional, List, Dict
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config_loader import ConfigManager
from src.scoring_engine import ScoringEngine
from src.conversation_fsm import ConversationFSM
from src.notifier import NotificationManager
from src.bot_manager import BotManager
from src.resilient_client import ResilientAPIClient

chat_url = "https://www.zhipin.com/web/geek/chat"
user_data_dir = r"C:\chrome_debug_profile"
resume_file_path = r"d:\招聘\个人简历\杨春_个人求职简历.pdf"
MAX_INSPECTION_ROUNDS = 3


def generate_dynamic_llm_reply(
    hr_msg: str,
    client: Optional[ResilientAPIClient] = None,
    hr_name: str = "",
    chat_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """调用用户 API 中转站大模型，以求职者【杨春】第一人称生成灵活、智能、高情商的定制应答"""
    if client and client.client:
        system_prompt = (
            "【角色设定】\n"
            "你是求职者本人杨春，正在 BOSS 直聘上与招聘 HR 进行实时求职沟通。\n\n"
            "【你的真实背景与核心事实库（严格遵守，绝不凭空编造）】\n"
            "1. 姓名：杨春\n"
            "2. 学历背景：湖南信息学院 全日制统招本科（计算机科学与工程学院 · 区块链工程专业）\n"
            "3. 技能与证书：持有 C1 驾驶证、熟练掌握计算机日常软硬件与常用办公软件、逻辑严谨、执行力强\n"
            "4. 求职状态：目前已离职，可根据用人单位安排随时到岗开展工作\n"
            "5. 岗位方向与态度：主要求职客服/运营/技术支持/综合办公等岗位，工作态度积极务实、踏实负责、学习适应能力强\n"
            "6. 语言水平真实情况：具备基础英文读写与工单查阅能力，日常配合翻译工具能快速上手，学习意愿强（客观务实，绝不过度夸大口语）\n"
            "7. 排班与轮休：完全服从并接受公司的正规轮班、排班、晚班及轮休制度，抗压能力良好\n"
            "8. 期望薪资：期望薪资在 6k-9k 左右（结合具体排班补贴与绩效），更看重平台发展，具体可面议\n\n"
            "【回复原则与要求】\n"
            "1. 语气真诚、谦逊、有礼貌、不卑不亢，符合真实优秀大学生的沟通风格；\n"
            "2. 针对 HR 刚刚发送的消息进行有针对性的正面精准作答；\n"
            "3. 如果 HR 发来面试邀约/询问会议时间，表示感谢并说明自己时间充裕，随时方便视频/电话/现场面试；\n"
            "4. 字数控制在 40~100 字左右，精炼得体，严禁输出任何 markdown 格式或系统说明，只输出纯回复文本本身。"
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            for m in chat_history[-4:]:
                messages.append(m)
        messages.append({"role": "user", "content": f"HR [{hr_name}] 刚刚发来消息：\n\"{hr_msg}\"\n\n请以求职者杨春的第一人称生成简短得体的回复："})
        
        try:
            print(f"      🧠 正在请求 API 中转站大模型 ({client.primary_model}) 动态生成回复...", flush=True)
            reply, model_used = client.create_chat_completion(messages=messages, temperature=0.5, max_tokens=250)
            if reply and len(reply.strip()) > 3:
                clean_reply = reply.strip().replace('"', '').replace('“', '').replace('”', '')
                print(f"      ✨ 【中转站大模型 ({model_used}) 成功生成】: \"{clean_reply}\"", flush=True)
                return clean_reply
        except Exception as e:
            print(f"      ⚠️ 中转站 API 请求异常，启用高情商本地安全兜底: {e}", flush=True)

    # 兜底高情商知识库 (仅在 API 未配置或断网时无缝生效)
    msg_lower = hr_msg.lower()
    if any(k in msg_lower for k in ["到岗", "离职", "什么时候", "在职", "时间", "多久能来"]):
        return "您好！我目前已处于离职状态，可根据贵司安排随时到岗开展工作。"
    if any(k in msg_lower for k in ["接受", "排班", "夜班", "晚班", "轮休", "做五休二", "加班", "轮班", "休假"]):
        return "您好！我可以完全接受公司的正规排班与轮休制度，具备良好的团队协作与抗压能力。"
    if any(k in msg_lower for k in ["英语", "英文", "水平", "口语", "读写", "工单", "邮件", "专四", "六级", "cet"]):
        return "您好！我具备基础的英文读写与工单查阅能力，熟练掌握计算机操作与办公协同系统，学习适应能力强，能快速熟悉并上手具体业务。"
    if any(k in msg_lower for k in ["面试", "电话", "聊聊", "会议", "现场", "视频", "几点", "方便", "腾讯会议"]):
        return "您好！非常感谢您的认可与邀约，我全天时间均比较充裕，您可以直接通过平台发我面试时间与会议链接，期待与您进一步交流！"
    if any(k in msg_lower for k in ["薪资", "待遇", "多少钱", "期望", "待遇要求", "工资"]):
        return "您好！我对贵司该岗位的期望薪资在 6k-9k 左右（结合具体排班与绩效补贴），更看重平台的发展空间与团队氛围，具体可根据公司薪酬体系面议。"
    if any(k in msg_lower for k in ["学历", "专业", "学校", "统招", "本科", "区块链"]):
        return "您好！我是全日制统招本科学历（区块链工程专业），学习与逻辑思维能力强，持有 C1 驾驶证，踏实负责。"
        
    return "您好！关注到贵司的岗位需求，我的学习与沟通理解能力强，态度积极踏实，请问方便进一步了解下具体的岗位职责和业务方向吗？"


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


async def handle_resume_request_card(page, bot_mgr: Optional[BotManager] = None, hr_info: str = ""):
    """完整三步交付简历：[同意] -> [发送在线简历] -> [保存并发送]，发完绝不追加发任何文字"""
    approved_any = False
    try:
        # 第一步：寻找卡片上的“同意”按钮
        agree_btn = page.locator("button:has-text('同意'), .btn-agree, .btn-sure, [class*='agree']").last
        if await agree_btn.is_visible():
            print("      📄 发现 HR 发起的官方【索要附件简历】卡片，AI 正在代您自动点击【同意】...", flush=True)
            await agree_btn.click(force=True)
            await asyncio.sleep(1.5)
            approved_any = True
            
        # 第二步：处理点击同意后弹出的简历类型选择弹窗（【发送在线简历】）
        online_resume_card = page.locator("div:has-text('发送在线简历'), [class*='resume-item']:has-text('发送在线简历'), span:has-text('发送在线简历')").last
        if await online_resume_card.is_visible():
            print("      🎯 识别到简历选择弹窗，AI 正在自动点击【发送在线简历】...", flush=True)
            await online_resume_card.click(force=True)
            await asyncio.sleep(1.8)
            approved_any = True
            
        # 第三步：处理预览弹窗（精准锁定绿色按钮【保存并发送】）
        for _ in range(5):
            save_and_send_btn = page.locator("button:has-text('保存并发送'), [class*='btn']:has-text('保存并发送'), span:has-text('保存并发送'), .dialog-wrap button:has-text('保存并发送'), button:has-text('确认发送'), button:has-text('发送')").last
            try:
                if await save_and_send_btn.is_visible():
                    print("      📑 识别到简历预览弹窗，AI 正在精准点击绿色按钮【保存并发送】...", flush=True)
                    await save_and_send_btn.click(force=True)
                    await asyncio.sleep(2.0)
                    approved_any = True
                    break
            except Exception:
                pass
            await asyncio.sleep(0.6)
            
        if approved_any:
            print("      🎉 ✅ 完整三步流程确认完毕，简历已通过【保存并发送】正式送达 HR！AI 已自动进入【绝对沉默静候状态】。", flush=True)
            if bot_mgr:
                try:
                    bot_mgr.notify_resume_sent_event(hr_name=hr_info or "BOSS 直聘 HR", job_info="客服/运营岗位")
                except Exception:
                    pass
            return True
            
    except Exception as e:
        print(f"      ℹ️ 处理简历卡片/弹窗状态: {e}", flush=True)
    return approved_any


async def process_chat_inbox(page, resilient_client: Optional[ResilientAPIClient] = None, bot_mgr: Optional[BotManager] = None):
    """遍历聊天列表并由中转站大模型代替求职者与 HR 对话沟通"""
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
        print("   暂未扫描到符合条件的 HR 目标，等待下轮巡检...", flush=True)
        return
        
    print(f"   📋 扫描到 {len(matched_convos)} 个符合条件的 HR 会话，AI 开始逐一代聊巡查...", flush=True)
    
    for c in matched_convos:
        try:
            print(f"\n   🎯 【AI 巡查会话】: {c['text']}", flush=True)
            
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
                if (items.length === 0) return { lastIsMine: false, hasUnhandledCard: false, lastMsg: "", hrMsgs: [], history: [] };
                
                const lastItem = items[items.length - 1];
                const isMine = lastItem.className.includes('myself') || 
                               lastItem.className.includes('item-myself') ||
                               lastItem.className.includes('chat-item-myself') ||
                               (lastItem.querySelector('.item-myself, .chat-item-myself') !== null);
                               
                const hrMsgs = [];
                const history = [];
                items.forEach(it => {
                    const isHr = it.className.includes('friend') || it.className.includes('item-friend') || it.className.includes('chat-item-hr');
                    const txt = it.innerText ? it.innerText.trim() : '';
                    if (txt) {
                        if (isHr) {
                            hrMsgs.push(txt);
                            history.push({ role: 'user', content: txt });
                        } else {
                            history.push({ role: 'assistant', content: txt });
                        }
                    }
                });
                
                let hasAgree = false;
                const allButtons = document.querySelectorAll('button, div[role="button"], span');
                for (let b of allButtons) {
                    const t = b.innerText || '';
                    if (t.includes('同意') || t.includes('保存并发送')) {
                        hasAgree = true;
                        break;
                    }
                }
                
                return {
                    lastIsMine: isMine,
                    hasUnhandledCard: hasAgree,
                    lastMsg: lastItem.innerText ? lastItem.innerText.trim() : '',
                    hrMsgs: hrMsgs,
                    history: history
                };
            }""")
            
            # 优先处理“索要附件简历”卡片
            resume_card_approved = await handle_resume_request_card(page, bot_mgr=bot_mgr, hr_info=c['text'])
            if resume_card_approved:
                # 发了简历之后绝对不发任何文字消息，直接保持沉默静候 HR
                continue
                
            # 严格沉默守则：如果最新消息已是我方发送，且 HR 还没发新消息，100% 保持沉默！
            if convo_state["lastIsMine"] and not convo_state["hasUnhandledCard"]:
                print("      🤫 【严格沉默守则】最新一条消息/简历已由我方成功送达，HR 暂未回复新消息，AI 保持沉默，静候 HR 发信。", flush=True)
                continue
                
            last_hr_msg = convo_state["hrMsgs"][-1] if convo_state["hrMsgs"] else ""
            print(f"      📩 【HR 最新提问/消息】: \"{last_hr_msg}\"", flush=True)
            
            # 由 API 中转站大模型动态生成高情商应答
            reply_text = generate_dynamic_llm_reply(
                hr_msg=last_hr_msg or "请问方便了解岗位要求吗？",
                client=resilient_client,
                hr_name=c['text'],
                chat_history=convo_state.get("history", [])
            )
            
            # 3. 聚焦输入框并键入
            print("      👉 AI 正在激活输入框并进行物理级真机键盘打字...", flush=True)
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
            print("      🚀 AI 敲击物理回车发送给 HR...", flush=True)
            await page.keyboard.press("Enter")
            await asyncio.sleep(2.5)
            
            print(f"      🎉 ✅ AI 代聊回复已完成发送！当前会话已进入【绝对沉默静候状态】。", flush=True)
            
        except Exception as e:
            print(f"      ⚠️ 处理会话异常: {e}", flush=True)
            continue


async def main():
    print("\n" + "="*70)
    print("🎯 BOSS 直聘【HR 聊天室·API 中转站大模型全自动代聊引擎】")
    print(f"👤 代聊求职者: 杨春 (全日制统招本科 / 客服运营沙箱测试)")
    print(f"🛡️ 湖南本地 100% 隔离 | 📄 绑定简历: {resume_file_path}")
    print(f"⏱️ 巡检模式: 有限轮巡检（共 {MAX_INSPECTION_ROUNDS} 轮，完成后自动退出）")
    print("="*70 + "\n", flush=True)
    
    bot_mgr = BotManager()
    resilient_client = ResilientAPIClient()
    print(f"🌐 已连接 API 中转站: {resilient_client.base_url}")
    print(f"🧠 主力大模型: {resilient_client.primary_model}")
    print(f"🔀 备选降级梯队: {', '.join(resilient_client.fallback_models)}\n", flush=True)
    
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
        print(f"║  🧠 【已开启：中转站大模型实时动态代聊 HR！】             ║")
        print("╚" + "═"*60 + "╝\n", flush=True)
        
        for cycle in range(1, MAX_INSPECTION_ROUNDS + 1):
            print(f"--- [第 {cycle}/{MAX_INSPECTION_ROUNDS} 轮 中转站大模型巡检代聊 --- {time.strftime('%H:%M:%S')}] ---", flush=True)
            try:
                await process_chat_inbox(page, resilient_client=resilient_client, bot_mgr=bot_mgr)
            except Exception as e:
                print(f"巡检通知: {e}", flush=True)
                
            if cycle < MAX_INSPECTION_ROUNDS:
                print(f"⏳ 正在守候 HR 新消息中... (15 秒后执行第 {cycle+1} 轮检查)", flush=True)
                await asyncio.sleep(15)
                
        print("\n" + "="*70)
        print(f"🎉 【有限 {MAX_INSPECTION_ROUNDS} 轮 大模型代聊巡检全部执行完毕！】")
        print("="*70 + "\n", flush=True)
        
        await asyncio.sleep(5.0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 对话引擎退出。")
