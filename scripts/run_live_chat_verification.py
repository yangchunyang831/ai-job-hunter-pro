"""
Direct Live Chat Verification Script.
Connects to Chrome, visits /web/geek/chat, iterates through all conversations,
inspects HR messages, generates replies, types into the chat box, and captures full visual screenshots.
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
    msg_lower = hr_msg.lower()
    if any(k in msg_lower for k in ["英语", "外语", "口语", "四级", "六级", "专八", "熟练", "水平", "流畅"]):
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
    print("🚀 BOSS 直聘【HR 聊天室·端到端真机联调验证】启动")
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
        
        print(f"1. 🎉 成功直连桌面 Chrome 窗口！当前 URL: {page.url}", flush=True)
        
        # 导航到 chat 页面
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
                
        await page.screenshot(path=str(screenshots_dir / "chat_inbox_loaded.png"))
        print("   📸 消息中心总览截图已保存至 tests/test_screenshots/chat_inbox_loaded.png", flush=True)
        
        # 3. 提取会话列表
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
        
        print(f"\n3. 📋 共发现 {len(conv_list)} 个会话记录，开始依次遍历验证：\n", flush=True)
        
        for c in conv_list[:5]:
            item_text = c["text"]
            
            # 严格跳过湖南本地
            if any(loc in item_text for loc in ["湖南", "怀化", "洪江", "长沙", "株洲"]):
                print(f"   🛡️ 隔离湖南本地会话: {item_text[:40]}", flush=True)
                continue
                
            print("─"*60)
            print(f"👉 【会话 {c['idx']+1}】: {item_text[:65]}")
            print("─"*60, flush=True)
            
            # 原生 JS 点击该会话
            await page.evaluate(f"""(index) => {{
                const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, .geek-chat-list li, ul.user-list li, [class*="user-item"]');
                if (lis[index]) {{
                    lis[index].click();
                }}
            }}""", c["idx"])
            
            await asyncio.sleep(2.5)
            
            # 截取该会话窗口
            await page.screenshot(path=str(screenshots_dir / f"chat_convo_{c['idx']+1}.png"))
            
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
            
            print(f"   HR 消息数: {len(messages)} 条", flush=True)
            if not messages:
                print("   ℹ️ 该会话暂无 HR 历史消息（尚未发起回复）。", flush=True)
                continue
                
            last_hr_msg = ""
            for txt in reversed(messages):
                t = txt.strip()
                if t and not any(my_kw in t for my_kw in ["已发送", "关注到贵司正在招聘英语客服", "请问该岗位对外语"]):
                    last_hr_msg = t
                    break
                    
            if not last_hr_msg:
                print("   ℹ️ HR 暂无新回复（上条消息为我们发出的打招呼）。", flush=True)
                continue
                
            print(f"   💬 【捕获到 HR 最新消息】: \"{last_hr_msg}\"", flush=True)
            
            # 自动生成应答
            reply_text = generate_english_cs_reply(last_hr_msg)
            print(f"   🤖 【自动生成智能回复】: \"{reply_text}\"", flush=True)
            
            # 如果 HR 索要简历，尝试点击发简历
            if any(k in last_hr_msg.lower() for k in ["发一份简历", "发个简历", "发下简历", "发简历", "附件简历", "看看简历", "投递", "简历发一下", "简历发我", "简历过来"]):
                print(f"   📎 【触发专属简历派送】: {resume_file_path}", flush=True)
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
                    print(f"   ℹ️ 简历按钮提示: {e}", flush=True)
                    
            # 填入聊天输入框并回车发送
            input_box = page.locator(".chat-input, textarea, .chat-editor, [contenteditable='true'], .input-area").first
            try:
                if await input_box.is_visible():
                    await input_box.click(timeout=3000)
                    await input_box.fill(reply_text)
                    await page.keyboard.press("Enter")
                    print("   🎉 ✅ 消息已成功发送至 HR！", flush=True)
                    await asyncio.sleep(2.0)
            except Exception as e:
                print(f"   ⚠️ 输入框交互提示: {e}", flush=True)
                
            await page.screenshot(path=str(screenshots_dir / "chat_reply_verified.png"))
            
        print("\n" + "="*70)
        print("🎉 【端到端真实聊天对答与简历派发测试完成！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
