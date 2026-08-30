import pathlib, re
p = pathlib.Path("index.html")
html = p.read_text(encoding="utf-8")

# A. Speed naik + hapus boost
html = html.replace(
    "m.userData.speed = 0.22 + Math.random() * 0.04;",
    "m.userData.speed = 0.38 + Math.random() * 0.08;"
)
html = re.sub(
    r"  const remainingForBoosts = allValidCells\.filter\(c => !occupiedKeys\.has\(`\$\{c\.x\},\$\{c\.z\}`\)\);\n"
    r"  remainingForBoosts\.sort\(\(\) => Math\.random\(\) - 0\.5\);\n"
    r"  const boostCount = Math\.min\(remainingForBoosts\.length, 5\);\n"
    r"  for\(let i = 0; i < boostCount; i\+\+\)\{\n"
    r"    const cell = remainingForBoosts\[i\];\n"
    r"    const px = \(cell\.x - HALF_X\)\*CELL, pz = \(cell\.z - HALF_Z\)\*CELL;\n"
    r"    createBoostPadMesh\(px, pz\);\n"
    r"  \}",
    "  // boost dihapus",
    html
)
html = re.sub(
    r"  boosts\.forEach\(b => \{\n    if\(b\.arrow\)\{\n      b\.arrow\.position\.y = 0\.05 \+ Math\.sin\(performance\.now\(\) \* 0\.01\) \* 0\.03;\n    \}\n  \}\);",
    "  // boost anim dihapus",
    html
)
html = re.sub(
    r"    for\(const b of boosts\)\{\n      const dist = Math\.hypot\(m\.position\.x - b\.x, m\.position\.z - b\.z\);\n      if\(dist < 1\.1 && \(!m\.userData\.boostCooldown \|\| m\.userData\.boostCooldown <= 0\)\)\{\n        m\.userData\.boostCooldown = 1\.2;\n        const dirX = m\.userData\.vx \|\| \(Math\.random\(\) - 0\.5\);\n        const dirZ = m\.userData\.vz \|\| \(Math\.random\(\) - 0\.5\);\n        const len = Math\.hypot\(dirX, dirZ\) \|\| 1;\n\n        m\.userData\.vx \+= \(dirX / len\) \* 0\.95;\n        m\.userData\.vz \+= \(dirZ / len\) \* 0\.95;\n        createBoostEffect\(b\.x, b\.z\);\n        document\.getElementById\('status'\)\.textContent = `⚡ SPEED BOOST! \$\{NAMES\[m\.userData\.id\]\} MELESAT!`;\n        break;\n      \}\n    \}",
    "    // boost col dihapus",
    html
)

# B. Data negara + flag (hanya data, belum 3D)
inject = '''
const FLAG_COUNTRY={"🇮🇩":"Indonesia","🇯🇵":"Jepang","🇰🇷":"Korea","🇧🇷":"Brazil","🇺🇸":"Amerika","🇫🇷":"Prancis","🇩🇪":"Jerman","🇹🇷":"Turki","🇮🇳":"India","🇹🇭":"Thailand","🇻🇳":"Vietnam","🇵🇭":"Filipina","🇲🇾":"Malaysia","🇸🇬":"Singapura","🇦🇷":"Argentina","🇬🇧":"Inggris","🇨🇳":"China","🇮🇹":"Italia","🇪🇸":"Spanyol","🇳🇱":"Belanda","🇨🇦":"Kanada","🇦🇺":"Australia","🇸🇦":"Saudi","🇵🇸":"Palestina"};
const ALL_FLAGS=Object.keys(FLAG_COUNTRY);
function countryName(f){return FLAG_COUNTRY[f]||"Negara";}
function randomFlags(n){return [...ALL_FLAGS].sort(()=>Math.random()-0.5).slice(0,n);}
let playerFlags=randomFlags(4);
let playerNames=playerFlags.map(countryName);
let STATE_URL=(location.port==="8765"?"":"http://127.0.0.1:8765")+"/state";
function setMarbleFlag(id,emoji,name){if(id>=0&&id<4){playerFlags[id]=emoji;playerNames[id]=name||countryName(emoji);updateUI();}}
async function pollPlayerState(){try{const r=await fetch(STATE_URL,{cache:"no-store"});if(!r.ok)return;const s=await r.json();(s.active||[]).forEach((p,i)=>{if(i>3)return;const f=p.flag||playerFlags[i];const n=(p.name||p.user||playerNames[i]||"").toString().slice(0,12);if(playerFlags[i]!==f||playerNames[i]!==n)setMarbleFlag(i,f,n);});}catch(e){}}
setInterval(pollPlayerState,2000);
'''

if "FLAG_COUNTRY" not in html:
    html = html.replace(
        "const COLORS=[0xff2244,0x2288ff,0x22dd66,0xffdd00], NAMES=['MERAH','BIRU','HIJAU','KUNING'], RADIUS=0.95;",
        "const COLORS=[0xff2244,0x2288ff,0x22dd66,0xffdd00], NAMES=['MERAH','BIRU','HIJAU','KUNING'], RADIUS=0.95;\n" + inject
    )
    print("Data flag ditambahkan")

# C. UI pakai nama negara + emoji
old_label = "const label = r.m.userData.cloneId > 0 ? `${NAMES[r.i]} (Klon ${r.m.userData.cloneId})` : NAMES[r.i];"
new_label = "const flag=playerFlags[r.i]||'🏳️'; const base=playerNames[r.i]||NAMES[r.i]; const label = r.m.userData.cloneId > 0 ? `${flag} ${base} (Klon \( {r.m.userData.cloneId})` : ` \){flag} ${base}`;"
if old_label in html:
    html = html.replace(old_label, new_label)
    print("Label UI diganti nama negara")

# D. Acak ulang tiap ronde
if "playerFlags=randomFlags(4)" not in html.replace(" ", ""):
    html = html.replace(
        "function startRound(){",
        "function startRound(){\n  playerFlags=randomFlags(4);\n  playerNames=playerFlags.map(countryName);\n"
    )
    print("Random tiap ronde")

# E. Flag 3D mengikuti marble (termasuk klon), posisi tinggi
flag3d = r'''
function createFlagTexture(emoji){
  const c=document.createElement("canvas"); c.width=256; c.height=192;
  const g=c.getContext("2d");
  g.fillStyle="rgba(0,0,0,0.65)";
  g.beginPath(); if(g.roundRect) g.roundRect(6,10,244,172,16); else g.rect(6,10,244,172); g.fill();
  g.strokeStyle="rgba(255,220,120,0.5)"; g.lineWidth=4; g.stroke();
  g.font="115px serif"; g.textAlign="center"; g.textBaseline="middle";
  g.fillText(emoji||"🏳️",128,100);
  const t=new THREE.CanvasTexture(c); t.needsUpdate=true; t.minFilter=THREE.LinearFilter; t.magFilter=THREE.LinearFilter; return t;
}
function updateFlagPositions(){
  for(const m of marbles){
    if(m.userData.eliminated){ if(m.userData.flagSprite) m.userData.flagSprite.visible=false; continue; }
    const emoji=playerFlags[m.userData.id]||ALL_FLAGS[m.userData.id%ALL_FLAGS.length];
    if(!m.userData.flagSprite || m.userData.flagSprite.userData.emoji!==emoji){
      if(m.userData.flagSprite){ scene.remove(m.userData.flagSprite); try{m.userData.flagSprite.material.map.dispose();}catch(e){} try{m.userData.flagSprite.material.dispose();}catch(e){} }
      const mat=new THREE.SpriteMaterial({map:createFlagTexture(emoji),transparent:true,depthTest:true,depthWrite:false});
      const sp=new THREE.Sprite(mat); sp.scale.set(2.0,1.5,1); sp.userData.emoji=emoji; scene.add(sp); m.userData.flagSprite=sp;
    }
    const sp=m.userData.flagSprite; sp.visible=true;
    sp.position.set(m.position.x, m.position.y+4.2, m.position.z);
  }
}
'''

if "function updateFlagPositions" not in html:
    html = html.replace("const marbles=[];", flag3d + "\nconst marbles=[];")
    print("Flag 3D ditambahkan")

if "updateFlagPositions();" not in html:
    html = html.replace(
        "if(++tick%12===0) updateUI();",
        "updateFlagPositions();\n  if(++tick%12===0) updateUI();"
    )
    print("Flag update tiap frame")

p.write_text(html, encoding="utf-8")
print("=== PATCH SELESAI ===")
