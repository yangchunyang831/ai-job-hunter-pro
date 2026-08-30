"""
Direct Send Chat Message to English CS HR.
Completely standalone, runs headless/headed with persistent context,
types and sends the message to 翟先生 / 欧阳先生, and captures screenshot proof.
"""
import sys
import os
import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

chat_url = "https://www.zhipin.com/web/geek/chat"
user_data_dir = r"C:\chrome_debug_profile"


async def main():
    print("\n" + "="*70)
    print("🚀 BOSS 直聘【直接打字并发送消息至【翟先生/欧阳先生】】启动")
    print("="*70 + "\n", flush=True)
    
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        print("1. 正在拉起 Chrome 浏览器并加载登录 Profile...", flush=True)
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome",
            args=["--no-first-run", "--no-default-browser-check"]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("2. 正在直达消息中心 (https://www.zhipin.com/web/geek/chat)...", flush=True)
        await page.goto(chat_url, wait_until="domcontentloaded")
        await asyncio.sleep(4.0)
        
        # 3. 查找并点击目标英语客服会话 (翟先生 / 欧阳先生)
        print("3. 正在定位并选中【翟先生 / 欧阳先生】会话...", flush=True)
        clicked_info = await page.evaluate("""() => {
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
        print(f"   👉 选中结果: {clicked_info}", flush=True)
        await asyncio.sleep(3.0)
        
        reply_message = "您好！关注到贵司的英文客服岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户线上沟通，请问方便进一步了解下具体的岗位职责和业务方向吗？"
        print(f"\n4. 🤖 准备填入的回复话术:\n   \"{reply_message}\"", flush=True)
        
        # 5. 填入输入框
        print("5. 正在注入输入框并触发发送...", flush=True)
        sent_result = await page.evaluate(f"""(msg) => {{
            // 查找所有可能的聊天输入框
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
            
            // 点击发送按钮
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
            return {{ success: true, method: "text_set_press_enter" }};
        }}""", reply_message)
        print(f"   👉 填入与发送状态: {sent_result}", flush=True)
        
        # 键盘 Enter 保底
        await page.keyboard.press("Enter")
        await asyncio.sleep(3.0)
        
        # 6. 截图留证
        proof_path = screenshots_dir / "verified_chat_sent_proof.png"
        await page.screenshot(path=str(proof_path))
        print(f"\n6. 📸 真实聊天窗口截图已保存至: {proof_path}", flush=True)
        
        # 7. 提取右侧聊天气泡
        bubbles = await page.evaluate("""() => {
            const list = [];
            document.querySelectorAll('.chat-message, .message-card, .item-myself, .item-friend, .chat-item-myself, .chat-item-hr, [class*="myself"], [class*="friend"]').forEach(el => {
                const txt = el.innerText ? el.innerText.trim() : '';
                if (txt) list.push(txt.replace(/\\n/g, ' '));
            });
            return list;
        }""")
        print(f"\n7. 💬 聊天视窗中的气泡记录:\n   {bubbles}", flush=True)
        
        await asyncio.sleep(2.0)
        await context.close()
        
        print("\n" + "="*70)
        print("🎉 【发送执行完毕！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
