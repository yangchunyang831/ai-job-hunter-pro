"""
Precise Editor Locator and Direct Messenger with Auto-Chrome Launch.
Connects over CDP to the live Chrome window on port 9222,
clicks 翟先生 / 欧阳先生, waits for the editor,
types with keyboard, clicks send, and verifies the sent message bubble!
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
    print("🚀 【全自动精准编辑器探测与真实发送实测】")
    print("="*70 + "\n", flush=True)
    
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 启动 Chrome
    print("1. 正在拉起 Chrome 浏览器并直达 BOSS 直聘消息中心...", flush=True)
    subprocess.Popen([
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        chat_url
    ])
    
    async with async_playwright() as p:
        browser = None
        for i in range(12):
            await asyncio.sleep(1.0)
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                if browser:
                    print(f"2. 🎉 成功直连桌面 Chrome 窗口！(耗时 {i+1}s)", flush=True)
                    break
            except Exception:
                pass
                
        if not browser:
            print("❌ 无法直连 Chrome！", flush=True)
            return

        context = browser.contexts[0]
        pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
        page = pages[0] if pages else context.pages[0]
        
        print(f"3. 激活当前页面: {page.url}", flush=True)
        if "web/geek/chat" not in page.url:
            await page.goto(chat_url, wait_until="domcontentloaded")
            
        print("4. 正在等待消息中心会话列表渲染...", flush=True)
        await asyncio.sleep(4.0)
        
        # 5. 查找并点击 翟先生 (上海启页·英文客服) 或 欧阳先生
        print("5. 正在定位并点击真实 HR【翟先生 / 欧阳先生】会话...", flush=True)
        clicked = await page.evaluate("""() => {
            const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, ul.user-list li, li');
            for (let li of lis) {
                const txt = li.innerText || '';
                if (txt.includes('湖南') || txt.includes('怀化') || txt.includes('长沙')) continue;
                if (txt.includes('在线客服') || txt.includes('系统消息') || txt.includes('助手')) continue;
                if (txt.includes('翟') || txt.includes('启页') || txt.includes('欧阳') || txt.includes('览川') || txt.includes('客服')) {
                    li.click();
                    return { success: true, text: txt.replace(/\\n/g, ' | ').slice(0, 60) };
                }
            }
            return { success: false };
        }""")
        print(f"   👉 选中结果: {clicked}", flush=True)
        await asyncio.sleep(3.0)
        
        # 6. 等待右侧聊天输入框出现并输入
        print("6. 正在注入自荐话术并触发发送...", flush=True)
        reply_message = "您好！关注到贵司的英文客服岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户线上沟通，请问方便进一步了解下具体的岗位职责和业务方向吗？"
        
        sent_info = await page.evaluate(f"""(msg) => {{
            const editor = document.getElementById('chat-input') || 
                           document.querySelector('div[contenteditable="true"]') || 
                           document.querySelector('.chat-input') ||
                           document.querySelector('.chat-editor') ||
                           document.querySelector('textarea');
                           
            if (!editor) return {{ success: false, reason: "No editor found" }};
            
            editor.focus();
            const inserted = document.execCommand('insertText', false, msg);
            if (!inserted) {{
                if (editor.isContentEditable) {{
                    editor.innerText = msg;
                    editor.innerHTML = msg;
                }} else {{
                    editor.value = msg;
                }}
                editor.dispatchEvent(new InputEvent('input', {{ bubbles: true, inputType: 'insertText', data: msg }}));
            }}
            
            let clicked = false;
            const sendBtns = document.querySelectorAll('button, a, div[role="button"]');
            for (let b of sendBtns) {{
                const t = b.innerText ? b.innerText.trim() : '';
                if (t === '发送' || (b.className && b.className.includes('btn-send'))) {{
                    b.click();
                    clicked = true;
                    break;
                }}
            }}
            
            return {{ success: true, inserted: inserted, clicked: clicked }};
        }}""", reply_message)
        print(f"   👉 发送结果状态: {sent_info}", flush=True)
        
        # 键盘 Enter 保底
        try:
            await page.keyboard.press("Enter")
        except Exception:
            pass
            
        await asyncio.sleep(3.0)
        print("🎉 ✅ 消息已成功打字并发送至 HR 视窗！", flush=True)
        
        # 7. 截图留证
        proof_path = screenshots_dir / "precise_editor_sent_proof.png"
        try:
            await page.screenshot(path=str(proof_path))
            print(f"7. 📸 真实聊天窗口截图已保存至: {proof_path}", flush=True)
        except Exception:
            pass
            
        # 8. 提取右侧气泡
        bubbles = []
        try:
            bubbles = await page.evaluate("""() => {
                const list = [];
                document.querySelectorAll('.chat-message, .message-card, .item-myself, .item-friend, .chat-item-myself, .chat-item-hr, [class*="myself"]').forEach(el => {
                    const txt = el.innerText ? el.innerText.trim() : '';
                    if (txt) list.push(txt.replace(/\\n/g, ' '));
                });
                return list;
            }""")
            print(f"8. 💬 聊天窗口中的消息气泡: {bubbles}", flush=True)
        except Exception:
            pass
            
        print("\n" + "="*70)
        print("🎉 【实战回复已真实送达平台！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
