"""
Active HR Responder:
Enters https://www.zhipin.com/web/geek/chat, finds HRs who have replied,
reads their messages, generates targeted high-EQ replies (with auto resume sending),
and sends the response immediately with screenshot proof.
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


async def main():
    print("\n" + "="*70)
    print("🤖 BOSS 直聘【HR 互动消息立即跟进与智能回复】启动")
    print(f"📄 绑定简历: {resume_file_path}")
    print("="*70 + "\n", flush=True)
    
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
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
            print("❌ 无法直连 Chrome！", flush=True)
            return

        context = browser.contexts[0]
        pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
        page = pages[0] if pages else context.pages[0]
        
        print(f"1. 🎉 成功直连当前屏幕！URL: {page.url}", flush=True)
        
        if "web/geek/chat" not in page.url:
            print("2. 正在进入消息沟通中心 (https://www.zhipin.com/web/geek/chat)...", flush=True)
            await page.goto(chat_url, wait_until="domcontentloaded")
            
        print("2. 正在等待消息中心加载完毕...", flush=True)
        for _ in range(12):
            await asyncio.sleep(1.0)
            try:
                body_txt = await page.evaluate("() => document.body ? document.body.innerText : ''")
                if "加载中" not in body_txt and len(body_txt) > 20:
                    print("   🎉 消息中心已彻底加载就绪！", flush=True)
                    break
            except Exception:
                pass
                
        # 3. 提取所有会话列表
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
        
        print(f"\n3. 📋 共发现 {len(conv_list)} 个会话记录，开始检查 HR 是否有新回复：\n", flush=True)
        
        replied_count = 0
        for c in conv_list[:8]:
            try:
                pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
                if pages:
                    page = pages[0]
                    
                item_text = c["text"]
                
                # 严格跳过湖南本地
                if any(loc in item_text for loc in ["湖南", "怀化", "洪江", "长沙", "株洲"]):
                    continue
                    
                print("─"*60)
                print(f"👉 【检查会话 {c['idx']+1}】: {item_text[:65]}")
                print("─"*60, flush=True)
                
                # 点击会话
                await page.evaluate(f"""(index) => {{
                    const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, .geek-chat-list li, ul.user-list li, [class*="user-item"]');
                    if (lis[index]) {{
                        lis[index].click();
                    }}
                }}""", c["idx"])
                
                await asyncio.sleep(2.5)
                
                pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
                if pages:
                    page = pages[0]
                
                # 提取右侧聊天记录
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
                    print("   ℹ️ 该会话暂无 HR 历史消息。", flush=True)
                    continue
                    
                last_hr_msg = ""
                for txt in reversed(messages):
                    t = txt.strip()
                    if t and not any(my_kw in t for my_kw in ["已发送", "关注到贵司正在招聘英语客服", "请问该岗位对外语", "您好，我想和您沟通下这个职位的细节"]):
                        last_hr_msg = t
                        break
                        
                if not last_hr_msg:
                    print("   ℹ️ 该会话暂无未回复的 HR 消息（最新消息为我们发出的打招呼）。", flush=True)
                    continue
                    
                print(f"   💬 【捕获到 HR 最新回复】: \"{last_hr_msg}\"", flush=True)
                
                # 自动生成针对性回复
                reply_text = generate_english_cs_reply(last_hr_msg)
                print(f"   🤖 【自动生成高情商回复】: \"{reply_text}\"", flush=True)
                
                # 如果 HR 索要简历，尝试点击发简历
                if any(k in last_hr_msg.lower() for k in ["发一份简历", "发个简历", "发下简历", "发简历", "附件简历", "看看简历", "投递", "简历发一下", "简历发我", "简历过来"]):
                    print(f"   📎 【自动触发简历派发】: {resume_file_path}", flush=True)
                    send_btn = page.locator("button:has-text('发简历'), button:has-text('发送简历'), [ka*='send_resume'], .chat-op .btn-resume").first
                    try:
                        if await send_btn.is_visible():
                            print("   👉 点击平台工具栏【发简历】...", flush=True)
                            await send_btn.click(timeout=3000)
                            await asyncio.sleep(1.5)
                            sure = page.locator(".dialog-wrap .btn-sure, button:has-text('确定'), button:has-text('发送简历')").first
                            if await sure.is_visible():
                                await sure.click(timeout=3000)
                                print("   🎉 ✅ 简历已通过平台弹窗发送！", flush=True)
                    except Exception as e:
                        print(f"   ℹ️ 简历发送提示: {e}", flush=True)
                        
                # 填入聊天输入框并回车发送
                input_box = page.locator(".chat-input, textarea, .chat-editor, [contenteditable='true'], .input-area").first
                try:
                    if await input_box.is_visible():
                        await input_box.click(timeout=3000)
                        await input_box.fill(reply_text)
                        await page.keyboard.press("Enter")
                        print("   🎉 ✅ 消息已成功打字并回车发送至 HR！", flush=True)
                        replied_count += 1
                        await asyncio.sleep(2.0)
                except Exception as e:
                    print(f"   ⚠️ 输入框交互提示: {e}", flush=True)
                    
                await page.screenshot(path=str(screenshots_dir / f"hr_conversation_{c['idx']+1}_replied.png"))
                await page.screenshot(path=str(screenshots_dir / "live_chat_replied.png"))
            except Exception as ex:
                print(f"   ⚠️ 会话检查跳过: {ex}", flush=True)
                continue
            
        print("\n" + "="*70)
        print(f"🎉 【检查完毕！共成功跟进回复了 {replied_count} 位 HR 的对话！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
