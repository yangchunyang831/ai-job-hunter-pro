"""
Find WeFlow direct download link from weflow.top JS bundle.
"""
import sys
import re
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def find_urls():
    r = httpx.get("https://weflow.top/_astro/DownloadCenterClient.DLa6x4-8.js", timeout=10.0)
    print("JS status:", r.status_code)
    if r.status_code == 200:
        # Search for .exe or release urls
        print("JS snippet around exe / release / download:")
        for line in r.text.split(";"):
            if any(k in line.lower() for k in ["download", ".exe", "release", "windows", "http", "pan", "123", "github"]):
                print("  ->", line[:150])

if __name__ == "__main__":
    find_urls()
