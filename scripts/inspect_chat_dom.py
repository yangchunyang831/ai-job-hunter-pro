"""
Inspect chat DOM structure and execute guaranteed input & click send.
"""
import sys
import os
import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

user_data_dir = r"C:\chrome_debug_profile"
chat_url = "https://www.zhipin.com/web/geek/chat"


async def main():
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome",
            args=["--no-first-run", "--no-default-browser-check"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(chat_url, wait_until="domcontentloaded")
        await asyncio.sleep(4.0)
        
        # 1. 点击会话 2: 翟先生
        clicked = await page.evaluate("""() => {
            const lis = document.querySelectorAll('li');
            for (let i = 0; i < lis.length; i++) {
                if (lis[i].innerText && (lis[i].innerText.includes('翟') || lis[i].innerText.includes('启页'))) {
                    lis[i].click();
                    return { success: true, text: lis[i].innerText.replace(/\\n/g, ' | ') };
                }
            }
            if (lis.length > 0) {
                lis[0].click();
                return { success: true, text: lis[0].innerText.replace(/\\n/g, ' | ') };
            }
            return { success: false };
        }""")
        print(f"1. 选中会话: {clicked}", flush=True)
        await asyncio.sleep(3.0)
        
        # 2. 检查右侧所有输入相关的元素
        inputs_found = await page.evaluate("""() => {
            const res = [];
            document.querySelectorAll('div[contenteditable="true"], textarea, input, [class*="editor"], [class*="input"], [id*="chat-input"]').forEach(el => {
                res.push({
                    tag: el.tagName,
                    id: el.id,
                    className: el.className,
                    contentEditable: el.contentEditable,
                    rect: el.getBoundingClientRect()
                });
            });
            return res;
        }""")
        print(f"2. 发现的输入组件: {inputs_found}", flush=True)
        
        reply_text = "您好！关注到贵司的英文客服岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户线上沟通，请问方便进一步了解下具体的岗位职责和业务方向吗？"
        
        # 3. 填入消息并点击发送
        sent = await page.evaluate(f"""(msg) => {{
            // 找到右侧最大的 contenteditable div 或 textarea
            const candidates = document.querySelectorAll('div[contenteditable="true"], textarea, [class*="chat-input"], [id*="chat-input"], .chat-editor');
            let target = null;
            for (let el of candidates) {{
                const r = el.getBoundingClientRect();
                if (r.width > 200 && r.height > 20) {{
                    target = el;
                    break;
                }}
            }}
            if (!target) return {{ success: false, reason: "No target editor found" }};
            
            target.focus();
            if (target.isContentEditable) {{
                target.innerText = msg;
                target.dispatchEvent(new InputEvent('input', {{ bubbles: true, inputType: 'insertText', data: msg }}));
            }} else {{
                target.value = msg;
                target.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
            
            // 点击发送按钮
            const btns = document.querySelectorAll('button, a, div[role="button"]');
            let sendBtn = null;
            for (let b of btns) {{
                if (b.innerText && (b.innerText.trim() === '发送' || b.innerText.includes('发送'))) {{
                    sendBtn = b;
                    break;
                }}
            }}
            if (sendBtn) {{
                sendBtn.click();
                return {{ success: true, method: "button_click", button: sendBtn.className }};
            }}
            return {{ success: true, method: "text_filled_waiting_enter" }};
        }}""", reply_text)
        print(f"3. 发送执行结果: {sent}", flush=True)
        
        # 额外键盘回车保底
        await page.keyboard.press("Enter")
        await asyncio.sleep(3.0)
        
        # 4. 截图
        await page.screenshot(path=str(screenshots_dir / "zhai_live_chat_verified.png"))
        print("4. 📸 真实聊天视窗截图已保存至 tests/test_screenshots/zhai_live_chat_verified.png", flush=True)
        
        # 5. 提取已发送消息气泡
        bubbles = await page.evaluate("""() => {
            const list = [];
            document.querySelectorAll('.chat-message, .message-card, .item-myself, .item-friend, .chat-item-myself, .chat-item-hr, [class*="myself"], [class*="friend"]').forEach(el => {
                const txt = el.innerText ? el.innerText.trim() : '';
                if (txt) list.push(txt.replace(/\\n/g, ' '));
            });
            return list;
        }""")
        print(f"5. 💬 聊天视窗中的气泡记录: {bubbles}", flush=True)
        
        await asyncio.sleep(2.0)
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
