import subprocess
import time
import sys

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
user_data_dir = r"C:\chrome_debug_profile"
chat_url = "https://www.zhipin.com/web/geek/chat"

print("Launching persistent Chrome detached process...", flush=True)
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200

subprocess.Popen(
    [
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        chat_url
    ],
    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
    close_fds=True
)

print("Chrome detached process launched successfully!", flush=True)
