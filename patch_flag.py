import pathlib, re

p = pathlib.Path("bot.py")
bot = p.read_text(encoding="utf-8")

country_map = '''
COUNTRY_FLAGS = {
    "indonesia": "🇮🇩", "indo": "🇮🇩", "ri": "🇮🇩",
    "malaysia": "🇲🇾", "singapore": "🇸🇬", "singapura": "🇸🇬",
    "thailand": "🇹🇭", "vietnam": "🇻🇳", "filipina": "🇵🇭", "philippines": "🇵🇭",
    "jepang": "🇯🇵", "japan": "🇯🇵", "korea": "🇰🇷", "china": "🇨🇳", "cina": "🇨🇳",
    "india": "🇮🇳", "turki": "🇹🇷", "turkey": "🇹🇷",
    "inggris": "🇬🇧", "uk": "🇬🇧", "prancis": "🇫🇷", "france": "🇫🇷",
    "jerman": "🇩🇪", "germany": "🇩🇪", "italia": "🇮🇹", "italy": "🇮🇹",
    "spanyol": "🇪🇸", "spain": "🇪🇸", "belanda": "🇳🇱", "netherlands": "🇳🇱",
    "amerika": "🇺🇸", "usa": "🇺🇸", "us": "🇺🇸", "kanada": "🇨🇦", "canada": "🇨🇦",
    "brazil": "🇧🇷", "brasil": "🇧🇷", "argentina": "🇦🇷",
    "australia": "🇦🇺", "mesir": "🇪🇬", "egypt": "🇪🇬",
    "arab saudi": "🇸🇦", "saudi": "🇸🇦", "palestina": "🇵🇸", "palestine": "🇵🇸",
}
DEFAULT_FLAGS = ["🇮🇩","🇯🇵","🇰🇷","🇧🇷","🇺🇸","🇫🇷","🇩🇪","🇹🇷","🇮🇳","🇹🇭"]

def resolve_country(text):
    t = str(text or "").lower().strip()
    t = re.sub(r"[^a-z0-9\\s]", "", t)
    t = re.sub(r"\\s+", " ", t).strip()
    if not t: return None
    if t in COUNTRY_FLAGS: return t, COUNTRY_FLAGS[t]
    for k, v in COUNTRY_FLAGS.items():
        if k in t or t in k: return k, v
    return None
'''

if "COUNTRY_FLAGS" not in bot:
    bot = bot.replace("MAX_PLAYERS = 4\\n", "MAX_PLAYERS = 4\\n" + country_map + "\\n")

old = '''    player = {
        "user": user,
        "name": user,
        "joinedAt": time.time(),
        "control": None,
        "controlAt": 0,
        "controlId": 0
    }'''

new = '''    player = {
        "user": user,
        "name": user,
        "joinedAt": time.time(),
        "control": None,
        "controlAt": 0,
        "controlId": 0,
        "flag": random.choice(DEFAULT_FLAGS),
        "country": "random"
    }'''

if old in bot:
    bot = bot.replace(old, new)

flag_code = '''
            country_hit = resolve_country(msg)
            if country_hit:
                cname, cflag = country_hit
                player = next((p for p in state["active"] if str(p.get("user","")).lower()==user.lower()), None)
                if player:
                    player["flag"] = cflag
                    player["country"] = cname
                    save_state(state)
                    print(f"[FLAG] {user} -> {cname} {cflag}")
                    speak(f"{user} ganti bendera jadi {cname}!")
                else:
                    speak(f"{user} ketik join dulu baru bisa ganti bendera!")
                continue
'''

if "[FLAG]" not in bot and "resolve_country(msg)" not in bot:
    bot = bot.replace("            if raw_msg:\\n", flag_code + "\\n            if raw_msg:\\n")

bot = bot.replace('"POST, OPTIONS"', '"GET, POST, OPTIONS"')

old2 = '''    def do_OPTIONS(self):

        self.send_response(204)

        self.send_cors_headers()

        self.end_headers()

    def do_POST(self):'''

new2 = '''    def do_OPTIONS(self):

        self.send_response(204)

        self.send_cors_headers()

        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/state"):
            try:
                state = load_state()
                body = json.dumps(state, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                err = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(err)
            return
        self.send_response(404)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):'''

if "def do_GET" not in bot and old2 in bot:
    bot = bot.replace(old2, new2)

p.write_text(bot, encoding="utf-8")
print("SUKSES patch bot.py")
