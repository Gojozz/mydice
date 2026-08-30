from pathlib import Path
import re

p = Path("index.html")
s = p.read_text(encoding="utf-8")

# Backup
Path("index.html.before-final-country-fix").write_text(s, encoding="utf-8")

# ============================================================
# 1. HAPUS KAMERA FOLLOW / ZOOM
# ============================================================

s = re.sub(
    r'\n\s*let activeTargetMarble\s*=\s*null;\s*',
    '\n',
    s
)

s = s.replace("activeTargetMarble = null;", "")

# Cari blok kamera yang menggunakan activeTargetMarble
pattern = r'\n\s*if\s*\(!activeTargetMarble\)\s*\{.*?camera\.lookAt\(camTargetLook\);'

replacement = '''
  // FIXED CAMERA — selalu menampilkan seluruh labirin.
  camera.position.set(baseCamPos.x, baseCamPos.y, baseCamPos.z);
  camera.lookAt(0, 0, 0);
'''

s, n = re.subn(pattern, replacement, s, flags=re.S)

print("[CAMERA] follow block removed:", n)

s = re.sub(
    r'\n\s*let camTargetLook\s*=\s*new THREE\.Vector3\(0,\s*0,\s*0\);\s*',
    '\n',
    s
)

s = s.replace(
    "camera.lookAt(camTargetLook);",
    "camera.lookAt(0, 0, 0);"
)

# ============================================================
# 2. HAPUS NAMA WARNA SEBAGAI IDENTITAS
# ============================================================

old = "const COLORS=[0xff2244,0x2288ff,0x22dd66,0xffdd00], NAMES=['MERAH','BIRU','HIJAU','KUNING'], RADIUS=0.95;"

new = "const COLORS=[0xff2244,0x2288ff,0x22dd66,0xffdd00], RADIUS=0.95;"

if old in s:
    s = s.replace(old, new)
    print("[COUNTRY] NAMES removed")
else:
    print("[COUNTRY] NAMES declaration not found")

# ============================================================
# 3. HELPER IDENTITAS NEGARA
# ============================================================

if "function marbleLabel(" not in s:

    marker = "function updateUI(){"

    helper = '''
function getMarbleCountry(m){
  return {
    emoji: m.userData.countryEmoji || '🏳️',
    name: m.userData.countryName || 'Unknown Country'
  };
}

function marbleLabel(m){
  const c=getMarbleCountry(m);
  return `${c.emoji} ${c.name}`;
}

'''

    if marker in s:
        s = s.replace(marker, helper + marker, 1)
        print("[COUNTRY] marbleLabel added")

# ============================================================
# 4. PANEL LEBIH KECIL
# ============================================================

if ".flagEmoji{" not in s:

    css_marker = ".player{"

    css = '''
.player{
  min-width:0;
  width:auto;
  max-width:145px;
  padding:4px 7px;
  border-radius:10px;
  display:flex;
  align-items:center;
  gap:5px;
  font-size:9px;
  line-height:1.1;
  text-align:left;
  white-space:nowrap;
  overflow:hidden;
}
.flagEmoji{
  font-size:18px;
  line-height:1;
  flex:none;
}
.countryName{
  overflow:hidden;
  text-overflow:ellipsis;
}
'''

    if css_marker in s:
        s = s.replace(css_marker, css_marker + css[len(".player{"):], 1)
        print("[PANEL] compact CSS added")

# ============================================================
# 5. EVENT GAME -> NEGARA
# ============================================================

s = s.replace(
    "NAMES[m.userData.id]",
    "marbleLabel(m)"
)

s = s.replace(
    "NAMES[victim.userData.id]",
    "marbleLabel(victim)"
)

s = s.replace(
    "NAMES[colorId]",
    "marbleLabel(m)"
)

s = s.replace(
    "NAMES[i]",
    "marbleLabel(r.m)"
)

# ============================================================
# 6. CLONE DAPAT NEGARA BARU
# ============================================================

old_clone = """const cloneMesh = makeMarble(COLORS[colorId], colorId, newCloneId);"""

if old_clone in s:

    # Hanya tambahkan jika belum ada
    s = s.replace(
        old_clone,
        old_clone + """
          assignRandomCountry(cloneMesh);""",
        1
    )

    print("[CLONE] new country assigned")

# ============================================================
# 7. START ROUND
# ============================================================

s = s.replace(
    "winner=false;elapsed=0; activeTargetMarble=null;",
    "winner=false;elapsed=0;"
)

# ============================================================
# CHECK
# ============================================================

remaining_names = re.findall(r'NAMES\[[^\]]+\]', s)

if remaining_names:
    print("[WARNING] NAMES references remain:")
    for x in sorted(set(remaining_names)):
        print("  ", x)
else:
    print("[OK] No NAMES[] references")

p.write_text(s, encoding="utf-8")

print("[DONE] index.html updated")
