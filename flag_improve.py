import pathlib, re

p = pathlib.Path("index.html")
html = p.read_text(encoding="utf-8")

# --- 1) Mapping emoji -> nama negara ---
country_map_js = r'''
const FLAG_COUNTRY = {
  "🇮🇩":"Indonesia","🇯🇵":"Jepang","🇰🇷":"Korea","🇧🇷":"Brazil","🇺🇸":"Amerika",
  "🇫🇷":"Prancis","🇩🇪":"Jerman","🇹🇷":"Turki","🇮🇳":"India","🇹🇭":"Thailand",
  "🇻🇳":"Vietnam","🇵🇭":"Filipina","🇲🇾":"Malaysia","🇸🇬":"Singapura","🇦🇷":"Argentina",
  "🇬🇧":"Inggris","🇨🇳":"China","🇮🇹":"Italia","🇪🇸":"Spanyol","🇳🇱":"Belanda",
  "🇨🇦":"Kanada","🇦🇺":"Australia","🇸🇦":"Saudi","🇵🇸":"Palestina","🇪🇬":"Mesir"
};
const ALL_FLAGS = Object.keys(FLAG_COUNTRY);
function countryName(flag){ return FLAG_COUNTRY[flag] || "Negara"; }
function randomFlags(n){
  const pool=[...ALL_FLAGS].sort(()=>Math.random()-0.5);
  return pool.slice(0,n);
}
'''

# Sisipkan setelah DEFAULT_FLAGS jika belum ada
if "FLAG_COUNTRY" not in html:
    if "const DEFAULT_FLAGS=" in html or "const DEFAULT_FLAGS =" in html:
        # sisip setelah baris DEFAULT_FLAGS
        html = re.sub(
            r"(const DEFAULT_FLAGS\s*=\s*\[[^\]]+\];)",
            r"\1\n" + country_map_js,
            html,
            count=1
        )
        print("FLAG_COUNTRY ditambahkan")
    else:
        # fallback
        html = html.replace(
            "let playerFlags=",
            country_map_js + "\nlet playerFlags="
        )
        print("FLAG_COUNTRY ditambahkan (fallback)")

# --- 2) Acak bendera tiap sesi + nama negara ---
# Ganti inisialisasi playerFlags & playerNames
if "randomFlags(4)" not in html:
    html = re.sub(
        r"let playerFlags\s*=\s*\[[^\]]+\];\s*\n\s*let playerNames\s*=\s*\[[^\]]+\];",
        "let playerFlags = randomFlags(4);\nlet playerNames = playerFlags.map(f => countryName(f));",
        html,
        count=1
    )
    # alternatif pola
    if "randomFlags(4)" not in html:
        html = html.replace(
            "let playerFlags=[...DEFAULT_FLAGS].sort(()=>Math.random()-0.5).slice(0,4);",
            "let playerFlags=randomFlags(4);"
        )
        html = html.replace(
            "let playerNames=[...NAMES];",
            "let playerNames=playerFlags.map(f=>countryName(f));"
        )
    print("Random flag + nama negara diset")

# --- 3) Naikkan posisi bendera (tidak nutup marble) ---
html = html.replace(
    "sp.position.set(m.position.x, m.position.y+2.7, m.position.z);",
    "sp.position.set(m.position.x, m.position.y+3.8, m.position.z);"
)
html = html.replace(
    "sp.position.set(m.position.x, m.position.y + 2.7, m.position.z);",
    "sp.position.set(m.position.x, m.position.y + 3.8, m.position.z);"
)
# perkecil sedikit biar tidak terlalu besar
html = html.replace("sp.scale.set(2.6,1.95,1);", "sp.scale.set(2.2,1.65,1);")
print("Posisi bendera dinaikkan")

# --- 4) Bendera ikut klon ---
# Ubah updateFlagPositions agar SEMUA marble (termasuk klon) punya flag
# Versi baru: map sprite per marble object, bukan per id saja

new_update = r'''
function updateFlagPositions(){
  // pastikan setiap marble hidup punya sprite flag
  for(const m of marbles){
    if(m.userData.eliminated){
      if(m.userData.flagSprite){ m.userData.flagSprite.visible=false; }
      continue;
    }
    const id=m.userData.id;
    const emoji=playerFlags[id]||ALL_FLAGS[id%ALL_FLAGS.length];
    // buat sprite sendiri per marble (termasuk klon)
    if(!m.userData.flagSprite || m.userData.flagSprite.userData.emoji!==emoji){
      if(m.userData.flagSprite){
        scene.remove(m.userData.flagSprite);
        try{m.userData.flagSprite.material.map.dispose();}catch(e){}
        try{m.userData.flagSprite.material.dispose();}catch(e){}
      }
      const mat=new THREE.SpriteMaterial({map:createFlagTexture(emoji),transparent:true,depthTest:true,depthWrite:false});
      const sp=new THREE.Sprite(mat);
      sp.scale.set(2.0,1.5,1);
      sp.userData.emoji=emoji;
      scene.add(sp);
      m.userData.flagSprite=sp;
    }
    const sp=m.userData.flagSprite;
    sp.visible=true;
    sp.position.set(m.position.x, m.position.y+3.8, m.position.z);
  }
}
'''

# Ganti function updateFlagPositions yang lama
pattern = r"function updateFlagPositions\(\)\{[\s\S]*?\n\}"
if re.search(pattern, html):
    html = re.sub(pattern, new_update.strip(), html, count=1)
    print("updateFlagPositions diganti (dukung klon)")
else:
    print("Peringatan: updateFlagPositions lama tidak ketemu exact")

# --- 5) setMarbleFlag update nama negara ---
old_set = "function setMarbleFlag(id,emoji,name){if(id>=0&&id<4){playerFlags[id]=emoji;if(name)playerNames[id]=name;if(typeof ensureFlagSprite==='function')ensureFlagSprite(id,emoji);updateUI();}}"
new_set = "function setMarbleFlag(id,emoji,name){if(id>=0&&id<4){playerFlags[id]=emoji;playerNames[id]=name||countryName(emoji);updateUI();}}"
if old_set in html:
    html = html.replace(old_set, new_set)
else:
    # pola lain
    html = re.sub(
        r"function setMarbleFlag\(id,emoji,name\)\{[^}]+\}",
        "function setMarbleFlag(id,emoji,name){if(id>=0&&id<4){playerFlags[id]=emoji;playerNames[id]=name||countryName(emoji);updateUI();}}",
        html,
        count=1
    )
print("setMarbleFlag update nama negara")

# --- 6) UI label pakai nama negara ---
# pastikan label memakai playerNames (yang sekarang nama negara)
if "playerNames[r.i]" not in html and "base=playerNames" not in html:
    html = html.replace(
        "const label = r.m.userData.cloneId > 0 ? `${NAMES[r.i]} (Klon ${r.m.userData.cloneId})` : NAMES[r.i];",
        "const flag=playerFlags[r.i]||'🏳️'; const base=playerNames[r.i]||NAMES[r.i];\n"
        "      const label = r.m.userData.cloneId > 0 ? `${flag} ${base} (Klon \( {r.m.userData.cloneId})` : ` \){flag} ${base}`;"
    )

# --- 7) Saat startRound / reset, acak ulang bendera ---
if "playerFlags = randomFlags(4)" not in html and "function startRound" in html:
    html = html.replace(
        "function startRound(){",
        "function startRound(){\n  playerFlags = randomFlags(4);\n  playerNames = playerFlags.map(f => countryName(f));\n"
    )
    print("Random flag tiap ronde")

p.write_text(html, encoding="utf-8")
print("=== SELESAI ===")
