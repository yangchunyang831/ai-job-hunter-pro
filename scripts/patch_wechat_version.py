"""
WeChat 4.0 Version Spoofer / Patcher
Spoofs version DWORD from 4.0.3.11 (0x6400030B) to 4.1.13.12 (0x64010D0C)
to bypass Tencent server's '版本过低' check!
"""
import os
import shutil
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DLL_PATH = r"D:\Tencent\Weixin\4.0.3.11\Weixin.dll"
BAK_PATH = r"D:\Tencent\Weixin\4.0.3.11\Weixin.dll.bak"

OLD_HEX = b"\x0b\x03\x00\x64"  # 0x6400030B (4.0.3.11)
NEW_HEX = b"\x0c\x0d\x01\x64"  # 0x64010D0C (4.1.13.12)

def patch_version():
    if not os.path.exists(DLL_PATH):
        print(f"❌ 未找到 {DLL_PATH}")
        return False
    
    if not os.path.exists(BAK_PATH):
        shutil.copyfile(DLL_PATH, BAK_PATH)
        print(f"📦 已创建原始备份: {BAK_PATH}")
    
    with open(BAK_PATH, "rb") as f:
        data = f.read()
        
    count = data.count(OLD_HEX)
    print(f"🔍 找到目标版本特征码 {count} 处")
    
    if count == 0:
        print("⚠️ 未找到旧特征码或已被修改")
        return False
        
    patched_data = data.replace(OLD_HEX, NEW_HEX)
    
    with open(DLL_PATH, "wb") as f:
        f.write(patched_data)
        
    print(f"✅ 成功将微信版本号伪装为 4.1.13.12！已写入 {DLL_PATH}")
    return True

if __name__ == "__main__":
    patch_version()
