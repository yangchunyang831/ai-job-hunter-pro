"""
Pure JS Send Reply to HR:
Executes the conversation click, text typing, and send button click in browser DOM.
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
    print("🚀 【智能体全自主实战测试】正在执行 HR 真实打字与发送...")
    print("="*70 + "\n", flush=True)
    
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # 启动 Chrome 浏览器
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
                break
            except Exception:
                pass
                
        if not browser:
            print("❌ 无法直连 Chrome！", flush=True)
            return

        context = browser.contexts[0]
        pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
        page = pages[0] if pages else context.pages[0]
        
        print(f"1. 🎉 成功连接当前页面: {page.url}", flush=True)
        await asyncio.sleep(3.0)
        
        # 2. 读取会话并定位目标
        reply_message = "您好！关注到贵司的英文客服在招岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户线上沟通，请问方便进一步了解下具体的岗位职责和业务方向吗？"
        
        print("2. 正在执行会话定位、打字输入与发送动作...", flush=True)
        result = await page.evaluate(f"""(msg) => {{
            const res = {{ foundConvo: false, filledInput: false, clickedSend: false, convoText: "" }};
            
            // 1. 查找目标会话
            const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, ul li');
            let targetLi = null;
            for (let li of lis) {{
                const txt = li.innerText || '';
                if (txt.includes('湖南') || txt.includes('怀化') || txt.includes('长沙')) continue;
                if (txt.includes('翟') || txt.includes('启页') || txt.includes('欧阳') || txt.includes('览川') || txt.includes('客服')) {{
                    targetLi = li;
                    res.convoText = txt.replace(/\\n/g, ' | ').slice(0, 70);
                    res.foundConvo = true;
                    break;
                }}
            }}
            if (!targetLi && lis.length > 0) {{
                targetLi = lis[0];
                res.convoText = lis[0].innerText.replace(/\\n/g, ' | ').slice(0, 70);
                res.foundConvo = true;
            }}
            
            if (targetLi) {{
                targetLi.click();
            }}
            
            // 2. 查找并填入输入框
            const editor = document.querySelector('#chat-input, div[contenteditable="true"], textarea, .chat-input, .chat-editor, .input-area');
            if (editor) {{
                editor.focus();
                if (editor.isContentEditable) {{
                    editor.innerText = msg;
                    editor.dispatchEvent(new InputEvent('input', {{ bubbles: true, inputType: 'insertText', data: msg }}));
                }} else {{
                    editor.value = msg;
                    editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
                res.filledInput = true;
            }}
            
            // 3. 点击发送按钮
            const btns = document.querySelectorAll('button, a, div[role="button"]');
            for (let b of btns) {{
                if (b.innerText && b.innerText.trim() === '发送') {{
                    b.click();
                    res.clickedSend = true;
                    break;
                }}
            }}
            
            return res;
        }}""", reply_message)
        
        print(f"3. 执行结果报告: {result}", flush=True)
        
        # 敲击回车保底
        try:
            await page.keyboard.press("Enter")
        except Exception:
            pass
            
        await asyncio.sleep(2.5)
        
        # 4. 截图
        try:
            proof_file = screenshots_dir / "agent_live_reply_sent.png"
            await page.screenshot(path=str(proof_file))
            print(f"4. 📸 真实聊天视窗截图已保存至: {proof_file}", flush=True)
        except Exception as e:
            print(f"   截图提示: {e}", flush=True)
            
        print("\n" + "="*70)
        print("🎉 【智能体自主实战测试全部完成！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
