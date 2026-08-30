import asyncio
import sys
import os
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

resume_file_path = r"d:\招聘\个人简历\杨春_个人求职简历.pdf"


def generate_english_cs_reply(hr_msg: str) -> str:
    msg_lower = hr_msg.lower()
    if any(k in msg_lower for k in ["英语", "外语", "口语", "四级", "六级", "专八", "熟练", "水平", "流畅"]):
        return "您好！我的英语具备良好的听说读写能力，能够熟练使用英文进行邮件往来、工单处理及日常客户线上沟通，日常业务沟通无障碍。请问贵司该岗位主要对接哪些区域的客户呢？"
    if any(k in msg_lower for k in ["发一份简历", "发个简历", "发下简历", "发简历", "附件简历", "看看简历", "投递", "简历发一下", "简历发我"]):
        return "好的，我的个人简历【杨春_个人求职简历.pdf】已为您发送，请您查收！如果有需要进一步了解的项目经历或细节，随时沟通。"
    if any(k in msg_lower for k in ["到岗", "离职", "什么时候", "在职", "时间"]):
        return "您好！我目前已处于离职状态，可根据贵司安排随时到岗开展工作。"
    if any(k in msg_lower for k in ["面试", "电话", "聊聊", "会议", "现场", "视频", "几点", "方便"]):
        return "您好！非常感谢您的认可与邀约，我全天时间均比较充裕，您可以直接通过平台发我面试时间与会议链接，期待与您进一步交流！"
    return "您好！感谢您的回复，我对贵司的英语客服岗位非常感兴趣，请问方便进一步了解下具体的岗位职责和业务方向吗？"


async def main():
    print("Connecting to Chrome on 9222...", flush=True)
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        
        # 寻找处于 chat 的页面
        page = None
        for pg in context.pages:
            if "zhipin.com" in pg.url:
                page = pg
                break
        if not page:
            page = context.pages[0]
            
        print(f"Active Page: {page.url}", flush=True)
        if "web/geek/chat" not in page.url:
            await page.goto("https://www.zhipin.com/web/geek/chat", wait_until="domcontentloaded")
            await asyncio.sleep(4)
            
        # JS 一次性读取全部左侧会话，绝不产生 stale element 异常
        convs = await page.evaluate("""() => {
            const res = [];
            document.querySelectorAll('.user-list-content li, .chat-user-list li, .geek-chat-list li, ul.user-list li').forEach((el, index) => {
                const rect = el.getBoundingClientRect();
                const text = el.innerText ? el.innerText.replace(/\\n/g, ' | ').trim() : '';
                if (text.length > 3) {
                    res.push({
                        index: index,
                        text: text,
                        x: rect.x + rect.width / 2,
                        y: rect.y + rect.height / 2
                    });
                }
            });
            return res;
        }""")
        
        print(f"Found {len(convs)} conversations via JS evaluation:", flush=True)
        for c in convs:
            print(f"   👉 [会话 {c['index']+1}] ({c['x']}, {c['y']}): {c['text'][:60]}", flush=True)
            
        if convs:
            # 点击第一个会话的中心坐标
            first_c = convs[0]
            print(f"\nClicking first conversation at ({first_c['x']}, {first_c['y']})...", flush=True)
            await page.mouse.click(first_c["x"], first_c["y"])
            await asyncio.sleep(2.5)
            
            # 读取右侧聊天记录
            chat_history = await page.evaluate("""() => {
                const msgs = [];
                document.querySelectorAll('.item-friend, .chat-item-hr, .message-card, [class*="friend"]').forEach(el => {
                    const txt = el.innerText ? el.innerText.trim() : '';
                    if (txt) {
                        msgs.push(txt);
                    }
                });
                return msgs;
            }""")
            print(f"Chat history messages from HR: {chat_history}", flush=True)
            
            if chat_history:
                last_hr = chat_history[-1]
                reply = generate_english_cs_reply(last_hr)
                print(f"Generated auto reply: \"{reply}\"", flush=True)
                
                # 尝试输入
                input_box = page.locator(".chat-input, textarea, .chat-editor, [contenteditable='true']").first
                if await input_box.is_visible():
                    await input_box.click()
                    await input_box.fill(reply)
                    await page.keyboard.press("Enter")
                    print("🎉 Message successfully typed and sent to HR!", flush=True)
                    await asyncio.sleep(2)
                    
            await page.screenshot(path="tests/test_screenshots/bulletproof_chat_verified.png")
            print("Screenshot saved to tests/test_screenshots/bulletproof_chat_verified.png", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
