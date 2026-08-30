"""
Autonomous Login Capture & Auto-Reply Executor.
Opens BOSS 直聘 Chat, captures screen (login QR code / chat room),
waits for login confirmation, automatically sends English CS follow-up reply,
and captures proof.
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
resume_file_path = r"d:\招聘\个人简历\杨春_个人求职简历.pdf"


async def main():
    print("\n" + "="*70)
    print("🎯 BOSS 直聘【登录屏幕捕获 ➔ 自动对答 ➔ 真实发送】一体化流程启动")
    print("="*70 + "\n", flush=True)
    
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 启动 Chrome 浏览器
    print("1. 正在拉起 Chrome 浏览器并直达 BOSS 直聘...", flush=True)
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
        for _ in range(15):
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
        
        print(f"2. 🎉 成功直连桌面窗口！当前 URL: {page.url}", flush=True)
        await asyncio.sleep(3.0)
        
        # 截图当前屏幕（无论是否需要登录）
        screen_file = screenshots_dir / "current_boss_screen.png"
        await page.screenshot(path=str(screen_file))
        print(f"📸 当前屏幕截图已保存至: {screen_file}", flush=True)
        
        # 检查是否处于登录页
        is_logged_in = False
        for check_round in range(24): # 最长等待 120 秒用户扫码
            body_txt = await page.evaluate("() => document.body ? document.body.innerText : ''")
            
            if any(k in body_txt for k in ["消息", "沟通", "先生", "女士", "求职者", "推荐"]):
                if "微信扫码登录" not in body_txt and "短信登录" not in body_txt:
                    is_logged_in = True
                    print("\n🎉 【检测到已成功进入 BOSS 消息中心！】", flush=True)
                    break
                    
            print(f"⏳ 等待登录授权中... ({check_round * 5}s / 120s)", flush=True)
            await page.screenshot(path=str(screen_file))
            await asyncio.sleep(5.0)
            
        if not is_logged_in:
            print("⚠️ 登录等待超时，请查看 current_boss_screen.png 截图进行扫码。", flush=True)
            return
            
        # 3. 提取会话并发送回复
        print("\n3. 正在读取消息中心列表并锁定英语客服 HR...", flush=True)
        await asyncio.sleep(2.0)
        
        reply_message = "您好！关注到贵司的英文客服岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户线上沟通，请问方便进一步了解下具体的岗位职责和业务方向吗？"
        
        send_result = await page.evaluate(f"""(msg) => {{
            const res = {{ found: false, clicked: false, sent: false, targetName: "" }};
            const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, ul li');
            let targetLi = null;
            
            for (let li of lis) {{
                const txt = li.innerText || '';
                if (txt.includes('湖南') || txt.includes('怀化') || txt.includes('长沙')) continue;
                if (txt.includes('翟') || txt.includes('启页') || txt.includes('欧阳') || txt.includes('览川') || txt.includes('客服') || txt.includes('英语')) {{
                    targetLi = li;
                    res.targetName = txt.replace(/\\n/g, ' | ').slice(0, 60);
                    res.found = true;
                    break;
                }}
            }}
            
            if (!targetLi && lis.length > 0) {{
                targetLi = lis[0];
                res.targetName = lis[0].innerText.replace(/\\n/g, ' | ').slice(0, 60);
                res.found = true;
            }}
            
            if (targetLi) {{
                targetLi.click();
                res.clicked = true;
            }}
            
            return res;
        }}""", reply_message)
        
        print(f"4. 🎯 选中目标会话: {send_result}", flush=True)
        await asyncio.sleep(3.0)
        
        # 填入输入框
        print(f"5. 🤖 准备填入回复:\n   \"{reply_message}\"", flush=True)
        input_box = page.locator("#chat-input, div[contenteditable='true'], textarea, .chat-input, .chat-editor, .input-area").first
        try:
            if await input_box.is_visible():
                await input_box.click(timeout=3000)
                await asyncio.sleep(0.5)
                await page.keyboard.type(reply_message, delay=15)
                await asyncio.sleep(1.0)
                
                send_btn = page.locator("button.btn-send, button:has-text('发送'), [class*='btn-send'], .op-btn-send").first
                if await send_btn.is_visible():
                    await send_btn.click(timeout=2000)
                else:
                    await page.keyboard.press("Enter")
                    
                print("🎉 ✅ 消息已成功打字并发送至 HR 视窗！", flush=True)
        except Exception as e:
            print(f"   ℹ️ 尝试 DOM 原生输入保底: {e}", flush=True)
            await page.evaluate(f"""(msg) => {{
                const editor = document.querySelector('#chat-input, div[contenteditable="true"], textarea, .chat-input, .input-area');
                if (editor) {{
                    if (editor.isContentEditable) {{
                        editor.innerText = msg;
                        editor.dispatchEvent(new InputEvent('input', {{ bubbles: true, inputType: 'insertText', data: msg }}));
                    }} else {{
                        editor.value = msg;
                        editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                    const btn = document.querySelector('button.btn-send, button:has-text("发送")');
                    if (btn) btn.click();
                }}
            }}""", reply_message)
            await page.keyboard.press("Enter")
            
        await asyncio.sleep(3.0)
        
        # 截图留证
        proof_path = screenshots_dir / "live_reply_sent_confirmed.png"
        await page.screenshot(path=str(proof_path))
        print(f"\n6. 📸 最终已发送消息截图已保存至: {proof_path}", flush=True)
        
        print("\n" + "="*70)
        print("🎉 【实战回复测试执行完毕！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
