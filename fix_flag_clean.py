import pathlib, re

p = pathlib.Path("index.html")
html = p.read_text(encoding="utf-8")

# 1. Hapus sistem flagSprites lama (yang bikin 4 bendera diam)
# Hapus deklarasi array lama
html = re.sub(r"const flagSprites\s*=\s*\[null,null,null,null\];\s*", "", html)
html = re.sub(r"const flagSprites\s*=\s*\[[^\]]*\];\s*", "", html)

# Hapus fungsi ensureFlagSprite lama jika masih ada
html = re.sub(r"function ensureFlagSprite\([^)]*\)\{[\s\S]*?\n\}\s*", "", html)

# 2. Ganti updateFlagPositions dengan versi bersih (hanya ikut marble, posisi lebih tinggi)
new_fn = r'''function updateFlagPositions(){
  for(const m of marbles){
    if(m.userData.eliminated){
      if(m.userData.flagSprite) m.userData.flagSprite.visible = false;
      continue;
    }
    const emoji = playerFlags[m.userData.id] || ALL_FLAGS[m.userData.id % ALL_FLAGS.length];
    if(!m.userData.flagSprite || m.userData.flagSprite.userData.emoji !== emoji){
      if(m.userData.flagSprite){
        scene.remove(m.userData.flagSprite);
        try{ m.userData.flagSprite.material.map.dispose(); }catch(e){}
        try{ m.userData.flagSprite.material.dispose(); }catch(e){}
        m.userData.flagSprite = null;
      }
      const mat = new THREE.SpriteMaterial({
        map: createFlagTexture(emoji),
        transparent: true,
        depthTest: true,
        depthWrite: false
      });
      const sp = new THREE.Sprite(mat);
      sp.scale.set(1.8, 1.35, 1);
      sp.userData.emoji = emoji;
      scene.add(sp);
      m.userData.flagSprite = sp;
    }
    const sp = m.userData.flagSprite;
    sp.visible = true;
    // posisi LEBIH TINGGI biar tidak nutup marble
    sp.position.set(m.position.x, m.position.y + 5.5, m.position.z);
  }
}
'''

# Replace function updateFlagPositions yang ada
pattern = r"function updateFlagPositions\(\)\s*\{[\s\S]*?\n\}"
if re.search(pattern, html):
    html = re.sub(pattern, new_fn.strip(), html, count=1)
    print("updateFlagPositions diganti (bersih + tinggi)")
else:
    print("WARNING: function tidak ketemu")

# 3. Pastikan tinggi juga kalau ada hardcode lama
html = html.replace("m.position.y+4.2", "m.position.y+5.5")
html = html.replace("m.position.y + 4.2", "m.position.y + 5.5")
html = html.replace("m.position.y+3.8", "m.position.y+5.5")
html = html.replace("m.position.y + 3.8", "m.position.y + 5.5")
html = html.replace("m.position.y+2.7", "m.position.y+5.5")

# 4. Perkecil scale kalau masih besar
html = html.replace("sp.scale.set(2.0,1.5,1)", "sp.scale.set(1.8,1.35,1)")
html = html.replace("sp.scale.set(2.2,1.65,1)", "sp.scale.set(1.8,1.35,1)")
html = html.replace("sp.scale.set(2.6,1.95,1)", "sp.scale.set(1.8,1.35,1)")

p.write_text(html, encoding="utf-8")
print("SELESAI - refresh browser")
