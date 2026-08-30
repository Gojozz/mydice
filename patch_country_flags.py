from pathlib import Path

p = Path("index.html")
s = p.read_text()

marker = "const marbles=[];"

if "const COUNTRY_FLAGS =" in s:
    print("FLAG SYSTEM SUDAH ADA - tidak dipasang ulang.")
    raise SystemExit

if marker not in s:
    raise SystemExit("ERROR: const marbles=[] tidak ditemukan.")

code = r'''
// ===== 3D RANDOM COUNTRY FLAGS =====
const COUNTRY_FLAGS = [
  ["ID","Indonesia"],["JP","Japan"],["US","United States"],
  ["BR","Brazil"],["GB","United Kingdom"],["FR","France"],
  ["DE","Germany"],["IT","Italy"],["ES","Spain"],
  ["PT","Portugal"],["NL","Netherlands"],["BE","Belgium"],
  ["CH","Switzerland"],["SE","Sweden"],["NO","Norway"],
  ["DK","Denmark"],["FI","Finland"],["PL","Poland"],
  ["GR","Greece"],["TR","Turkey"],["RU","Russia"],
  ["UA","Ukraine"],["IN","India"],["CN","China"],
  ["KR","South Korea"],["TH","Thailand"],["VN","Vietnam"],
  ["PH","Philippines"],["MY","Malaysia"],["SG","Singapore"],
  ["AU","Australia"],["NZ","New Zealand"],["CA","Canada"],
  ["MX","Mexico"],["AR","Argentina"],["CL","Chile"],
  ["CO","Colombia"],["PE","Peru"],["ZA","South Africa"],
  ["EG","Egypt"],["NG","Nigeria"],["KE","Kenya"],
  ["MA","Morocco"],["SA","Saudi Arabia"],
  ["AE","United Arab Emirates"],["IL","Israel"],
  ["PK","Pakistan"],["BD","Bangladesh"],["LK","Sri Lanka"]
];

const FLAG_COLORS = {
  ID:["#e31b23","#ffffff"],
  JP:["#ffffff","#bc002d"],
  US:["#b22234","#3c3b6e"],
  BR:["#009c3b","#ffdf00"],
  GB:["#012169","#c8102e"],
  FR:["#0055a4","#ef4135"],
  DE:["#000000","#dd0000"],
  IT:["#009246","#ce2b37"],
  ES:["#aa151b","#f1bf00"],
  PT:["#046a38","#da291c"],
  NL:["#ae1c28","#21468b"],
  BE:["#000000","#ed2939"],
  CH:["#d52b1e","#ffffff"],
  SE:["#006aa7","#fecc00"],
  NO:["#ba0c2f","#00205b"],
  DK:["#c8102e","#ffffff"],
  FI:["#ffffff","#003580"],
  PL:["#ffffff","#dc143c"],
  GR:["#0d5eaf","#ffffff"],
  TR:["#e30a17","#ffffff"],
  RU:["#ffffff","#0039a6"],
  UA:["#0057b7","#ffd700"],
  IN:["#ff9933","#138808"],
  CN:["#de2910","#ffde00"],
  KR:["#ffffff","#cd2e3a"],
  TH:["#a51931","#2d2a4a"],
  VN:["#da251d","#ffde00"],
  PH:["#0038a8","#ce1126"],
  MY:["#010066","#cc0001"],
  SG:["#ed2939","#ffffff"],
  AU:["#002868","#ffffff"],
  NZ:["#00247d","#cc142b"],
  CA:["#d80621","#ffffff"],
  MX:["#006847","#ce1126"],
  AR:["#74acdf","#f6b40e"],
  CL:["#0039a6","#d52b1e"],
  CO:["#fcd116","#ce1126"],
  PE:["#d91023","#ffffff"],
  ZA:["#007749","#ffb81c"],
  EG:["#ce1126","#000000"],
  NG:["#008751","#ffffff"],
  KE:["#006600","#bb1e10"],
  MA:["#c1272d","#006233"],
  SA:["#006c35","#ffffff"],
  AE:["#00732f","#000000"],
  IL:["#ffffff","#0038b8"],
  PK:["#01411c","#ffffff"],
  BD:["#006a4e","#f42a41"],
  LK:["#8d153a","#ffb81c"]
};

function createCountryFlag(code,name){
  const colors=FLAG_COLORS[code] || ["#555555","#eeeeee"];

  const canvas=document.createElement("canvas");
  canvas.width=320;
  canvas.height=200;

  const ctx=canvas.getContext("2d");

  ctx.fillStyle=colors[0];
  ctx.fillRect(0,0,320,200);

  // Pola dasar yang berbeda agar setiap negara tetap terlihat
  if(["ID","PL"].includes(code)){
    ctx.fillStyle=code==="ID" ? "#ffffff" : "#dc143c";
    ctx.fillRect(0,100,320,100);
  }
  else if(["DE","RU","TH","NL","AR"].includes(code)){
    ctx.fillStyle=colors[1];
    ctx.fillRect(0,70,320,60);
  }
  else if(["FR","IT","BE","NG","CA","MX","PE"].includes(code)){
    ctx.fillStyle="#ffffff";
    ctx.fillRect(106,0,108,200);
  }
  else if(code==="UA"){
    ctx.fillStyle="#ffd700";
    ctx.fillRect(0,100,320,100);
  }
  else if(code==="IN"){
    ctx.fillStyle="#ffffff";
    ctx.fillRect(0,67,320,66);
    ctx.fillStyle="#138808";
    ctx.fillRect(0,133,320,67);
    ctx.fillStyle="#000080";
    ctx.beginPath();
    ctx.arc(160,100,22,0,Math.PI*2);
    ctx.strokeStyle="#000080";
    ctx.lineWidth=4;
    ctx.stroke();
  }
  else if(code==="JP"){
    ctx.fillStyle="#bc002d";
    ctx.beginPath();
    ctx.arc(160,100,52,0,Math.PI*2);
    ctx.fill();
  }
  else if(code==="TR"){
    ctx.fillStyle="#ffffff";
    ctx.beginPath();
    ctx.arc(135,100,52,0,Math.PI*2);
    ctx.fill();
    ctx.fillStyle="#e30a17";
    ctx.beginPath();
    ctx.arc(153,100,42,0,Math.PI*2);
    ctx.fill();
  }
  else if(code==="CN"){
    ctx.fillStyle="#ffde00";
    ctx.font="90px sans-serif";
    ctx.textAlign="center";
    ctx.textBaseline="middle";
    ctx.fillText("★",70,65);
  }
  else if(code==="BR"){
    ctx.fillStyle="#ffdf00";
    ctx.beginPath();
    ctx.moveTo(160,20);
    ctx.lineTo(300,100);
    ctx.lineTo(160,180);
    ctx.lineTo(20,100);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle="#002776";
    ctx.beginPath();
    ctx.arc(160,100,48,0,Math.PI*2);
    ctx.fill();
  }
  else if(code==="CH"){
    ctx.fillStyle="#ffffff";
    ctx.fillRect(130,45,60,110);
    ctx.fillRect(95,80,130,40);
  }
  else if(code==="GB"){
    ctx.strokeStyle="#ffffff";
    ctx.lineWidth=35;
    ctx.beginPath();
    ctx.moveTo(0,0);ctx.lineTo(320,200);
    ctx.moveTo(320,0);ctx.lineTo(0,200);
    ctx.stroke();

    ctx.strokeStyle="#c8102e";
    ctx.lineWidth=16;
    ctx.beginPath();
    ctx.moveTo(0,0);ctx.lineTo(320,200);
    ctx.moveTo(320,0);ctx.lineTo(0,200);
    ctx.stroke();

    ctx.strokeStyle="#ffffff";
    ctx.lineWidth=50;
    ctx.beginPath();
    ctx.moveTo(160,0);ctx.lineTo(160,200);
    ctx.moveTo(0,100);ctx.lineTo(320,100);
    ctx.stroke();

    ctx.strokeStyle="#c8102e";
    ctx.lineWidth=28;
    ctx.beginPath();
    ctx.moveTo(160,0);ctx.lineTo(160,200);
    ctx.moveTo(0,100);ctx.lineTo(320,100);
    ctx.stroke();
  }
  else if(code==="ZA"){
    ctx.fillStyle="#ffb81c";
    ctx.beginPath();
    ctx.moveTo(0,25);ctx.lineTo(145,100);ctx.lineTo(0,175);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle="#d21034";
    ctx.beginPath();
    ctx.moveTo(0,45);ctx.lineTo(110,100);ctx.lineTo(0,155);
    ctx.closePath();
    ctx.fill();
  }
  else if(code==="SA"){
    ctx.fillStyle="#ffffff";
    ctx.fillRect(55,100,210,8);
  }
  else if(code==="AE"){
    ctx.fillStyle="#ff0000";
    ctx.fillRect(0,0,80,200);
    ctx.fillStyle="#ffffff";
    ctx.fillRect(80,67,240,66);
    ctx.fillStyle="#000000";
    ctx.fillRect(80,133,240,67);
  }
  else if(code==="IL"){
    ctx.fillStyle="#0038b8";
    ctx.fillRect(0,25,320,30);
    ctx.fillRect(0,145,320,30);
  }
  else if(code==="BD"){
    ctx.fillStyle="#f42a41";
    ctx.beginPath();
    ctx.arc(145,100,55,0,Math.PI*2);
    ctx.fill();
  }
  else if(code==="PK"){
    ctx.fillStyle="#ffffff";
    ctx.fillRect(0,0,70,200);
  }
  else if(code==="LK"){
    ctx.fillStyle="#ffb81c";
    ctx.fillRect(0,0,20,200);
  }

  const texture=new THREE.CanvasTexture(canvas);
  texture.colorSpace=THREE.SRGBColorSpace;
  texture.minFilter=THREE.LinearFilter;
  texture.magFilter=THREE.LinearFilter;

  const material=new THREE.SpriteMaterial({
    map:texture,
    transparent:true,
    depthTest:false,
    depthWrite:false
  });

  const sprite=new THREE.Sprite(material);

  // Kiri-atas, bukan tepat di atas marble
  sprite.position.set(-1.45,1.45,0);

  // Ukuran 3D: ikut zoom kamera
  sprite.scale.set(2.0,1.25,1);

  sprite.renderOrder=20;
  sprite.userData.countryCode=code;
  sprite.userData.countryName=name;

  return sprite;
}

function removeCountryFlag(m){
  const sprite=m && m.userData ? m.userData.countryFlag : null;
  if(!sprite) return;

  m.remove(sprite);

  if(sprite.material){
    if(sprite.material.map) sprite.material.map.dispose();
    sprite.material.dispose();
  }

  m.userData.countryFlag=null;
}

function assignRandomCountry(m){
  removeCountryFlag(m);

  const c=COUNTRY_FLAGS[
    Math.floor(Math.random()*COUNTRY_FLAGS.length)
  ];

  const sprite=createCountryFlag(c[0],c[1]);

  m.add(sprite);

  m.userData.countryCode=c[0];
  m.userData.countryName=c[1];
  m.userData.countryFlag=sprite;
}

'''

s=s.replace(marker,code+"\n"+marker,1)

# Tambahkan ke makeMarble setelah root.userData dibuat
needle="""root.userData={id, cloneId, vx:0, vz:0, finished:false, eliminated:false, isTeleporting:false, teleportPhase: 'none', crowdTime: 0, isCrowding: false, boostCooldown: 0};"""

if needle not in s:
    raise SystemExit("ERROR: makeMarble userData tidak ditemukan.")

replacement=needle+"\n  assignRandomCountry(root);"
s=s.replace(needle,replacement,1)

# Reset: hapus flag sebelum marble dibuang
needle2="""function resetMarbles(){
  while(marbles.length){scene.remove(marbles.pop());}
  activeTargetMarble = null;"""

replacement2="""function resetMarbles(){
  while(marbles.length){
    const oldMarble=marbles.pop();
    removeCountryFlag(oldMarble);
    scene.remove(oldMarble);
  }
  activeTargetMarble = null;"""

if needle2 not in s:
    raise SystemExit("ERROR: resetMarbles tidak ditemukan.")

s=s.replace(needle2,replacement2,1)

p.write_text(s)
print("OK: sistem bendera 3D berhasil dipasang.")
