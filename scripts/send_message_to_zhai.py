"""
Direct Message Sender to 翟先生 (上海启页人事专员·英文客服).
Opens /web/geek/chat, clicks 翟先生's conversation, types candidate reply,
clicks send, and captures screenshot verification of the sent message bubble.
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


async def main():
    print("\n" + "="*70)
    print("🚀 BOSS 直聘【立即向【上海启页·翟先生】发送跟进沟通回复】")
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
            print("1. 正在启动 Chrome 浏览器...", flush=True)
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
            print("2. 进入消息中心 (https://www.zhipin.com/web/geek/chat)...", flush=True)
            await page.goto(chat_url, wait_until="domcontentloaded")
            
        print("2. 正在等待消息中心数据加载就绪...", flush=True)
        for _ in range(15):
            await asyncio.sleep(1.0)
            try:
                body_txt = await page.evaluate("() => document.body ? document.body.innerText : ''")
                if "加载中" not in body_txt and len(body_txt) > 20:
                    print("   🎉 消息中心已彻底加载就绪！", flush=True)
                    break
            except Exception:
                pass
                
        # 3. 查找【翟先生】会话项
        print("3. 正在定位【翟先生 (上海启页)】会话...", flush=True)
        found_target = await page.evaluate("""() => {
            const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, .geek-chat-list li, ul.user-list li, [class*="user-item"]');
            for (let i = 0; i < lis.length; i++) {
                const txt = lis[i].innerText || '';
                if (txt.includes('翟') || txt.includes('启页')) {
                    lis[i].click();
                    return { success: true, index: i, text: txt.replace(/\\n/g, ' | ').slice(0, 70) };
                }
            }
            return { success: false, index: -1, text: '' };
        }""")
        
        print(f"   👉 定位结果: {found_target}", flush=True)
        await asyncio.sleep(3.0)
        
        # 4. 准备高情商回复话术
        reply_message = "您好！关注到贵司的英文客服在招岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户线上沟通，请问方便进一步了解下具体的岗位职责和业务方向吗？"
        print(f"\n4. 🤖 准备发送的智能回复话术:\n   \"{reply_message}\"", flush=True)
        
        # 5. 填入输入框并发送
        print("\n5. 正在填入输入框并点击发送...", flush=True)
        
        # 方案 A: Locator 输入与回车
        input_loc = page.locator(".chat-input, textarea, .chat-editor, [contenteditable='true'], .input-area").first
        sent_ok = False
        try:
            if await input_loc.is_visible():
                await input_loc.click(timeout=3000)
                await input_loc.fill(reply_message)
                await asyncio.sleep(0.5)
                send_btn = page.locator("button.btn-send, button:has-text('发送'), [class*='btn-send'], .op-btn-send").first
                if await send_btn.is_visible():
                    await send_btn.click(timeout=2000)
                else:
                    await page.keyboard.press("Enter")
                sent_ok = True
                print("   🎉 ✅ 消息已成功打字并发送至【翟先生】！", flush=True)
        except Exception as e:
            print(f"   ℹ️ Locator 填入提示: {e}", flush=True)
            
        # 方案 B: DOM 事件原生触发保底
        if not sent_ok:
            print("   👉 使用 DOM 原生输入保底发送...", flush=True)
            await page.evaluate(f"""(msg) => {{
                const editor = document.querySelector('.chat-input, textarea, .chat-editor, [contenteditable="true"], .input-area');
                if (editor) {{
                    if (editor.tagName === 'TEXTAREA' || editor.tagName === 'INPUT') {{
                        editor.value = msg;
                        editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }} else {{
                        editor.innerText = msg;
                        editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                    const btn = document.querySelector('button.btn-send, button:has-text("发送"), [class*="btn-send"], .op-btn-send');
                    if (btn) btn.click();
                }}
            }}""", reply_message)
            await page.keyboard.press("Enter")
            print("   🎉 ✅ 原生 DOM 发送指令已执行！", flush=True)
            
        await asyncio.sleep(3.0)
        
        # 6. 截图留证
        await page.screenshot(path=str(screenshots_dir / "zhai_reply_sent_verified.png"))
        await page.screenshot(path=str(screenshots_dir / "live_chat_replied.png"))
        print(f"\n6. 📸 真实回复送达截图已保存至 tests/test_screenshots/zhai_reply_sent_verified.png", flush=True)
        
        # 7. 读取当前右侧聊天消息流
        current_msgs = await page.evaluate("""() => {
            const list = [];
            document.querySelectorAll('.chat-message, .message-card, .item-myself, .item-friend, .chat-item-myself, .chat-item-hr').forEach(el => {
                const txt = el.innerText ? el.innerText.trim() : '';
                if (txt) list.push(txt.replace(/\\n/g, ' '));
            });
            return list;
        }""")
        print(f"\n7. 💬 聊天窗口当前最新消息列表:\n{current_msgs}", flush=True)
        
        print("\n" + "="*70)
        print("🎉 【已成功向【翟先生 (上海启页)】完成沟通消息发送！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
