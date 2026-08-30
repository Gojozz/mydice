import pathlib

p = pathlib.Path("index.html")
html = p.read_text(encoding="utf-8")

# Ganti fungsi createFlagTexture + attachFlag + setMarbleFlag biar stabil & jelas
old = """function createFlagTexture(emoji){
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
}"""

new = """function createFlagTexture(emoji){
  const canvas=document.createElement('canvas');
  canvas.width=256;
  canvas.height=192;
  const ctx=canvas.getContext('2d');
  // background gelap biar kontras
  ctx.fillStyle='rgba(0,0,0,0.55)';
  ctx.beginPath();
  if(ctx.roundRect) ctx.roundRect(8,12,240,168,20); else ctx.rect(8,12,240,168);
  ctx.fill();
  // border tipis
  ctx.strokeStyle='rgba(255,255,255,0.35)';
  ctx.lineWidth=4;
  ctx.stroke();
  // emoji bendera (lebih besar & tajam)
  ctx.font='120px serif';
  ctx.textAlign='center';
  ctx.textBaseline='middle';
  ctx.fillText(emoji||'🏳️', 128, 100);
  const tex=new THREE.CanvasTexture(canvas);
  tex.needsUpdate=true;
  tex.minFilter=THREE.LinearFilter;
  tex.magFilter=THREE.LinearFilter;
  return tex;
}

// Flag tidak di-parent ke marble (supaya tidak ikut muter / loncat)
const flagSprites = [null, null, null, null];

function attachFlag(marble, emoji){
  const id = marble.userData.id;
  if(id < 0 || id > 3) return;

  // kalau emoji sama, jangan buat ulang (biar tidak kedip)
  if(flagSprites[id] && marble.userData.flag === emoji){
    return;
  }

  // hapus yang lama
  if(flagSprites[id]){
    scene.remove(flagSprites[id]);
    if(flagSprites[id].material.map) flagSprites[id].material.map.dispose();
    flagSprites[id].material.dispose();
    flagSprites[id] = null;
  }

  const mat = new THREE.SpriteMaterial({
    map: createFlagTexture(emoji),
    transparent: true,
    depthTest: true,
    depthWrite: false
  });
  const sprite = new THREE.Sprite(mat);
  sprite.scale.set(2.8, 2.1, 1);
  scene.add(sprite);
  flagSprites[id] = sprite;
  marble.userData.flag = emoji;
}

function setMarbleFlag(id, emoji, displayName){
  if(id < 0 || id > 3) return;
  const changed = playerFlags[id] !== emoji;
  playerFlags[id] = emoji;
  if(displayName) playerNames[id] = displayName;

  // update hanya marble utama (bukan klon)
  const main = marbles.find(m => m.userData.id === id && m.userData.cloneId === 0 && !m.userData.eliminated);
  if(main && changed){
    attachFlag(main, emoji);
  }
  updateUI();
}

// Update posisi flag setiap frame (stabil, tidak loncat)
function updateFlagPositions(){
  for(let i = 0; i < 4; i++){
    const sprite = flagSprites[i];
    if(!sprite) continue;
    const m = marbles.find(x => x.userData.id === i && x.userData.cloneId === 0 && !x.userData.eliminated);
    if(!m){
      sprite.visible = false;
      continue;
    }
    sprite.visible = true;
    // ikut posisi marble, tapi TIDAK ikut rotasi
    sprite.position.x = m.position.x;
    sprite.position.y = m.position.y + 2.6;
    sprite.position.z = m.position.z;
  }
}"""

if old in html:
    html = html.replace(old, new)
    print("Fungsi flag diganti")
else:
    print("BLOK LAMA TIDAK DITEMUKAN - coba cek manual")
    # fallback: tetap tulis file supaya tidak rusak
    pass

# Panggil updateFlagPositions di dalam loop update
if "updateFlagPositions()" not in html:
    # sisipkan di akhir function update, sebelum closing-nya yang berhubungan dengan timer/ui
    if "if(++tick%12===0) updateUI();" in html:
        html = html.replace(
            "if(++tick%12===0) updateUI();",
            "updateFlagPositions();\n  if(++tick%12===0) updateUI();"
        )
        print("updateFlagPositions ditambahkan ke loop")
    else:
        print("Peringatan: tidak ketemu tempat sisip updateFlagPositions")

p.write_text(html, encoding="utf-8")
print("SUKSES perbaiki bendera")
