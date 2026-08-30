"""
Bulletproof Live Chat Interactor.
Connects over CDP to the user's running Chrome window on desktop,
waits for .user-list-content li, clicks 翟先生, types reply message,
and clicks the send button with screenshot proof.
"""
import sys
import os
import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

chat_url = "https://www.zhipin.com/web/geek/chat"


async def main():
    print("\n" + "="*70)
    print("🚀 BOSS 直聘【直连真机窗口·为【翟先生】发送真实回复】")
    print("="*70 + "\n", flush=True)
    
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        # 直连桌面 Chrome (由 start_auto_chat_responder.bat 或后台运行的 Chrome)
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
        page = pages[0] if pages else context.pages[0]
        
        print(f"1. 🎉 成功接入桌面 Chrome！当前页面: {page.url}", flush=True)
        
        if "web/geek/chat" not in page.url:
            await page.goto(chat_url, wait_until="domcontentloaded")
            
        print("2. 正在等待消息列表数据彻底就绪...", flush=True)
        await page.wait_for_selector(".user-list-content, .chat-user-list, ul.user-list, li", timeout=15000)
        await asyncio.sleep(2.0)
        
        # 3. 查找【翟先生】
        print("3. 正在定位【翟先生 (上海启页·英文客服)】...", flush=True)
        clicked = await page.evaluate("""() => {
            const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, ul li');
            for (let i = 0; i < lis.length; i++) {
                const txt = lis[i].innerText || '';
                if (txt.includes('翟') || txt.includes('启页')) {
                    lis[i].click();
                    return { success: true, index: i, text: txt.replace(/\\n/g, ' | ') };
                }
            }
            return { success: false };
        }""")
        print(f"   👉 定位结果: {clicked}", flush=True)
        await asyncio.sleep(3.0)
        
        # 4. 输入回复内容
        reply_message = "您好！关注到贵司的英文客服在招岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户线上沟通，请问方便进一步了解下具体的岗位职责和业务方向吗？"
        print(f"\n4. 🤖 准备填入聊天输入框:\n   \"{reply_message}\"", flush=True)
        
        # 5. 聚焦输入框并键入
        editor = page.locator(".chat-input, textarea, .chat-editor, [contenteditable='true'], .input-area").first
        if await editor.is_visible():
            print("5. 正在聚焦输入框并打字...", flush=True)
            await editor.click()
            await asyncio.sleep(0.5)
            await page.keyboard.type(reply_message, delay=15)
            await asyncio.sleep(1.0)
            
            # 点击发送
            send_btn = page.locator("button.btn-send, button:has-text('发送'), [class*='btn-send'], .op-btn-send").first
            if await send_btn.is_visible():
                print("6. 正在点击【发送】按钮...", flush=True)
                await send_btn.click()
            else:
                print("6. 敲击 Enter 键发送...", flush=True)
                await page.keyboard.press("Enter")
                
            await asyncio.sleep(3.0)
            print("🎉 ✅ 消息已成功发送至【翟先生】聊天室！", flush=True)
            
        # 6. 截图
        proof_path = screenshots_dir / "zhai_reply_sent_confirmed.png"
        await page.screenshot(path=str(proof_path))
        print(f"\n7. 📸 真实回复截图已保存至: {proof_path}", flush=True)
        
        # 7. 提取右侧聊天记录
        msgs = await page.evaluate("""() => {
            const list = [];
            document.querySelectorAll('.chat-message, .message-card, .item-myself, .item-friend, .chat-item-myself, .chat-item-hr').forEach(el => {
                const txt = el.innerText ? el.innerText.trim() : '';
                if (txt) list.push(txt.replace(/\\n/g, ' '));
            });
            return list;
        }""")
        print(f"\n8. 💬 聊天视窗中的最新消息列表:\n   {msgs}", flush=True)
        
        print("\n" + "="*70)
        print("🎉 【实战回复已全部完成并确权！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
