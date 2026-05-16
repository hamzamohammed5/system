"""
شغّله للتحقق من ImageMagick:
  python check_imagemagick.py "C:/A4.xcf"
"""
import sys, os, subprocess, shutil, tempfile

path = sys.argv[1] if len(sys.argv) > 1 else ""

print("=== ImageMagick check ===")

# ابحث عن magick.exe في المسارات الشائعة
import glob
candidates = [
    r"C:\Program Files\ImageMagick*\magick.exe",
    r"C:\Program Files (x86)\ImageMagick*\magick.exe",
]
found_magick = None
for pattern in candidates:
    matches = glob.glob(pattern)
    if matches:
        found_magick = sorted(matches)[-1]
        print(f"  ✅ magick.exe: {found_magick}")
        break

if not found_magick:
    found_magick = shutil.which("magick")
    if found_magick:
        print(f"  ✅ magick (PATH): {found_magick}")

if not found_magick:
    print("  ❌ ImageMagick غير مثبت")
    print("\n  حمّله من: https://imagemagick.org/script/download.php#windows")
    print("  اختر: ImageMagick-*-Q16-HDRI-x64-dll.exe")
    print("  ✅ فعّل: 'Install legacy utilities (e.g. convert)'")
    sys.exit(0)

# اتحقق من دعم XCF
if path and os.path.exists(path):
    print(f"\n=== Test convert XCF → PNG ===")
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    
    r = subprocess.run(
        [found_magick, path, "-thumbnail", "256x256", tmp.name],
        capture_output=True, text=True, timeout=15
    )
    print(f"  returncode: {r.returncode}")
    if r.stderr:
        print(f"  stderr: {r.stderr[:300]}")
    
    exists = os.path.exists(tmp.name)
    size   = os.path.getsize(tmp.name) if exists else 0
    print(f"  PNG output: {'✅' if exists and size > 100 else '❌'} ({size} bytes)")
    if exists:
        os.unlink(tmp.name)

print("\n=== Test Wand ===")
if path and os.path.exists(path):
    try:
        from wand.image import Image as WandImage
        with WandImage(filename=path) as img:
            print(f"  ✅ Wand opened: {img.width}×{img.height} {img.format}")
    except Exception as e:
        print(f"  ❌ Wand error: {e}")