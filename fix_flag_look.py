import pathlib, re

p = pathlib.Path("index.html")
html = p.read_text(encoding="utf-8")

# Ganti createFlagTexture: tanpa outline, emoji lebih besar & tajam
new_tex = r'''function createFlagTexture(emoji){
  const c=document.createElement("canvas");
  c.width=512; c.height=384;
  const g=c.getContext("2d");
  // background transparan (tanpa kotak / outline)
  g.clearRect(0,0,512,384);
  // emoji besar & tajam
  g.font="280px serif";
  g.textAlign="center";
  g.textBaseline="middle";
  g.fillText(emoji||"🏳️", 256, 200);
  const t=new THREE.CanvasTexture(c);
  t.needsUpdate=true;
  t.minFilter=THREE.LinearFilter;
  t.magFilter=THREE.LinearFilter;
  return t;
}'''

pattern = r"function createFlagTexture\s*\(\s*emoji\s*\)\s*\{[\s\S]*?\n\}"
if re.search(pattern, html):
    html = re.sub(pattern, new_tex.strip(), html, count=1)
    print("createFlagTexture diganti")
else:
    print("WARNING: createFlagTexture tidak ketemu")

# Perbesar sprite flag
html = html.replace("sp.scale.set(1.8,1.35,1)", "sp.scale.set(3.2,2.4,1)")
html = html.replace("sp.scale.set(1.8, 1.35, 1)", "sp.scale.set(3.2, 2.4, 1)")
html = html.replace("sp.scale.set(2.0,1.5,1)", "sp.scale.set(3.2,2.4,1)")
html = html.replace("sp.scale.set(2.2,1.65,1)", "sp.scale.set(3.2,2.4,1)")

# Naikkan sedikit biar proporsi pas dengan ukuran baru
html = html.replace("m.position.y + 5.5", "m.position.y + 6.2")
html = html.replace("m.position.y+5.5", "m.position.y+6.2")

p.write_text(html, encoding="utf-8")
print("SELESAI")
