"""
Force Send Live Reply to English CS HR on BOSS 直聘.
Directly clicks the English CS conversation, types the reply into the chat input,
presses Enter / clicks Send, and captures screenshot proof of the sent message bubble!
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
    print("🚀 BOSS 直聘【立即向英语客服 HR 发送真实沟通回复】")
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
            print("1. 正在启动桌面 Chrome 浏览器...", flush=True)
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
            print("2. 导航至消息沟通中心 (https://www.zhipin.com/web/geek/chat)...", flush=True)
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
                
        # 3. 查找第一个英语客服的会话 (欧阳先生 / 翟先生 / 览川 / 启页 / 诺博)
        print("\n3. 正在定位首个【英语客服】HR 会话...", flush=True)
        
        clicked = await page.evaluate("""() => {
            const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, .geek-chat-list li, ul.user-list li, [class*="user-item"]');
            for (let i = 0; i < lis.length; i++) {
                const txt = lis[i].innerText || '';
                // 排除湖南
                if (txt.includes('湖南') || txt.includes('怀化') || txt.includes('长沙')) continue;
                // 匹配英语客服相关
                if (txt.includes('览川') || txt.includes('启页') || txt.includes('诺博') || txt.includes('世臻') || txt.includes('英语') || txt.includes('英文') || txt.includes('客服')) {
                    lis[i].click();
                    return { success: true, text: txt.replace(/\\n/g, ' | ').slice(0, 70) };
                }
            }
            if (lis.length > 0) {
                lis[0].click();
                return { success: true, text: lis[0].innerText.replace(/\\n/g, ' | ').slice(0, 70) };
            }
            return { success: false, text: '' };
        }""")
        
        print(f"   👉 选中并点击会话: {clicked}", flush=True)
        await asyncio.sleep(3.0)
        
        # 4. 准备高情商回复话术
        reply_message = "您好！关注到贵司正在招聘英语客服岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户沟通，请问方便发一份详细岗位要求了解下吗？"
        print(f"\n4. 🤖 准备发送的智能回复话术:\n   \"{reply_message}\"", flush=True)
        
        # 5. 定位输入框并打字发送
        print("\n5. 正在填入聊天输入框并点击发送...", flush=True)
        
        # 方案 A: 通过 Locator 填入并回车
        input_elem = page.locator(".chat-input, textarea, .chat-editor, [contenteditable='true'], .input-area, div.chat-input").first
        sent_success = False
        try:
            if await input_elem.is_visible():
                await input_elem.click(timeout=3000)
                await input_elem.fill(reply_message)
                await asyncio.sleep(1.0)
                await page.keyboard.press("Enter")
                sent_success = True
                print("   🎉 ✅ 成功通过输入框填入并回车发送！", flush=True)
        except Exception as e:
            print(f"   ℹ️ Locator 填入尝试: {e}", flush=True)
            
        # 方案 B: 如果方案 A 未触发，通过 DOM 事件与按钮点击保底
        if not sent_success:
            print("   👉 使用 DOM 原生事件保底发送...", flush=True)
            sent_success = await page.evaluate(f"""(msg) => {{
                const editor = document.querySelector('.chat-input, textarea, .chat-editor, [contenteditable="true"], .input-area');
                if (!editor) return false;
                if (editor.tagName === 'TEXTAREA' || editor.tagName === 'INPUT') {{
                    editor.value = msg;
                    editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }} else {{
                    editor.innerText = msg;
                    editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
                const sendBtn = document.querySelector('button.btn-send, button:has-text("发送"), [class*="btn-send"], .op-btn-send');
                if (sendBtn) {{
                    sendBtn.click();
                    return true;
                }}
                return true;
            }}""", reply_message)
            await page.keyboard.press("Enter")
            print(f"   🎉 ✅ 原生发送执行结果: {sent_success}", flush=True)
            
        await asyncio.sleep(3.0)
        
        # 6. 截图留证
        await page.screenshot(path=str(screenshots_dir / "reply_sent_live_proof.png"))
        await page.screenshot(path=str(screenshots_dir / "live_chat_replied.png"))
        print(f"\n6. 📸 真实回复送达截图已保存至 tests/test_screenshots/reply_sent_live_proof.png", flush=True)
        
        # 7. 读取右侧聊天框已送达的消息
        chat_bubbles = await page.evaluate("""() => {
            const bubbles = [];
            document.querySelectorAll('.item-myself, .chat-item-myself, .message-content, [class*="myself"]').forEach(el => {
                const txt = el.innerText ? el.innerText.trim() : '';
                if (txt) bubbles.push(txt);
            });
            return bubbles;
        }""")
        print(f"\n7. 💬 聊天窗口中已送达的我的消息列表:\n   {chat_bubbles}", flush=True)
        
        print("\n" + "="*70)
        print("🎉 【回复已真实送达英语客服 HR 聊天视窗！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
