import pathlib, re

p = pathlib.Path("index.html")
html = p.read_text(encoding="utf-8")

# Pastikan speed sudah naik
html = html.replace(
    "m.userData.speed = 0.22 + Math.random() * 0.04;",
    "m.userData.speed = 0.38 + Math.random() * 0.08;"
)

# Hapus boost jika masih ada
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

html = re.sub(
    r"  boosts\.forEach\(b => \{\n"
    r"    if\(b\.arrow\)\{\n"
    r"      b\.arrow\.position\.y = 0\.05 \+ Math\.sin\(performance\.now\(\) \* 0\.01\) \* 0\.03;\n"
    r"    \}\n"
    r"  \}\);",
    "  // Boost animation dihapus",
    html
)

html = re.sub(
    r"    for\(const b of boosts\)\{\n"
    r"      const dist = Math\.hypot\(m\.position\.x - b\.x, m\.position\.z - b\.z\);\n"
    r"      if\(dist < 1\.1 && \(!m\.userData\.boostCooldown \|\| m\.userData\.boostCooldown <= 0\)\)\{\n"
    r"        m\.userData\.boostCooldown = 1\.2;\n"
    r"        const dirX = m\.userData\.vx \|\| \(Math\.random\(\) - 0\.5\);\n"
    r"        const dirZ = m\.userData\.vz \|\| \(Math\.random\(\) - 0\.5\);\n"
    r"        const len = Math\.hypot\(dirX, dirZ\) \|\| 1;\n"
    r"\n"
    r"        m\.userData\.vx \+= \(dirX / len\) \* 0\.95;\n"
    r"        m\.userData\.vz \+= \(dirZ / len\) \* 0\.95;\n"
    r"        createBoostEffect\(b\.x, b\.z\);\n"
    r"        document\.getElementById\('status'\)\.textContent = `⚡ SPEED BOOST! \$\{NAMES\[m\.userData\.id\]\} MELESAT!`;\n"
    r"        break;\n"
    r"      \}\n"
    r"    \}",
    "    // Boost collision dihapus",
    html
)

# Tambah variabel flag
if "DEFAULT_FLAGS" not in html:
    html = html.replace(
        "const COLORS=[0xff2244,0x2288ff,0x22dd66,0xffdd00], NAMES=['MERAH','BIRU','HIJAU','KUNING'], RADIUS=0.95;",
        "const COLORS=[0xff2244,0x2288ff,0x22dd66,0xffdd00], NAMES=['MERAH','BIRU','HIJAU','KUNING'], RADIUS=0.95;\n"
        "const DEFAULT_FLAGS=['🇮🇩','🇯🇵','🇰🇷','🇧🇷','🇺🇸','🇫🇷','🇩🇪','🇹🇷','🇮🇳','🇹🇭','🇻🇳','🇵🇭','🇲🇾','🇸🇬','🇦🇷','🇬🇧'];\n"
        "let playerFlags=[...DEFAULT_FLAGS].sort(()=>Math.random()-0.5).slice(0,4);\n"
        "let playerNames=[...NAMES];\n"
        "let STATE_URL=(location.port==='8765'?'':'http://127.0.0.1:8765')+'/state';"
    )

flag_code = r'''
function createFlagTexture(emoji){
  const canvas=document.createElement('canvas');
  canvas.width=128; canvas.height=96;
  const ctx=canvas.getContext('2d');
  ctx.clearRect(0,0,128,96);
  ctx.fillStyle='rgba(0,0,0,0.35)';
  ctx.beginPath();
  if(ctx.roundRect) ctx.roundRect(4,8,120,80,12); else ctx.rect(4,8,120,80);
  ctx.fill();
  ctx.font='64px serif';
  ctx.textAlign='center';
  ctx.textBaseline='middle';
  ctx.fillText(emoji||'🏳️',64,52);
  const tex=new THREE.CanvasTexture(canvas);
  tex.needsUpdate=true;
  return tex;
}
function attachFlag(marble,emoji){
  if(marble.userData.flagSprite){
    marble.remove(marble.userData.flagSprite);
    if(marble.userData.flagSprite.material.map) marble.userData.flagSprite.material.map.dispose();
    marble.userData.flagSprite.material.dispose();
    marble.userData.flagSprite=null;
  }
  const mat=new THREE.SpriteMaterial({map:createFlagTexture(emoji),transparent:true,depthTest:true});
  const sprite=new THREE.Sprite(mat);
  sprite.scale.set(2.2,1.65,1);
  sprite.position.set(0,2.4,0);
  marble.add(sprite);
  marble.userData.flagSprite=sprite;
  marble.userData.flag=emoji;
}
function setMarbleFlag(id,emoji,displayName){
  if(id<0||id>3) return;
  playerFlags[id]=emoji;
  if(displayName) playerNames[id]=displayName;
  marbles.forEach(m=>{
    if(m.userData.id===id && m.userData.cloneId===0) attachFlag(m,emoji);
  });
  updateUI();
}
async function pollPlayerState(){
  try{
    const res=await fetch(STATE_URL,{cache:'no-store'});
    if(!res.ok) return;
    const state=await res.json();
    const active=state.active||[];
    for(let i=0;i<4;i++){
      if(i<active.length){
        const p=active[i];
        const flag=p.flag||playerFlags[i]||'🏳️';
        const name=(p.name||p.user||NAMES[i]).toString().slice(0,12);
        if(playerFlags[i]!==flag || playerNames[i]!==name){
          setMarbleFlag(i,flag,name);
        }
      }
    }
  }catch(e){}
}
'''

if "createFlagTexture" not in html:
    html = html.replace(
        "const marbles=[];\nfunction makeMarble",
        flag_code + "\nconst marbles=[];\nfunction makeMarble"
    )

# Attach flag saat reset marbles
old_reset = """    marbles.push(m);
    respawnMarble(m, i);
    m.userData.lastX = m.position.x; m.userData.lastZ = m.position.z;
  }
  updateUI();
}"""

new_reset = """    marbles.push(m);
    respawnMarble(m, i);
    m.userData.lastX = m.position.x; m.userData.lastZ = m.position.z;
    attachFlag(m, playerFlags[i] || DEFAULT_FLAGS[i % DEFAULT_FLAGS.length]);
  }
  updateUI();
}"""

if "attachFlag(m, playerFlags" not in html and old_reset in html:
    html = html.replace(old_reset, new_reset)

# Update UI biar tampil bendera
old_ui = """      const label = r.m.userData.cloneId > 0 ? `${NAMES[r.i]} (Klon ${r.m.userData.cloneId})` : NAMES[r.i];
      div.innerHTML=`<div class="dot" style="background:#${COLORS[r.i].toString(16).padStart(6,'0')}"></div> ${label}`;"""

new_ui = """      const flag = playerFlags[r.i] || '🏳️';
      const baseName = playerNames[r.i] || NAMES[r.i];
      const label = r.m.userData.cloneId > 0 ? `${flag} ${baseName} (Klon \( {r.m.userData.cloneId})` : ` \){flag} ${baseName}`;
      div.innerHTML=`<div class="dot" style="background:#${COLORS[r.i].toString(16).padStart(6,'0')}"></div> ${label}`;"""

if "playerFlags[r.i]" not in html and old_ui in html:
    html = html.replace(old_ui, new_ui)

# Mulai polling
if "pollPlayerState" in html and "setInterval(pollPlayerState" not in html:
    html = html.replace(
        "function startRound(){",
        "setInterval(pollPlayerState, 2000);\npollPlayerState();\n\nfunction startRound(){"
    )

p.write_text(html, encoding="utf-8")
print("SUKSES patch index.html")
