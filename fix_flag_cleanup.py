import pathlib, re

p = pathlib.Path("index.html")
html = p.read_text(encoding="utf-8")

# Fungsi pembersih semua flag sprite
cleanup_fn = r'''
function clearAllFlagSprites(){
  // bersihkan flag di tiap marble
  for(const m of marbles){
    if(m.userData.flagSprite){
      scene.remove(m.userData.flagSprite);
      try{ m.userData.flagSprite.material.map.dispose(); }catch(e){}
      try{ m.userData.flagSprite.material.dispose(); }catch(e){}
      m.userData.flagSprite = null;
    }
  }
  // bersihkan sisa sprite flag yang nyangkut di scene (bukan anak marble)
  const toRemove=[];
  scene.traverse(obj=>{
    if(obj.type==="Sprite" && obj.userData && obj.userData.emoji){
      toRemove.push(obj);
    }
  });
  for(const sp of toRemove){
    scene.remove(sp);
    try{ if(sp.material.map) sp.material.map.dispose(); }catch(e){}
    try{ sp.material.dispose(); }catch(e){}
  }
}
'''

if "function clearAllFlagSprites" not in html:
    # sisip sebelum updateFlagPositions atau sebelum const marbles
    if "function updateFlagPositions" in html:
        html = html.replace("function updateFlagPositions", cleanup_fn + "\nfunction updateFlagPositions")
    else:
        html = html.replace("const marbles=[];", cleanup_fn + "\nconst marbles=[];")
    print("clearAllFlagSprites ditambahkan")
else:
    print("clearAllFlagSprites sudah ada")

# Panggil saat startRound
if "clearAllFlagSprites()" not in html:
    html = html.replace(
        "function startRound(){",
        "function startRound(){\n  if(typeof clearAllFlagSprites==='function') clearAllFlagSprites();\n"
    )
    print("clearAllFlagSprites dipanggil di startRound")
else:
    # pastikan ada di startRound
    if "function startRound(){\n  if(typeof clearAllFlagSprites" not in html and "function startRound(){\n  playerFlags" in html:
        html = html.replace(
            "function startRound(){\n  playerFlags",
            "function startRound(){\n  if(typeof clearAllFlagSprites==='function') clearAllFlagSprites();\n  playerFlags"
        )
    print("startRound dicek")

# Panggil juga di resetMarbles (awal)
if "function resetMarbles" in html and "clearAllFlagSprites" in html:
    # sisip di awal resetMarbles
    old = "function resetMarbles(){\n  while(marbles.length){scene.remove(marbles.pop());}"
    new = "function resetMarbles(){\n  if(typeof clearAllFlagSprites==='function') clearAllFlagSprites();\n  while(marbles.length){scene.remove(marbles.pop());}"
    if old in html:
        html = html.replace(old, new)
        print("clearAllFlagSprites dipanggil di resetMarbles")
    else:
        # pola alternatif
        html = html.replace(
            "function resetMarbles(){",
            "function resetMarbles(){\n  if(typeof clearAllFlagSprites==='function') clearAllFlagSprites();"
        )
        print("clearAllFlagSprites dipanggil di resetMarbles (alt)")

p.write_text(html, encoding="utf-8")
print("SELESAI")
