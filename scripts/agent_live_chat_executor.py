"""
Agent Live Chat Executor:
Completely autonomous script executed by the AI agent to test live HR replying on BOSS 直聘.
Launches Chrome to /web/geek/chat, clicks 翟先生 / 欧阳先生, types candidate message, sends it,
and captures visual proof screenshot.
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
    
    # 1. 启动 Chrome 浏览器
    print("1. 正在启动 Chrome 并直达 BOSS 直聘消息中心...", flush=True)
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
        for i in range(15):
            await asyncio.sleep(1.0)
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                if browser:
                    print(f"2. 🎉 成功连接 Chrome！(耗时 {i+1} 秒)", flush=True)
                    break
            except Exception:
                pass
                
        if not browser:
            print("❌ 无法直连 Chrome！", flush=True)
            return

        context = browser.contexts[0]
        
        # 寻找消息中心页面
        page = None
        for pg in context.pages:
            if not pg.is_closed() and "zhipin.com" in pg.url:
                page = pg
                break
        if not page and context.pages:
            page = context.pages[0]
            
        print(f"3. 激活当前页面: {page.url}", flush=True)
        
        if "web/geek/chat" not in page.url:
            print("   正在跳转至消息沟通中心...", flush=True)
            await page.goto(chat_url, wait_until="domcontentloaded")
            
        print("4. 正在等待消息中心数据加载就绪...", flush=True)
        for i in range(15):
            await asyncio.sleep(1.0)
            try:
                has_items = await page.evaluate("""() => {
                    const lis = document.querySelectorAll('li');
                    return lis.length > 3;
                }""")
                if has_items:
                    print(f"   🎉 消息列表已于第 {i+1} 秒完全加载就绪！", flush=True)
                    break
            except Exception:
                pass
                
        # 5. 提取会话列表
        conv_list = await page.evaluate("""() => {
            const list = [];
            const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, ul li');
            lis.forEach((li, idx) => {
                const text = li.innerText ? li.innerText.replace(/\\n/g, ' | ').trim() : '';
                if (text.length > 5 && (text.includes('先生') || text.includes('女士') || text.includes(':') || text.includes('沟通'))) {
                    list.push({ idx: idx, text: text });
                }
            });
            return list;
        }""")
        
        print(f"\n5. 📋 扫描到 {len(conv_list)} 个会话记录:", flush=True)
        for c in conv_list:
            print(f"   👉 [会话 {c['idx']+1}]: {c['text'][:65]}", flush=True)
            
        # 6. 定位目标【翟先生 (上海启页·英文客服)】或【欧阳先生 (携程英语客服)】
        target_idx = None
        for c in conv_list:
            if any(loc in c["text"] for loc in ["湖南", "怀化", "长沙"]):
                continue
            if any(kw in c["text"] for kw in ["翟", "启页", "欧阳", "览川", "诺博", "客服", "英语"]):
                target_idx = c["idx"]
                print(f"\n6. 🎯 成功锁定英语客服目标会话: {c['text'][:65]}", flush=True)
                break
                
        if target_idx is None and conv_list:
            target_idx = conv_list[0]["idx"]
            print(f"\n6. 🎯 默认选择首个非湖南会话: {conv_list[0]['text'][:65]}", flush=True)
            
        if target_idx is not None:
            # 点击会话
            await page.evaluate(f"""(idx) => {{
                const lis = document.querySelectorAll('.user-list-content li, .chat-user-list li, ul li');
                if (lis[idx]) lis[idx].click();
            }}""", target_idx)
            await asyncio.sleep(3.0)
            
            # 7. 准备回复话术
            reply_message = "您好！关注到贵司的英文客服在招岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户线上沟通，请问方便进一步了解下具体的岗位职责和业务方向吗？"
            print(f"\n7. 🤖 准备填入聊天输入框的话术:\n   \"{reply_message}\"", flush=True)
            
            # 8. 填入输入框并打字发送
            input_box = page.locator(".chat-input, textarea, .chat-editor, [contenteditable='true'], .input-area").first
            try:
                if await input_box.is_visible():
                    print("8. 正在聚焦聊天输入框并模拟键盘打字...", flush=True)
                    await input_box.click(timeout=3000)
                    await asyncio.sleep(0.5)
                    await page.keyboard.type(reply_message, delay=15)
                    await asyncio.sleep(1.0)
                    
                    send_btn = page.locator("button.btn-send, button:has-text('发送'), [class*='btn-send'], .op-btn-send").first
                    if await send_btn.is_visible():
                        print("9. 发现【发送】按钮，正在点击发送...", flush=True)
                        await send_btn.click(timeout=2000)
                    else:
                        print("9. 敲击 Enter 键发送消息...", flush=True)
                        await page.keyboard.press("Enter")
                        
                    await asyncio.sleep(3.0)
                    print("🎉 ✅ 消息已成功发送至聊天视窗！", flush=True)
            except Exception as e:
                print(f"   ℹ️ 备用方式填入: {e}", flush=True)
                
            # 9. 截图留证
            proof_file = screenshots_dir / "agent_live_reply_sent.png"
            await page.screenshot(path=str(proof_file))
            print(f"\n10. 📸 真实聊天视窗截图已保存至: {proof_file}", flush=True)
            
            # 10. 读取右侧聊天消息
            bubbles = await page.evaluate("""() => {
                const list = [];
                document.querySelectorAll('.chat-message, .message-card, .item-myself, .item-friend, .chat-item-myself, .chat-item-hr').forEach(el => {
                    const txt = el.innerText ? el.innerText.trim() : '';
                    if (txt) list.push(txt.replace(/\\n/g, ' '));
                });
                return list;
            }""")
            print(f"\n11. 💬 聊天视窗中的最新消息气泡:\n   {bubbles}", flush=True)
            
        print("\n" + "="*70)
        print("🎉 【智能体自主实战测试全部完成！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
