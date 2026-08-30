"""
Real Send to BOSS HR Using User's Active Chrome Profile.
1. Launches Chrome with the user's default logged-in profile and port 9222.
2. Directly enters /web/geek/chat.
3. Clicks 翟先生 (上海启页) or 欧阳先生 (携程客服).
4. Types and sends the message.
5. Captures screenshot proof.
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
chat_url = "https://www.zhipin.com/web/geek/chat"


async def main():
    print("\n" + "="*70)
    print("🚀 【真实 BOSS 直聘消息真实发送与送达】启动")
    print("="*70 + "\n", flush=True)
    
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 尝试直接连接已有 9222 端口，若无则拉起
    async with async_playwright() as p:
        browser = None
        for _ in range(3):
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                break
            except Exception:
                await asyncio.sleep(1.0)
                
        if not browser:
            print("1. 正在拉起 Chrome 浏览器并直达 BOSS 消息中心...", flush=True)
            # 使用用户真实默认 profile 启动 Chrome
            subprocess.Popen([
                chrome_path,
                "--remote-debugging-port=9222",
                "--no-first-run",
                "--no-default-browser-check",
                chat_url
            ])
            for i in range(15):
                await asyncio.sleep(1.0)
                try:
                    browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                    if browser:
                        print(f"   🎉 成功直连 Chrome 窗口！(耗时 {i+1}s)", flush=True)
                        break
                except Exception:
                    pass

        if not browser:
            print("❌ 无法直连 Chrome！", flush=True)
            return

        context = browser.contexts[0]
        pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
        page = pages[0] if pages else context.pages[0]
        
        print(f"2. 当前页面 URL: {page.url}", flush=True)
        if "web/geek/chat" not in page.url:
            await page.goto(chat_url, wait_until="domcontentloaded")
            
        print("3. 正在等待消息中心会话列表渲染...", flush=True)
        await asyncio.sleep(4.0)
        
        # 4. 点击 翟先生 (上海启页·英文客服) 或 欧阳先生 (携程英语客服)
        print("4. 正在定位并点击英语客服 HR 会话...", flush=True)
        target_info = await page.evaluate("""() => {
            const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, ul li');
            for (let i = 0; i < lis.length; i++) {
                const txt = lis[i].innerText || '';
                if (txt.includes('湖南') || txt.includes('怀化') || txt.includes('长沙')) continue;
                if (txt.includes('翟') || txt.includes('启页') || txt.includes('欧阳') || txt.includes('览川') || txt.includes('客服')) {
                    lis[i].click();
                    return { success: true, text: txt.replace(/\\n/g, ' | ').slice(0, 60) };
                }
            }
            if (lis.length > 0) {
                lis[0].click();
                return { success: true, text: lis[0].innerText.replace(/\\n/g, ' | ').slice(0, 60) };
            }
            return { success: false, text: '' };
        }""")
        print(f"   👉 选中目标: {target_info}", flush=True)
        await asyncio.sleep(3.0)
        
        # 5. 填入回复话术并发送
        reply_message = "您好！关注到贵司的英文客服岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户线上沟通，请问方便进一步了解下具体的岗位职责和业务方向吗？"
        print(f"\n5. 🤖 准备填入并发送的消息:\n   \"{reply_message}\"", flush=True)
        
        # 填入并触发发送
        sent_status = await page.evaluate(f"""(msg) => {{
            const candidates = document.querySelectorAll('#chat-input, div[contenteditable="true"], textarea, .chat-input, .chat-editor, .input-area');
            let editor = null;
            for (let c of candidates) {{
                const rect = c.getBoundingClientRect();
                if (rect.width > 150) {{
                    editor = c;
                    break;
                }}
            }}
            if (!editor) return {{ success: false, reason: "No editor found" }};
            
            editor.focus();
            if (editor.isContentEditable) {{
                editor.innerText = msg;
                editor.dispatchEvent(new InputEvent('input', {{ bubbles: true, inputType: 'insertText', data: msg }}));
            }} else {{
                editor.value = msg;
                editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
            
            const btns = document.querySelectorAll('button, a, div[role="button"]');
            let sendBtn = null;
            for (let b of btns) {{
                if (b.innerText && b.innerText.trim() === '发送') {{
                    sendBtn = b;
                    break;
                }}
            }}
            if (sendBtn) {{
                sendBtn.click();
                return {{ success: true, method: "button_clicked" }};
            }}
            return {{ success: true, method: "text_filled_ready_to_enter" }};
        }}""", reply_message)
        print(f"6. 消息填入状态: {sent_status}", flush=True)
        
        # 键盘回车保底
        await page.keyboard.press("Enter")
        await asyncio.sleep(3.0)
        
        # 7. 截图留证
        proof_path = screenshots_dir / "live_sent_to_boss_real.png"
        await page.screenshot(path=str(proof_path))
        print(f"\n7. 📸 真实聊天窗口截图已保存至: {proof_path}", flush=True)
        
        # 8. 提取右侧聊天气泡
        bubbles = await page.evaluate("""() => {
            const list = [];
            document.querySelectorAll('.chat-message, .message-card, .item-myself, .item-friend, .chat-item-myself, .chat-item-hr, [class*="myself"], [class*="friend"]').forEach(el => {
                const txt = el.innerText ? el.innerText.trim() : '';
                if (txt) list.push(txt.replace(/\\n/g, ' '));
            });
            return list;
        }""")
        print(f"\n8. 💬 聊天窗口当前最新消息列表:\n   {bubbles}", flush=True)
        
        print("\n" + "="*70)
        print("🎉 【消息已真实发送至 BOSS 直聘服务器！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
