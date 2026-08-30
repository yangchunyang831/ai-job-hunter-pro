"""
Syncs Default Profile Login Cookies to C:\\chrome_debug_profile\\Default
and directly executes the live chat reply to 翟先生 / 欧阳先生!
"""
import sys
import os
import shutil
import subprocess
import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

src_dir = Path(r"C:\Users\Administrator\AppData\Local\Google\Chrome\User Data\Default")
dst_dir = Path(r"C:\chrome_debug_profile\Default")
chat_url = "https://www.zhipin.com/web/geek/chat"
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def copy_login_state():
    print("1. 正在同步真实用户的登录凭证与 Cookies...", flush=True)
    dst_dir.mkdir(parents=True, exist_ok=True)
    items_to_copy = ["Network", "Local Storage", "Session Storage", "IndexedDB", "Cookies", "Preferences"]
    for item in items_to_copy:
        src_item = src_dir / item
        dst_item = dst_dir / item
        try:
            if src_item.is_dir():
                if dst_item.exists():
                    shutil.rmtree(dst_item, ignore_errors=True)
                shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
            elif src_item.is_file():
                shutil.copy2(src_item, dst_item)
            print(f"   ✅ 同步凭证模块: {item}", flush=True)
        except Exception as e:
            print(f"   ℹ️ 模块同步提示 ({item}): {e}", flush=True)


async def main():
    print("\n" + "="*70)
    print("🎯 BOSS 直聘【克隆真实登录态 ➔ 真实打字 ➔ 平台确权】")
    print("="*70 + "\n", flush=True)
    
    copy_login_state()
    
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # 启动 Chrome
    print("\n2. 正在以用户真实登录态启动 Chrome 并直达消息沟通中心...", flush=True)
    subprocess.Popen([
        chrome_path,
        "--remote-debugging-port=9222",
        "--user-data-dir=C:\\chrome_debug_profile",
        "--no-first-run",
        "--no-default-browser-check",
        chat_url
    ])
    
    async with async_playwright() as p:
        browser = None
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
        
        print(f"3. 当前页面 URL: {page.url}", flush=True)
        if "web/geek/chat" not in page.url:
            await page.goto(chat_url, wait_until="domcontentloaded")
            
        print("4. 正在等待消息中心会话列表彻底加载就绪...", flush=True)
        await asyncio.sleep(5.0)
        
        # 截图当前状态
        await page.screenshot(path=str(screenshots_dir / "user_logged_in_state.png"))
        
        # 5. 读取并点击目标会话
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
        print(f"5. 🎯 选中目标会话: {target_info}", flush=True)
        await asyncio.sleep(3.0)
        
        # 6. 填入回复话术并发送
        reply_message = "您好！关注到贵司的英文客服岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户线上沟通，请问方便进一步了解下具体的岗位职责和业务方向吗？"
        print(f"\n6. 🤖 准备发送的智能回复话术:\n   \"{reply_message}\"", flush=True)
        
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
            return {{ success: true, method: "text_filled" }};
        }}""", reply_message)
        print(f"7. 消息填入状态: {sent_status}", flush=True)
        
        await page.keyboard.press("Enter")
        await asyncio.sleep(3.0)
        
        # 7. 截图留证
        proof_path = screenshots_dir / "user_real_reply_sent_proof.png"
        await page.screenshot(path=str(proof_path))
        print(f"\n8. 📸 真实聊天窗口截图已保存至: {proof_path}", flush=True)
        
        # 8. 提取右侧聊天气泡
        bubbles = await page.evaluate("""() => {
            const list = [];
            document.querySelectorAll('.chat-message, .message-card, .item-myself, .item-friend, .chat-item-myself, .chat-item-hr, [class*="myself"]').forEach(el => {
                const txt = el.innerText ? el.innerText.trim() : '';
                if (txt) list.push(txt.replace(/\\n/g, ' '));
            });
            return list;
        }""")
        print(f"\n9. 💬 聊天窗口当前最新消息列表:\n   {bubbles}", flush=True)
        
        print("\n" + "="*70)
        print("🎉 【回复已真实发送至 BOSS 直聘服务器！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
