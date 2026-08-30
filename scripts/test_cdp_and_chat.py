"""
Active CDP Connection & Chat Flow Tester.
Checks port 9222, connects to live Chrome, scans chat room,
and tests message sending with full logging and screenshot capture.
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


async def main():
    print("\n" + "="*70)
    print("🚀 【全自主真机穿透测试启动】正在接入 Chrome 进行实战验证...")
    print("="*70 + "\n", flush=True)
    
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser = None
        for i in range(5):
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                if browser:
                    print(f"1. 🎉 成功接入桌面 Chrome (端口 9222)！", flush=True)
                    break
            except Exception:
                await asyncio.sleep(1.0)
                
        if not browser:
            print("⚠️ 未检测到桌面 Chrome 开启 9222 端口，请确保已双击运行 start_auto_chat_responder.bat", flush=True)
            return

        context = browser.contexts[0]
        pages = [pg for pg in context.pages if not pg.is_closed() and "zhipin.com" in pg.url]
        page = pages[0] if pages else context.pages[0]
        
        print(f"2. 当前页面 URL: {page.url}", flush=True)
        
        if "web/geek/chat" not in page.url:
            print("   正在导航至消息沟通中心 (https://www.zhipin.com/web/geek/chat)...", flush=True)
            await page.goto(chat_url, wait_until="domcontentloaded")
            await asyncio.sleep(3.0)
            
        # 读取会话列表
        print("3. 正在读取左侧会话列表...", flush=True)
        convs = await page.evaluate("""() => {
            const res = [];
            const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, ul li');
            lis.forEach((li, idx) => {
                const txt = li.innerText ? li.innerText.replace(/\\n/g, ' | ').trim() : '';
                if (txt.length > 5 && (txt.includes('先生') || txt.includes('女士') || txt.includes(':') || txt.includes('沟通'))) {
                    res.push({ idx: idx, text: txt });
                }
            });
            return res;
        }""")
        
        print(f"   📋 发现 {len(convs)} 个会话记录:", flush=True)
        for c in convs:
            print(f"      👉 {c['text'][:65]}", flush=True)
            
        # 选择英语客服会话
        target = None
        for c in convs:
            if any(loc in c["text"] for loc in ["湖南", "怀化", "长沙"]):
                continue
            if any(kw in c["text"] for kw in ["翟", "启页", "欧阳", "览川", "诺博", "客服", "英语"]):
                target = c
                break
                
        if not target and convs:
            target = convs[0]
            
        if target:
            print(f"\n4. 🎯 选中目标会话: 【{target['text'][:60]}】", flush=True)
            
            # 点击会话
            await page.evaluate(f"""(idx) => {{
                const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, ul li');
                if (lis[idx]) lis[idx].click();
            }}""", target["idx"])
            await asyncio.sleep(2.5)
            
            # 填入回复话术
            reply_text = "您好！关注到贵司的英文客服在招岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户线上沟通，请问方便进一步了解下具体的岗位职责和业务方向吗？"
            print(f"5. 🤖 准备发送智能回复:\n   \"{reply_text}\"", flush=True)
            
            # 填入输入框并发送
            sent_status = await page.evaluate(f"""(msg) => {{
                const editor = document.querySelector('#chat-input, div[contenteditable="true"], textarea, .chat-input, .chat-editor, .input-area');
                if (!editor) return {{ success: false, reason: "No editor" }};
                editor.focus();
                if (editor.isContentEditable) {{
                    editor.innerText = msg;
                    editor.dispatchEvent(new InputEvent('input', {{ bubbles: true, inputType: 'insertText', data: msg }}));
                }} else {{
                    editor.value = msg;
                    editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
                const sendBtn = document.querySelector('button.btn-send, button:has-text("发送"), [class*="btn-send"], .op-btn-send');
                if (sendBtn) {{
                    sendBtn.click();
                    return {{ success: true, method: "btn_click" }};
                }}
                return {{ success: true, method: "text_set" }};
            }}""", reply_text)
            
            print(f"6. 消息填入与发送状态: {sent_status}", flush=True)
            await page.keyboard.press("Enter")
            await asyncio.sleep(2.5)
            
            # 截图
            proof = screenshots_dir / "cdp_live_test_proof.png"
            await page.screenshot(path=str(proof))
            print(f"7. 📸 真实聊天窗口截图已保存至: {proof}", flush=True)
            
        print("\n" + "="*70)
        print("🎉 【穿透实战测试执行完毕！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
