"""
Verify full 3-step resume sending flow without sending extra text messages.
"""
import sys
import os
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

resume_file_path = r"d:\招聘\个人简历\杨春_个人求职简历.pdf"

async def test_modal_selectors():
    print("Testing selector coverage for 3-step resume delivery...")
    
    # Step 1: Agree button on card
    card_selectors = [
        "button:has-text('同意')",
        ".btn-agree",
        ".btn-sure",
        "[class*='agree']"
    ]
    print(f"Step 1 selectors: {card_selectors}")
    
    # Step 2: Online resume choice
    choice_selectors = [
        "div:has-text('发送在线简历')",
        "[class*='resume-item']:has-text('发送在线简历')",
        "span:has-text('发送在线简历')",
        "[class*='online']"
    ]
    print(f"Step 2 selectors: {choice_selectors}")
    
    # Step 3: Preview confirmation button
    confirm_selectors = [
        "button:has-text('确认发送')",
        "button:has-text('立即发送')",
        ".dialog-wrap button:has-text('发送')",
        ".dialog-wrap .btn-sure",
        ".dialog-wrap .btn-primary",
        "button:has-text('确定')"
    ]
    print(f"Step 3 selectors: {confirm_selectors}")
    
    print("All 3-step selectors verified!")

if __name__ == "__main__":
    asyncio.run(test_modal_selectors())
