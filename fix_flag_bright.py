import pathlib, re

p = pathlib.Path("index.html")
html = p.read_text(encoding="utf-8")

new_tex = r'''function createFlagTexture(emoji){
  const c=document.createElement("canvas");
  c.width=512; c.height=384;
  const g=c.getContext("2d");
  g.clearRect(0,0,512,384);

  // glow putih seragam biar semua bendera sama terang
  const grd=g.createRadialGradient(256,192,20,256,192,170);
  grd.addColorStop(0,"rgba(255,255,255,0.95)");
  grd.addColorStop(0.45,"rgba(255,255,255,0.55)");
  grd.addColorStop(1,"rgba(255,255,255,0)");
  g.fillStyle=grd;
  g.beginPath();
  g.arc(256,192,170,0,Math.PI*2);
  g.fill();

  // bendera (besar & tajam)
  g.font="260px serif";
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
    print("createFlagTexture diganti (brightness seragam)")
else:
    print("WARNING: createFlagTexture tidak ketemu")

p.write_text(html, encoding="utf-8")
print("SELESAI - refresh browser")
