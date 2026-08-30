import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

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
    return "您好！感谢您的回复，我对贵司的英语客服岗位非常感兴趣，请问方便进一步了解下具体的岗位职责和业务方向吗？"


async def main():
    print("Connecting to live Chrome on 9222...", flush=True)
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
        page = pages[0] if pages else context.pages[0]
        
        print(f"Connected to page: {page.url}", flush=True)
        if "web/geek/chat" not in page.url:
            print("Navigating to /web/geek/chat ...", flush=True)
            await page.goto("https://www.zhipin.com/web/geek/chat", wait_until="domcontentloaded")
            await asyncio.sleep(4.0)
            
        # JS 提取左侧所有会话
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
        
        print(f"Total conversations extracted: {len(conv_list)}", flush=True)
        for c in conv_list:
            print(f"\n👉 [会话 {c['idx']+1}]: {c['text'][:70]}", flush=True)
            
            # JS 原生触发点击
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
            
            print(f"   HR 消息数: {len(messages)}", flush=True)
            if messages:
                last_msg = messages[-1].replace("\n", " ")
                print(f"   💬 [HR 最新回复]: \"{last_msg}\"", flush=True)
                
                reply = generate_english_cs_reply(last_msg)
                print(f"   🤖 [生成智能应答]: \"{reply}\"", flush=True)
                
                if any(k in last_msg.lower() for k in ["发一份简历", "发个简历", "发下简历", "发简历", "附件简历", "看看简历", "投递", "简历发一下", "简历发我", "简历过来"]):
                    print(f"   📎 [触发简历发送]: {resume_file_path}", flush=True)
                    send_btn = page.locator("button:has-text('发简历'), button:has-text('发送简历'), [ka*='send_resume'], .chat-op .btn-resume").first
                    if await send_btn.is_visible():
                        print("   👉 点击平台工具栏【发简历】...", flush=True)
                        await send_btn.click()
                        await asyncio.sleep(1.5)
                        sure = page.locator(".dialog-wrap .btn-sure, button:has-text('确定'), button:has-text('发送简历')").first
                        if await sure.is_visible():
                            await sure.click()
                            print("   🎉 ✅ 简历已通过平台弹窗发送！", flush=True)
                            
                input_box = page.locator(".chat-input, textarea, .chat-editor, [contenteditable='true'], .input-area").first
                if await input_box.is_visible():
                    await input_box.click()
                    await input_box.fill(reply)
                    await page.keyboard.press("Enter")
                    print(f"   🎉 ✅ 回复已成功输入并回车发送！", flush=True)
                    await asyncio.sleep(2.0)
                    
        await page.screenshot(path="tests/test_screenshots/live_chat_tested_properly.png")
        print("\nScreenshot saved to tests/test_screenshots/live_chat_tested_properly.png", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
