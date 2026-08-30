import pathlib, re
p = pathlib.Path("index.html")
html = p.read_text(encoding="utf-8")

# 1. Naikkan speed
html = html.replace(
    "m.userData.speed = 0.22 + Math.random() * 0.04;",
    "m.userData.speed = 0.38 + Math.random() * 0.08;"
)

# 2. Hapus boost pads
html = re.sub(
    r"  const remainingForBoosts = allValidCells\.filter\(c => !occupiedKeys\.has\(`\$\{c\.x\},\$\{c\.z\}`\)\);\n"
    r"  remainingForBoosts\.sort\(\(\) => Math\.random\(\) - 0\.5\);\n"
    r"  const boostCount = Math\.min\(remainingForBoosts\.length, 5\);\n"
    r"  for\(let i = 0; i < boostCount; i\+\+\)\{\n"
    r"    const cell = remainingForBoosts\[i\];\n"
    r"    const px = \(cell\.x - HALF_X\)\*CELL, pz = \(cell\.z - HALF_Z\)\*CELL;\n"
    r"    createBoostPadMesh\(px, pz\);\n"
    r"  \}",
    "  // Boost pads dihapus",
    html
)

# 3. Hapus animasi & collision boost
html = re.sub(
    r"  boosts\.forEach\(b => \{\n    if\(b\.arrow\)\{\n      b\.arrow\.position\.y = 0\.05 \+ Math\.sin\(performance\.now\(\) \* 0\.01\) \* 0\.03;\n    \}\n  \}\);",
    "  // boost anim dihapus",
    html
)
html = re.sub(
    r"    for\(const b of boosts\)\{\n      const dist = Math\.hypot\(m\.position\.x - b\.x, m\.position\.z - b\.z\);\n      if\(dist < 1\.1 && \(!m\.userData\.boostCooldown \|\| m\.userData\.boostCooldown <= 0\)\)\{\n        m\.userData\.boostCooldown = 1\.2;\n        const dirX = m\.userData\.vx \|\| \(Math\.random\(\) - 0\.5\);\n        const dirZ = m\.userData\.vz \|\| \(Math\.random\(\) - 0\.5\);\n        const len = Math\.hypot\(dirX, dirZ\) \|\| 1;\n\n        m\.userData\.vx \+= \(dirX / len\) \* 0\.95;\n        m\.userData\.vz \+= \(dirZ / len\) \* 0\.95;\n        createBoostEffect\(b\.x, b\.z\);\n        document\.getElementById\('status'\)\.textContent = `⚡ SPEED BOOST! \$\{NAMES\[m\.userData\.id\]\} MELESAT!`;\n        break;\n      \}\n    \}",
    "    // boost collision dihapus",
    html
)

# 4. Bendera SEDERHANA lewat HUD saja dulu (tidak pakai 3D, biar tidak rusak)
# Kita hanya tampilkan emoji di list player + status, TIDAK floating 3D dulu
if "playerFlags" not in html:
    html = html.replace(
        "const COLORS=[0xff2244,0x2288ff,0x22dd66,0xffdd00], NAMES=['MERAH','BIRU','HIJAU','KUNING'], RADIUS=0.95;",
        "const COLORS=[0xff2244,0x2288ff,0x22dd66,0xffdd00], NAMES=['MERAH','BIRU','HIJAU','KUNING'], RADIUS=0.95;\n"
        "const DEFAULT_FLAGS=['🇮🇩','🇯🇵','🇰🇷','🇧🇷','🇺🇸','🇫🇷','🇩🇪','🇹🇷','🇮🇳','🇹🇭'];\n"
        "let playerFlags=[...DEFAULT_FLAGS].sort(()=>Math.random()-0.5).slice(0,4);\n"
        "let playerNames=[...NAMES];\n"
        "let STATE_URL=(location.port==='8765'?'':'http://127.0.0.1:8765')+'/state';\n"
        "function setMarbleFlag(id,emoji,name){ if(id>=0&&id<4){ playerFlags[id]=emoji; if(name) playerNames[id]=name; updateUI(); } }\n"
        "async function pollPlayerState(){ try{ const r=await fetch(STATE_URL,{cache:'no-store'}); if(!r.ok)return; const s=await r.json(); (s.active||[]).forEach((p,i)=>{ if(i>3)return; const f=p.flag||playerFlags[i]; const n=(p.name||p.user||NAMES[i]).toString().slice(0,12); if(playerFlags[i]!==f||playerNames[i]!==n) setMarbleFlag(i,f,n); }); }catch(e){} }\n"
        "setInterval(pollPlayerState,2000); pollPlayerState();"
    )

# Update label di UI
old_ui = "      const label = r.m.userData.cloneId > 0 ? `${NAMES[r.i]} (Klon \( {r.m.userData.cloneId})` : NAMES[r.i];\n      div.innerHTML=`<div class=\"dot\" style=\"background:# \){COLORS[r.i].toString(16).padStart(6,'0')}\"></div> ${label}`;"
new_ui = "      const flag=playerFlags[r.i]||'🏳️'; const base=playerNames[r.i]||NAMES[r.i];\n      const label = r.m.userData.cloneId > 0 ? `${flag} ${base} (Klon \( {r.m.userData.cloneId})` : ` \){flag} \( {base}`;\n      div.innerHTML=`<div class=\"dot\" style=\"background:# \){COLORS[r.i].toString(16).padStart(6,'0')}\"></div> ${label}`;"
if old_ui in html:
    html = html.replace(old_ui, new_ui)

p.write_text(html, encoding="utf-8")
print("SUKSES: speed naik + boost hilang + bendera di HUD (aman)")
