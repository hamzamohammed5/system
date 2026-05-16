"""
اختبار تشخيصي لاستخراج الـ thumbnail من ملف XCF
شغّله من مجلد المشروع:
  python test_xcf_debug.py "C:/path/to/file.xcf"
"""
import sys, os, hashlib, struct, glob

def xcf_uri(path):
    p = path.replace("\\", "/")
    if len(p) >= 2 and p[1] == ":":
        return "file:///" + p
    elif p.startswith("/"):
        return "file://" + p
    return "file:///" + p

def check_gimp_cache(xcf_path):
    print("\n=== [1] GIMP Cache ===")
    home    = os.path.expanduser("~")
    appdata = os.environ.get("APPDATA", "")
    uri     = xcf_uri(xcf_path)
    md5     = hashlib.md5(uri.encode("utf-8")).hexdigest()
    print(f"URI  : {uri}")
    print(f"MD5  : {md5}")
    
    found = []
    for size_dir in ("large", "normal", "x-large"):
        for base in [
            os.path.join(home, ".cache", "thumbnails", size_dir),
            os.path.join(home, ".thumbnails", size_dir),
        ]:
            p = os.path.join(base, md5 + ".png")
            exists = os.path.exists(p)
            print(f"  {'✅' if exists else '❌'} {p}")
            if exists:
                found.append(p)
        if appdata:
            for ver in ("3.0", "2.99", "2.10", "2.8"):
                p = os.path.join(appdata, "GIMP", ver, "thumbnails", size_dir, md5 + ".png")
                exists = os.path.exists(p)
                if exists:
                    print(f"  ✅ {p}")
                    found.append(p)
    
    # بحث شامل عن أي thumbnails لـ GIMP
    print("\n  [بحث شامل في مجلدات GIMP thumbnails]")
    if appdata:
        for ver in ("3.0", "2.99", "2.10", "2.8"):
            base = os.path.join(appdata, "GIMP", ver, "thumbnails")
            if os.path.exists(base):
                print(f"  موجود: {base}")
                for root, dirs, files in os.walk(base):
                    for f in files[:3]:
                        print(f"    → {os.path.join(root, f)}")
            else:
                print(f"  ❌ {base}")
    
    return found

def check_xcf_native(xcf_path):
    print("\n=== [2] XCF Native Read ===")
    _XCF_MAGIC      = b"gimp xcf "
    _PROP_THUMBNAIL = 1028
    _PROP_END       = 0
    
    try:
        with open(xcf_path, "rb") as f:
            magic = f.read(9)
            print(f"Magic: {magic} ({'✅ XCF' if magic == _XCF_MAGIC else '❌ NOT XCF'})")
            if magic != _XCF_MAGIC:
                return False
            
            ver_raw = f.read(4)
            f.read(1)  # NUL
            try:
                xcf_ver = int(ver_raw.strip(b"\x00v"))
            except:
                xcf_ver = 0
            print(f"Version: {ver_raw} → v{xcf_ver}")
            
            # width, height, base_type
            w, h, bt = struct.unpack(">III", f.read(12))
            print(f"Canvas: {w} × {h}, base_type={bt}")
            
            if xcf_ver >= 4:
                prec = struct.unpack(">I", f.read(4))[0]
                print(f"Precision: {prec}")
            
            # scan props
            for i in range(300):
                ptype = struct.unpack(">I", f.read(4))[0]
                plen  = struct.unpack(">I", f.read(4))[0]
                print(f"  prop[{i}]: type={ptype}, len={plen}")
                
                if ptype == _PROP_END:
                    print("  → PROP_END")
                    break
                
                if ptype == _PROP_THUMBNAIL:
                    print(f"  → ✅ PROP_THUMBNAIL found! payload={plen}")
                    # قراءة payload
                    a = struct.unpack(">i", f.read(4))[0]
                    b = struct.unpack(">i", f.read(4))[0]
                    c = struct.unpack(">i", f.read(4))[0]
                    data_len = plen - 12
                    print(f"     a={a}, b={b}, c={c}, data_len={data_len}")
                    
                    raw = f.read(min(data_len, 100))
                    print(f"     first bytes: {raw[:20].hex()}")
                    
                    for width, height in [(b,c),(a,b),(c,b),(a,c)]:
                        if 1 <= width <= 4096 and 1 <= height <= 4096:
                            total = width * height
                            if total > 0 and data_len % total == 0:
                                bpp = data_len // total
                                if bpp in (3, 4):
                                    print(f"     ✅ Decode: {width}×{height} bpp={bpp}")
                                    return True
                    print("     ❌ Could not decode dimensions")
                    return False
                
                f.seek(plen, 1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback; traceback.print_exc()
    return False

def check_gimp_exe():
    print("\n=== [3] GIMP Executable ===")
    import shutil
    for name in ("gimp", "gimp-2.10", "gimp-2.99", "gimp-3.0"):
        found = shutil.which(name)
        if found:
            print(f"  ✅ {name} → {found}")
    
    for pattern in [
        r"C:\Program Files\GIMP *\bin\gimp-*.exe",
        r"C:\Program Files (x86)\GIMP *\bin\gimp-*.exe",
    ]:
        matches = glob.glob(pattern)
        for m in matches:
            print(f"  ✅ {m}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_xcf_debug.py <path_to_xcf>")
        sys.exit(1)
    
    path = sys.argv[1]
    print(f"XCF File: {path}")
    print(f"Exists: {os.path.exists(path)}")
    if os.path.exists(path):
        print(f"Size: {os.path.getsize(path):,} bytes")
    
    check_gimp_cache(path)
    check_xcf_native(path)
    check_gimp_exe()