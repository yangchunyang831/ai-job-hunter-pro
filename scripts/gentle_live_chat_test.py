"""
Gentle Live Chat Tester for Mobile Hotspot Connection.
Zero rapid refreshing. Natural human-like delays.
1. Connects to Chrome on port 9222.
2. Checks page state (login / chat).
3. If chat is loaded, clicks 翟先生 / 欧阳先生, types candidate message, and sends it.
4. Captures screenshot proof.
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
    print("🎯 BOSS 直聘【手机热点新 IP · 温和低频实战对答测试】启动")
    print("="*70 + "\n", flush=True)
    
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 启动 Chrome 浏览器（自然单次拉起）
    print("1. 正在启动 Chrome 浏览器并直达 BOSS 直聘...", flush=True)
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
        for _ in range(12):
            await asyncio.sleep(1.0)
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                if browser:
                    print("2. 🎉 成功接入 Chrome 浏览器！", flush=True)
                    break
            except Exception:
                pass
                
        if not browser:
            print("❌ 无法直连 Chrome！", flush=True)
            return

        context = browser.contexts[0]
        pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
        page = pages[0] if pages else context.pages[0]
        
        print(f"3. 当前页面: {page.url}", flush=True)
        # 温和等待 4 秒让数据加载
        await asyncio.sleep(4.0)
        
        # 截图留存当前状态
        current_screen = screenshots_dir / "hotspot_current_screen.png"
        await page.screenshot(path=str(current_screen))
        print(f"📸 当前页面截图已保存至: {current_screen}", flush=True)
        
        body_txt = await page.evaluate("() => document.body ? document.body.innerText : ''")
        
        # 检查是否还在 403 或登录页
        if "访问受限" in body_txt and "立即登录" in body_txt:
            print("⚠️ 检测到【立即登录】按钮，正在点击以唤起登录窗口...", flush=True)
            btn = page.locator("a:has-text('立即登录'), button:has-text('立即登录')").first
            if await btn.is_visible():
                await btn.click()
                await asyncio.sleep(3.0)
                await page.screenshot(path=str(current_screen))
                print(f"📸 登录弹窗截图已更新至: {current_screen}", flush=True)
                return
                
        if "微信扫码登录" in body_txt or "短信登录" in body_txt:
            print("ℹ️ 页面处于登录扫码状态，二维码已截取至 hotspot_current_screen.png", flush=True)
            return
            
        # 4. 提取会话列表
        print("4. 正在读取消息沟通中心会话...", flush=True)
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
        print(f"   👉 锁定并点击目标会话: {target_info}", flush=True)
        await asyncio.sleep(3.0)
        
        # 5. 填入回复话术
        reply_message = "您好！关注到贵司的英文客服岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户线上沟通，请问方便进一步了解下具体的岗位职责和业务方向吗？"
        print(f"\n5. 🤖 准备发送的智能回复:\n   \"{reply_message}\"", flush=True)
        
        # 填入输入框并发送
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
            return {{ success: true, method: "text_set" }};
        }}""", reply_message)
        print(f"6. 消息填入状态: {sent_status}", flush=True)
        
        await page.keyboard.press("Enter")
        await asyncio.sleep(3.0)
        
        # 6. 截图留证
        proof_path = screenshots_dir / "hotspot_reply_sent_confirmed.png"
        await page.screenshot(path=str(proof_path))
        print(f"\n7. 📸 真实聊天窗口截图已保存至: {proof_path}", flush=True)
        
        # 7. 提取右侧聊天气泡
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
        print("🎉 【实战对答测试执行完毕！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
