"""
Fetch and parse README for Akasha-WeChat and WeFlow.
"""
import sys
import re
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def inspect_raw_readme(repo):
    raw_urls = [
        f"https://raw.githubusercontent.com/{repo}/main/README.md",
        f"https://raw.githubusercontent.com/{repo}/master/README.md"
    ]
    for url in raw_urls:
        try:
            r = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
            if r.status_code == 200 and len(r.text) > 100:
                print(f"=== [{repo}] RAW README ({url}) ===")
                print(r.text[:3000])
                print("\n" + "="*50 + "\n")
                return True
        except Exception as e:
            print(f"Fetch {url} error: {e}")
    return False

if __name__ == "__main__":
    for repo in ["alingalingling/Akasha-WeChat", "hicccc77/WeFlow"]:
        print(f"Fetching {repo}...")
        if not inspect_raw_readme(repo):
            print(f"Could not fetch raw README for {repo}, trying api.github.com...")
            try:
                r = httpx.get(f"https://api.github.com/repos/{repo}", headers=headers, timeout=10.0)
                if r.status_code == 200:
                    info = r.json()
                    print(f"Description: {info.get('description')}")
                    print(f"Stars: {info.get('stargazers_count')}, Topics: {info.get('topics')}")
            except Exception as e:
                print("API error:", e)
