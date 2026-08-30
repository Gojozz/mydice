import pathlib

p = pathlib.Path("index.html")
html = p.read_text(encoding="utf-8")

# Pastikan variabel dasar sudah ada
if "playerFlags" not in html:
    print("ERROR: playerFlags belum ada. Jalankan fix_flag_hud.py dulu.")
    raise SystemExit(1)

# Blok fungsi flag (versi stabil)
flag_js = r'''
/* ===== FLAG FOLLOW MARBLE ===== */
function createFlagTexture(emoji){
  const c=document.createElement('canvas');
  c.width=256; c.height=192;
  const g=c.getContext('2d');
  g.fillStyle='rgba(0,0,0,0.65)';
  g.beginPath();
  if(g.roundRect) g.roundRect(6,10,244,172,16); else g.rect(6,10,244,172);
  g.fill();
  g.strokeStyle='rgba(255,220,120,0.55)';
  g.lineWidth=4;
  g.stroke();
  g.font='115px serif';
  g.textAlign='center';
  g.textBaseline='middle';
  g.fillText(emoji||'🏳️',128,100);
  const t=new THREE.CanvasTexture(c);
  t.needsUpdate=true;
  t.minFilter=THREE.LinearFilter;
  t.magFilter=THREE.LinearFilter;
  return t;
}
const flagSprites=[null,null,null,null];
function ensureFlagSprite(id,emoji){
  if(id<0||id>3) return;
  const cur=flagSprites[id];
  if(cur && cur.userData.emoji===emoji) return;
  if(cur){
    scene.remove(cur);
    try{cur.material.map.dispose();}catch(e){}
    try{cur.material.dispose();}catch(e){}
    flagSprites[id]=null;
  }
  const mat=new THREE.SpriteMaterial({map:createFlagTexture(emoji),transparent:true,depthTest:true,depthWrite:false});
  const sp=new THREE.Sprite(mat);
  sp.scale.set(2.6,1.95,1);
  sp.userData.emoji=emoji;
  sp.visible=false;
  scene.add(sp);
  flagSprites[id]=sp;
}
function updateFlagPositions(){
  for(let i=0;i<4;i++){
    let m=null;
    for(const x of marbles){
      if(x.userData.id===i && (!x.userData.cloneId||x.userData.cloneId===0) && !x.userData.eliminated){ m=x; break; }
    }
    const emoji=playerFlags[i]||DEFAULT_FLAGS[i%DEFAULT_FLAGS.length];
    ensureFlagSprite(i,emoji);
    const sp=flagSprites[i];
    if(!sp) continue;
    if(!m){ sp.visible=false; continue; }
    sp.visible=true;
    sp.position.set(m.position.x, m.position.y+2.7, m.position.z);
  }
}
/* ===== END FLAG ===== */
'''

# Sisipkan sebelum "const marbles=[]" jika belum ada
if "function updateFlagPositions" not in html:
    if "const marbles=[];" in html:
        html = html.replace("const marbles=[];", flag_js + "\nconst marbles=[];")
        print("Fungsi flag ditambahkan")
    else:
        print("ERROR: const marbles tidak ketemu")
        raise SystemExit(1)
else:
    print("Fungsi flag sudah ada, skip insert")

# Pastikan dipanggil setiap frame
if "updateFlagPositions();" not in html:
    # Tempat paling aman: baris updateUI berkala
    if "if(++tick%12===0) updateUI();" in html:
        html = html.replace(
            "if(++tick%12===0) updateUI();",
            "updateFlagPositions();\n  if(++tick%12===0) updateUI();"
        )
        print("updateFlagPositions dipasang di loop")
    else:
        # fallback: awal function update
        html = html.replace(
            "function update(dt = 0.016){",
            "function update(dt = 0.016){\n  if(typeof updateFlagPositions==='function') updateFlagPositions();"
        )
        print("updateFlagPositions dipasang di awal update()")
else:
    print("updateFlagPositions sudah dipanggil")

# Saat setMarbleFlag dipanggil, pastikan sprite ikut
# (setMarbleFlag dari HUD patch hanya updateUI, kita tambah ensure)
old_set = "function setMarbleFlag(id,emoji,name){if(id>=0&&id<4){playerFlags[id]=emoji;if(name)playerNames[id]=name;updateUI();}}"
new_set = "function setMarbleFlag(id,emoji,name){if(id>=0&&id<4){playerFlags[id]=emoji;if(name)playerNames[id]=name;if(typeof ensureFlagSprite==='function')ensureFlagSprite(id,emoji);updateUI();}}"
if old_set in html:
    html = html.replace(old_set, new_set)
    print("setMarbleFlag diupdate")

p.write_text(html, encoding="utf-8")
print("SUKSES: bendera ikut marble")
