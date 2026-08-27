from pathlib import Path

p = Path("index.html")
s = p.read_text()

start = s.find("function steer(m){")
end = s.find("function startRound(){", start)

if start == -1:
    raise SystemExit("ERROR: function steer(m) tidak ditemukan")

if end == -1:
    raise SystemExit("ERROR: function startRound() tidak ditemukan")

new_steer = r'''function steer(m){
  if(m.userData.finished) return;

  const r = RADIUS;
  const speed = 0.105 + m.userData.id * 0.012;

  /*
   * WALL FOLLOWING
   *
   * Marble tidak lagi mencari exit secara acak.
   *
   * 1. Jika tidak ada dinding:
   *    terus berjalan dengan arah terakhir.
   *
   * 2. Jika menemukan dinding:
   *    bergerak sejajar mengikuti dinding.
   *
   * 3. Saat dinding berakhir:
   *    tetap lanjut ke arah gerak terakhir.
   */

  let nearest = null;
  let nearestDist = Infinity;

  for(const w of walls){

    const qx = Math.max(
      w.x - w.hw,
      Math.min(m.position.x,w.x + w.hw)
    );

    const qz = Math.max(
      w.z - w.hd,
      Math.min(m.position.z,w.z + w.hd)
    );

    const dx = m.position.x - qx;
    const dz = m.position.z - qz;
    const dist = Math.hypot(dx,dz);

    if(dist < nearestDist){
      nearestDist = dist;
      nearest = w;
    }
  }

  /*
   * MASIH JAUH DARI DINDING
   *
   * Jangan belok.
   * Jangan mencari jalan.
   */
  if(!nearest || nearestDist > r + 0.45){

    let vx = m.userData.vx;
    let vz = m.userData.vz;

    let sp = Math.hypot(vx,vz);

    if(sp < 0.025){

      // Hanya fallback kalau marble benar-benar berhenti.
      const angle =
        (m.userData.id / 4) * Math.PI * 2 + 0.8;

      vx = Math.cos(angle);
      vz = Math.sin(angle);

      sp = 1;
    }

    m.userData.vx = vx / sp * speed;
    m.userData.vz = vz / sp * speed;

    return;
  }

  /*
   * ADA DINDING DI DEKAT MARBLE
   *
   * Jadikan dinding sebagai "rel".
   */
  const horizontal = nearest.w > nearest.d;

  let tx;
  let tz;

  if(horizontal){
    tx = 1;
    tz = 0;
  }else{
    tx = 0;
    tz = 1;
  }

  /*
   * Jangan tiba-tiba berbalik.
   * Pertahankan arah gerak sebelumnya.
   */
  const oldVx = m.userData.vx;
  const oldVz = m.userData.vz;

  if(
    oldVx * tx +
    oldVz * tz < 0
  ){
    tx = -tx;
    tz = -tz;
  }

  /*
   * Dorongan kecil menuju permukaan dinding.
   * Ini membuat marble benar-benar menempel
   * dan merambat sepanjang dinding.
   */
  let nx = 0;
  let nz = 0;

  if(horizontal){

    nz =
      m.position.z < nearest.z
      ? 1
      : -1;

  }else{

    nx =
      m.position.x < nearest.x
      ? 1
      : -1;
  }

  const follow = 0.012;

  m.userData.vx =
    tx * speed +
    nx * follow;

  m.userData.vz =
    tz * speed +
    nz * follow;
}

'''

s = s[:start] + new_steer + s[end:]

p.write_text(s)

print("PATCH BERHASIL")
print("Hanya function steer() yang diganti.")
