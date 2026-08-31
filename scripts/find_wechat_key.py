"""
WeChat 4.x SQLCipher Key Finder via Process Memory Scanning
Scans Weixin.exe memory pages and tests keys against MicroMsg.db page 1.
"""
import sys
import os
import ctypes
import ctypes.wintypes as wintypes
import psutil
from Cryptodome.Cipher import AES
import hashlib
import hmac

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = r"C:\Users\Administrator\Documents\WeChat Files\wxid_qjeqjiuwclso21\Msg\MicroMsg.db"

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
PAGE_READWRITE = 0x04
PAGE_READONLY = 0x02

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

class MEMORY_BASIC_INFORMATION64(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_uint64),
        ("AllocationBase", ctypes.c_uint64),
        ("AllocationProtect", wintypes.DWORD),
        ("Alignment1", wintypes.DWORD),
        ("RegionSize", ctypes.c_uint64),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("Alignment2", wintypes.DWORD),
    ]

def test_key_on_db(raw_key: bytes, db_bytes: bytes) -> bool:
    """Tests if raw_key (32 bytes) or pbkdf2 derived key decrypts page 1 of SQLite db."""
    salt = db_bytes[:16]
    # In SQLCipher, page 1 reserved bytes: typically 48 or 0 bytes at end of page
    # Let's test direct AES CBC on page 1 with IV = salt or page_bytes
    # Case 1: Raw derived key (32 bytes AES key)
    # In SQLCipher 4: first 16 bytes is salt. Next is ciphertext. IV is at page_size - 48 (16 bytes IV, 32 bytes HMAC)
    page_size = 4096
    page = db_bytes[:page_size]
    
    # Try different IV positions used in SQLCipher 3 & 4
    # SQLCipher 4: IV is at page[page_size - 48 : page_size - 32]
    # Ciphertext is page[16 : page_size - 48]
    if len(page) >= page_size:
        # SQLCipher 4
        iv4 = page[page_size - 48 : page_size - 32]
        ct4 = page[16 : page_size - 48]
        try:
            cipher = AES.new(raw_key, AES.MODE_CBC, iv4)
            dec = cipher.decrypt(ct4)
            if dec.startswith(b"SQLite format 3\x00") or b"SQLite format 3" in dec[:32]:
                return True
        except Exception:
            pass
            
        # SQLCipher 3 / WeChat 3
        # IV is at page[page_size - 32 : page_size - 16] or similar
        try:
            iv3 = page[page_size - 32 : page_size - 16]
            ct3 = page[16 : page_size - 32]
            cipher = AES.new(raw_key, AES.MODE_CBC, iv3)
            dec = cipher.decrypt(ct3)
            if dec.startswith(b"SQLite format 3\x00") or b"SQLite format 3" in dec[:32]:
                return True
        except Exception:
            pass
            
        # Direct IV = salt
        try:
            cipher = AES.new(raw_key, AES.MODE_CBC, salt)
            dec = cipher.decrypt(page[16:4096-48])
            if dec.startswith(b"SQLite format 3\x00") or b"SQLite format 3" in dec[:32]:
                return True
        except Exception:
            pass

    return False

def scan_wechat():
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return None

    with open(DB_PATH, "rb") as f:
        db_bytes = f.read(8192)

    pids = [p.pid for p in psutil.process_iter(["pid", "name"]) if "weixin" in p.info["name"].lower()]
    print(f"🔍 找到微信运行进程 PIDs: {pids}")

    for pid in pids:
        print(f"👉 正在扫描微信进程 PID {pid} ...")
        hProcess = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not hProcess:
            continue

        mbi = MEMORY_BASIC_INFORMATION64()
        address = 0
        tested_keys = set()
        
        while address < 0x7FFFFFFFFFFF:
            res = kernel32.VirtualQueryEx(hProcess, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi))
            if res == 0:
                break
                
            # Scan readable memory
            if mbi.State == MEM_COMMIT and (mbi.Protect in (PAGE_READWRITE, PAGE_READONLY, 0x20, 0x40)):
                size = min(mbi.RegionSize, 10 * 1024 * 1024)
                buf = ctypes.create_string_buffer(size)
                bytesRead = ctypes.c_size_t(0)
                
                if kernel32.ReadProcessMemory(hProcess, ctypes.c_void_p(address), buf, size, ctypes.byref(bytesRead)) != 0:
                    data = buf.raw[:bytesRead.value]
                    # Scan for 32-byte blocks aligned by 4 or 8
                    for i in range(0, len(data) - 32, 8):
                        cand = data[i:i+32]
                        if cand not in tested_keys:
                            tested_keys.add(cand)
                            if test_key_on_db(cand, db_bytes):
                                key_hex = cand.hex()
                                print(f"\n🎉🎉🎉 成功找到解密密钥: {key_hex}")
                                kernel32.CloseHandle(hProcess)
                                return key_hex
                                
            address += max(mbi.RegionSize, 4096)

        kernel32.CloseHandle(hProcess)

    print("⚠️ 内存中未匹配到密钥")
    return None

if __name__ == "__main__":
    scan_wechat()
