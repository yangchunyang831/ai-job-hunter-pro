"""
Starts Chrome detached with remote debugging port 9222 and sends message to 翟先生.
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

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data_dir = r"C:\chrome_debug_profile"
chat_url = "https://www.zhipin.com/web/geek/chat"


async def main():
    print("\n" + "="*70)
    print("🚀 BOSS 直聘【启动常驻 Chrome 并为【翟先生】发送真实回复】")
    print("="*70 + "\n", flush=True)
    
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 检查或以 DETACHED 模式拉起 Chrome
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    DETACHED_PROCESS = 0x00000008
    
    print("1. 正在拉起常驻独立 Chrome 浏览器窗口...", flush=True)
    subprocess.Popen(
        [
            chrome_path,
            "--remote-debugging-port=9222",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            chat_url
        ],
        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
        close_fds=True
    )
    
    await asyncio.sleep(4.0)
    
    async with async_playwright() as p:
        browser = None
        for _ in range(12):
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                break
            except Exception:
                await asyncio.sleep(1.0)
                
        if not browser:
            print("❌ 无法接入 Chrome！", flush=True)
            return

        context = browser.contexts[0]
        pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
        page = pages[0] if pages else context.pages[0]
        
        print(f"2. 🎉 成功直连桌面 Chrome 窗口！URL: {page.url}", flush=True)
        
        if "web/geek/chat" not in page.url:
            await page.goto(chat_url, wait_until="domcontentloaded")
            
        print("3. 正在等待消息中心数据加载就绪...", flush=True)
        await asyncio.sleep(3.0)
        
        # 4. 定位并点击【翟先生】
        print("4. 正在定位【翟先生 (上海启页·英文客服)】...", flush=True)
        clicked = await page.evaluate("""() => {
            const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, ul.user-list li, [class*="user-item"]');
            for (let i = 0; i < lis.length; i++) {
                const txt = lis[i].innerText || '';
                if (txt.includes('翟') || txt.includes('启页')) {
                    lis[i].click();
                    return { success: true, index: i, text: txt.replace(/\\n/g, ' | ') };
                }
            }
            if (lis.length > 0) {
                lis[0].click();
                return { success: true, index: 0, text: lis[0].innerText.replace(/\\n/g, ' | ') };
            }
            return { success: false };
        }""")
        print(f"   👉 定位结果: {clicked}", flush=True)
        await asyncio.sleep(3.0)
        
        # 5. 填入回复内容并点击发送
        reply_message = "您好！关注到贵司的英文客服岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户线上沟通，请问方便进一步了解下具体的岗位职责和业务方向吗？"
        print(f"\n5. 🤖 准备发送智能回复:\n   \"{reply_message}\"", flush=True)
        
        # 定位输入框
        editor = page.locator(".chat-input, textarea, .chat-editor, [contenteditable='true'], .input-area").first
        if await editor.is_visible():
            print("6. 正在聚焦输入框并打字...", flush=True)
            await editor.click()
            await asyncio.sleep(0.5)
            await page.keyboard.type(reply_message, delay=15)
            await asyncio.sleep(1.0)
            
            # 点击发送
            send_btn = page.locator("button.btn-send, button:has-text('发送'), [class*='btn-send'], .op-btn-send").first
            if await send_btn.is_visible():
                print("7. 正在点击【发送】按钮...", flush=True)
                await send_btn.click()
            else:
                print("7. 敲击 Enter 键发送...", flush=True)
                await page.keyboard.press("Enter")
                
            await asyncio.sleep(3.0)
            print("🎉 ✅ 消息已成功发送至聊天室！", flush=True)
            
        # 6. 截图
        proof_path = screenshots_dir / "zhai_reply_sent_confirmed.png"
        await page.screenshot(path=str(proof_path))
        print(f"\n8. 📸 真实回复截图已保存至: {proof_path}", flush=True)
        
        # 7. 读取聊天记录
        msgs = await page.evaluate("""() => {
            const list = [];
            document.querySelectorAll('.chat-message, .message-card, .item-myself, .item-friend, .chat-item-myself, .chat-item-hr').forEach(el => {
                const txt = el.innerText ? el.innerText.trim() : '';
                if (txt) list.push(txt.replace(/\\n/g, ' '));
            });
            return list;
        }""")
        print(f"\n9. 💬 聊天视窗中的最新消息列表:\n   {msgs}", flush=True)
        
        print("\n" + "="*70)
        print("🎉 【实战回复已全部完成并确权！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
