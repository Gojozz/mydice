import pathlib

p = pathlib.Path("index.html")
html = p.read_text(encoding="utf-8")

# 1. Pastikan ada fungsi updateFlagPositions yang benar
if "function updateFlagPositions" not in html:
    print("ERROR: updateFlagPositions belum ada")
else:
    print("OK: updateFlagPositions ada")

# 2. Ganti seluruh blok flag supaya lebih sederhana & pasti jalan
# Hapus versi lama yang bermasalah, ganti dengan versi stabil

# Cari dan ganti dari createFlagTexture sampai sebelum const marbles
import re

# Versi baru yang lebih sederhana
new_flag_block = r'''
function createFlagTexture(emoji){
  const canvas=document.createElement('canvas');
  canvas.width=256; canvas.height=192;
  const ctx=canvas.getContext('2d');
  ctx.fillStyle='rgba(0,0,0,0.6)';
  ctx.beginPath();
  if(ctx.roundRect) ctx.roundRect(8,12,240,168,18); else ctx.rect(8,12,240,168);
  ctx.fill();
  ctx.strokeStyle='rgba(255,220,100,0.5)';
  ctx.lineWidth=5;
  ctx.stroke();
  ctx.font='110px serif';
  ctx.textAlign='center';
  ctx.textBaseline='middle';
  ctx.fillText(emoji||'🏳️',128,100);
  const tex=new THREE.CanvasTexture(canvas);
  tex.needsUpdate=true;
  tex.minFilter=THREE.LinearFilter;
  tex.magFilter=THREE.LinearFilter;
  return tex;
}

const flagSprites=[null,null,null,null];

function ensureFlag(id, emoji){
  if(id<0||id>3) return;
  // buat baru hanya jika belum ada atau emoji beda
  if(flagSprites[id] && flagSprites[id].userData.emoji===emoji) return;

  if(flagSprites[id]){
    scene.remove(flagSprites[id]);
    try{ flagSprites[id].material.map.dispose(); }catch(e){}
    try{ flagSprites[id].material.dispose(); }catch(e){}
    flagSprites[id]=null;
  }
  const mat=new THREE.SpriteMaterial({
    map:createFlagTexture(emoji),
    transparent:true,
    depthTest:true,
    depthWrite:false
  });
  const sp=new THREE.Sprite(mat);
  sp.scale.set(3.0, 2.25, 1);
  sp.userData.emoji=emoji;
  scene.add(sp);
  flagSprites[id]=sp;
}

function setMarbleFlag(id,emoji,displayName){
  if(id<0||id>3) return;
  playerFlags[id]=emoji;
  if(displayName) playerNames[id]=displayName;
  ensureFlag(id, emoji);
  updateUI();
}

function updateFlagPositions(){
  for(let i=0;i<4;i++){
    const sp=flagSprites[i];
    // cari marble utama yang masih hidup
    let m=null;
    for(const x of marbles){
      if(x.userData.id===i && x.userData.cloneId===0 && !x.userData.eliminated){
        m=x; break;
      }
    }
    if(!sp){
      // belum ada sprite, buat pakai flag default
      ensureFlag(i, playerFlags[i]||DEFAULT_FLAGS[i%DEFAULT_FLAGS.length]);
      continue;
    }
    if(!m){
      sp.visible=false;
      continue;
    }
    sp.visible=true;
    // ikuti posisi marble (tidak ikut rotasi)
    sp.position.set(m.position.x, m.position.y + 2.8, m.position.z);
  }
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

# Ganti blok lama (dari function createFlagTexture sampai sebelum const marbles=[])
pattern = r"function createFlagTexture\(emoji\)\{[\s\S]*?async function pollPlayerState\(\)\{[\s\S]*?\}\n"
if re.search(pattern, html):
    html = re.sub(pattern, new_flag_block, html)
    print("Blok flag diganti total")
else:
    # coba pola lebih longgar
    pattern2 = r"function createFlagTexture[\s\S]*?async function pollPlayerState[\s\S]*?catch\(e\)\{\}\n\}"
    if re.search(pattern2, html):
        html = re.sub(pattern2, new_flag_block.strip(), html)
        print("Blok flag diganti (pola 2)")
    else:
        print("GAGAL temukan blok lama, coba sisip manual")
        # sisip sebelum const marbles
        if "const marbles=[];" in html and "function ensureFlag" not in html:
            html = html.replace("const marbles=[];", new_flag_block + "\nconst marbles=[];")
            print("Disisipkan sebelum const marbles")

# 3. Pastikan updateFlagPositions dipanggil SETIAP FRAME
# Hapus dulu yang mungkin salah tempat
html = html.replace("updateFlagPositions();\n  if(++tick%12===0) updateUI();", "if(++tick%12===0) updateUI();")
html = html.replace("updateFlagPositions();\n", "")

# Sisipkan di tempat yang pasti jalan: di dalam function update, setelah gerak marble
# Cari pola yang ada di update loop
if "m.position.x+=m.userData.vx;m.position.z+=m.userData.vz;" in html:
    # tambahkan setelah semua marble sudah digeser, sebelum collide / di akhir loop marble
    pass

# Cara paling aman: panggil di animate / di akhir update sebelum requestAnimationFrame
if "function animate" in html or "requestAnimationFrame" in html:
    # cari requestAnimationFrame(animate) atau sejenis
    if "updateFlagPositions();" not in html:
        # sisip sebelum updateUI berkala
        if "if(++tick%12===0) updateUI();" in html:
            html = html.replace(
                "if(++tick%12===0) updateUI();",
                "updateFlagPositions();\n  if(++tick%12===0) updateUI();"
            )
            print("updateFlagPositions dipasang di loop tick")
        elif "update(dt" in html:
            # alternatif
            html = html.replace(
                "function update(dt = 0.016){",
                "function update(dt = 0.016){\n  updateFlagPositions();"
            )
            print("updateFlagPositions dipasang di awal update()")
        else:
            print("WARNING: tidak ketemu tempat pasang updateFlagPositions")
else:
    print("WARNING: struktur animate tidak dikenali")

# 4. Saat reset marbles, pastikan flag dibuat
if "attachFlag(m, playerFlags" in html:
    html = html.replace(
        "attachFlag(m, playerFlags[i] || DEFAULT_FLAGS[i % DEFAULT_FLAGS.length]);",
        "ensureFlag(i, playerFlags[i] || DEFAULT_FLAGS[i % DEFAULT_FLAGS.length]);"
    )
    print("reset marbles pakai ensureFlag")

p.write_text(html, encoding="utf-8")
print("=== SELESAI ===")
print("Cek dengan: grep -n 'updateFlagPositions\\|ensureFlag\\|flagSprites' index.html | head")
