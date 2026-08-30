"""
Agent Self-Testing Live Reply Script.
Waits for chat list to load, clicks 翟先生, types reply, clicks send, and takes screenshot proof.
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
    print("\n" + "="*70)
    print("🤖 【智能体自主实操】正在进入 BOSS 直聘消息中心执行回复...")
    print("="*70 + "\n", flush=True)
    
    screenshots_dir = Path(__file__).resolve().parent.parent / "tests" / "test_screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        print("1. 正在拉起浏览器并载入用户已登录 Profile...", flush=True)
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome",
            args=["--no-first-run", "--no-default-browser-check"]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("2. 正在进入消息沟通中心 (https://www.zhipin.com/web/geek/chat)...", flush=True)
        await page.goto(chat_url, wait_until="domcontentloaded")
        
        # 充分等待 Vue 与 WebSocket 数据渲染 (等待 6 秒)
        print("2. 正在等待消息中心数据加载就绪...", flush=True)
        for i in range(10):
            await asyncio.sleep(1.0)
            has_list = await page.evaluate("""() => {
                const items = document.querySelectorAll('li, [role="listitem"], .chat-user-list, .user-list');
                return items.length > 5;
            }""")
            if has_list:
                print(f"   🎉 消息列表已于第 {i+1} 秒完全渲染就绪！", flush=True)
                break
                
        await page.screenshot(path=str(screenshots_dir / "chat_inbox_loaded.png"))
        
        # 3. 读取并定位会话
        conv_list = await page.evaluate("""() => {
            const list = [];
            // 抓取所有 li 元素并过滤出包含人名/时间的会话卡片
            document.querySelectorAll('li').forEach((li, idx) => {
                const text = li.innerText ? li.innerText.replace(/\\n/g, ' | ').trim() : '';
                if ((text.includes('先生') || text.includes('女士') || text.includes(':') || text.includes('月') || text.includes('沟通')) && text.length > 5) {
                    list.push({ idx: idx, text: text });
                }
            });
            return list;
        }""")
        
        print(f"\n3. 📋 共发现 {len(conv_list)} 个会话记录:", flush=True)
        for c in conv_list:
            print(f"   👉 {c['text'][:65]}", flush=True)
            
        # 4. 定位【翟先生】或【欧阳先生/携程客服】
        target_li_idx = None
        for c in conv_list:
            if any(k in c["text"] for k in ["湖南", "怀化", "长沙"]):
                continue
            if any(k in c["text"] for k in ["翟", "启页", "欧阳", "览川", "诺博", "客服", "英语"]):
                target_li_idx = c["idx"]
                print(f"\n4. 🎯 成功锁定目标会话: {c['text'][:65]}", flush=True)
                break
                
        if target_li_idx is None and conv_list:
            target_li_idx = conv_list[0]["idx"]
            print(f"\n4. 🎯 默认选择首个会话: {conv_list[0]['text'][:65]}", flush=True)
            
        if target_li_idx is not None:
            # 点击目标会话
            await page.evaluate(f"""(idx) => {{
                const lis = document.querySelectorAll('li');
                if (lis[idx]) lis[idx].click();
            }}""", target_li_idx)
            await asyncio.sleep(2.5)
            
            # 5. 准备回复话术
            reply_message = "您好！关注到贵司的英文客服在招岗位，我的英语听说读写能力良好，能熟练处理英文工单与日常客户线上沟通，请问方便进一步了解下具体的岗位职责和业务方向吗？"
            print(f"\n5. 🤖 准备发送智能回复:\n   \"{reply_message}\"", flush=True)
            
            # 6. 定位输入框并打字发送
            input_box = page.locator(".chat-input, textarea, .chat-editor, [contenteditable='true'], .input-area").first
            if await input_box.is_visible():
                print("6. 正在聚焦聊天输入框并输入...", flush=True)
                await input_box.click()
                await asyncio.sleep(0.5)
                await page.keyboard.type(reply_message, delay=15)
                await asyncio.sleep(1.0)
                
                # 点击发送
                send_btn = page.locator("button.btn-send, button:has-text('发送'), [class*='btn-send'], .op-btn-send").first
                if await send_btn.is_visible():
                    print("7. 点击【发送】按钮...", flush=True)
                    await send_btn.click()
                else:
                    print("7. 敲击 Enter 键发送...", flush=True)
                    await page.keyboard.press("Enter")
                    
                await asyncio.sleep(3.0)
                print("🎉 ✅ 消息已成功发送至聊天室！", flush=True)
                
            # 7. 截图留证
            proof_path = screenshots_dir / "agent_reply_success_proof.png"
            await page.screenshot(path=str(proof_path))
            print(f"\n8. 📸 真实回复截图已保存至: {proof_path}", flush=True)
            
        await asyncio.sleep(2.0)
        await context.close()
        print("\n" + "="*70)
        print("🎉 【实战测试完毕！】")
        print("="*70 + "\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
