
def fetch_live_id_via_https(channel_id):
    if not channel_id:
        print("[AUTO LIVE ERROR] CHANNEL_ID tidak ditemukan!")
        return None
    url = f"https://www.youtube.com/channel/{channel_id}/live"
    print(f"[AUTO LIVE] Memeriksa stream live di: {url}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        with httpx.Client(follow_redirects=True, timeout=15.0, headers=headers) as client:
            resp = client.get(url)
            m = re.search(r"v=([a-zA-Z0-9_-]{11})", str(resp.url))
            if m:
                print(f"[AUTO LIVE SUCCESS] Video ID ditemukan: {m.group(1)}")
                return m.group(1)
            m_html = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
            if m_html:
                print(f"[AUTO LIVE SUCCESS] Video ID ditemukan (HTML): {m_html.group(1)}")
                return m_html.group(1)
    except Exception as e:
        print(f"[AUTO LIVE ERROR] Gagal request HTTP: {e}")
    return None



def get_live_video_id(channel_id=None):
    env_id = os.environ.get("YOUTUBE_LIVE_ID", "").strip()
    if env_id:
        print(f"[AUTO LIVE] Menggunakan YOUTUBE_LIVE_ID dari Secret: {env_id}")
        return env_id

    cid = channel_id or os.environ.get("YOUTUBE_CHANNEL_ID", "").strip()
    if not cid:
        print("[AUTO LIVE ERROR] YOUTUBE_CHANNEL_ID tidak ditemukan.")
        return None

    url = f"https://www.youtube.com/channel/{cid}/live"
    print(f"[AUTO LIVE] Mencari Live ID otomatis untuk Channel: {cid}...")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        with httpx.Client(follow_redirects=True, timeout=15.0, headers=headers) as client:
            resp = client.get(url)
            match = re.search(r"v=([a-zA-Z0-9_-]{11})", str(resp.url))
            if match:
                video_id = match.group(1)
                print(f"[AUTO LIVE SUCCESS] Live ID ditemukan dari redirect: {video_id}")
                return video_id

            match_html = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
            if match_html:
                video_id = match_html.group(1)
                print(f"[AUTO LIVE SUCCESS] Live ID ditemukan dari HTML: {video_id}")
                return video_id
    except Exception as e:
        print(f"[AUTO LIVE ERROR] Gagal deteksi otomatis: {e}")

    return None


import pytchat
import time
import os
import json
import tempfile
import threading
import re
import subprocess
import random
import queue
import httpx

from urllib.parse import quote
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from googleapiclient.discovery import build
# =========================================================
# PATCH pytchat — ambil channel ID lewat oEmbed
# =========================================================

import pytchat.util as pytchat_util
from pytchat.exceptions import InvalidVideoIdException


def _get_channelid_via_oembed(video_id: str):
    url = (
        "https://www.youtube.com/oembed?"
        f"url=https://www.youtube.com/watch?v={quote(video_id)}&format=json"
    )

    try:
        with httpx.Client(
            timeout=12,
            headers={
                "User-Agent":
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }
        ) as client:

            r = client.get(url)

            if r.status_code != 200:
                print(f"[PATCH] oEmbed status: {r.status_code}")
                return None

            data = r.json()
            author_url = data.get("author_url", "")

            print(f"[PATCH] author_url: {author_url}")

            m = re.search(
                r"/channel/(UC[0-9A-Za-z_-]{22})",
                author_url
            )

            if m:
                return m.group(1)

            if "/@" in author_url:
                r2 = client.get(author_url, follow_redirects=True)

                m2 = re.search(
                    r'"externalId":"(UC[0-9A-Za-z_-]{22})"',
                    r2.text
                )

                if m2:
                    return m2.group(1)

                m3 = re.search(
                    r'"channelId":"(UC[0-9A-Za-z_-]{22})"',
                    r2.text
                )

                if m3:
                    return m3.group(1)

    except Exception as e:
        print(f"[PATCH] oEmbed gagal: {e}")

    return None


def robust_get_channelid(client, video_id):

    uc = _get_channelid_via_oembed(video_id)

    if uc:
        print(f"[PATCH] Channel ID dari oEmbed: {uc}")
        return uc

    print("[PATCH] oEmbed gagal, coba cara lama pytchat...")

    try:
        return pytchat_util.get_channelid_2nd(client, video_id)

    except Exception as e:
        print(f"[PATCH] Cara lama juga gagal: {e}")

        raise InvalidVideoIdException(
            f"Cannot find channel id for video id:{video_id}."
        )


pytchat_util.get_channelid = robust_get_channelid

print("[PATCH] pytchat get_channelid sudah di-patch (oEmbed)")


# =========================================================
# KONFIGURASI
# =========================================================

CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID", "").strip()
VIDEO_ID = ""  # deteksi di start_bot() setelah stream sempat live
API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID", "").strip()

STATE_FILE = Path("chat_state.json")

MAX_PLAYERS = 4
ROTATION_PORT = 8765

last_processed_race = None


# =========================================================
# TTS
# =========================================================

PIPER_BIN = os.environ.get("PIPER_BIN", "piper")
PIPER_MODEL = os.environ.get(
    "PIPER_MODEL",
    "models/en_US-lessac-medium.onnx"
)

tts_queue = queue.Queue()
tts_lock = threading.Lock()
last_tts_time = 0.0

CHAT_COOLDOWN = 4.0
last_chat_response = {}

ENGAGEMENT_INTERVAL = 90
last_engagement_time = time.time() - 10000
engagement_index = 0

ENGAGE_PROMOS = [
    "If you enjoy the marble maze, please like the stream!",
    "Don't forget to subscribe for more marble maze action!",
    "Enjoying the game? Leave a comment and tell us your favorite country!",
    "Hit like if you want to see more marble maze battles!",
    "Subscribe and stay tuned for the next marble maze!",
    "Tell us where you are watching from in the comments!",
    "Like, subscribe, and leave a comment to support the game!",
    "Which country are you cheering for? Tell us in the comments!",
    "If you are enjoying the maze, show some love with a like!",
    "Subscribe so you don't miss the next marble maze!",
]


def clean_tts_text(text):
    if not text:
        return ""
    text = str(text).strip()
    text = re.sub(r"[^\w\s\.,!?\-']", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def run_piper(text):
    text = clean_tts_text(text)

    if not text:
        return False

    model_path = Path(PIPER_MODEL)

    if not model_path.exists():
        print(f"[TTS ERROR] Model not found: {model_path}")
        return False

    wav_path = Path(
        tempfile.mktemp(
            prefix="luna_",
            suffix=".wav"
        )
    )

    try:
        print(f"[TTS] {text}")
        print(f"[TTS] model={model_path}")
        print(
            f"[TTS] PULSE_SINK="
            f"{os.environ.get('PULSE_SINK', '')}"
        )

        process = subprocess.run(
            [
                PIPER_BIN,
                "--model",
                str(model_path),
                "--output_file",
                str(wav_path)
            ],
            input=(text + "\n").encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )

        if process.returncode != 0:
            print(
                "[TTS ERROR]",
                process.stderr.decode(
                    "utf-8",
                    errors="replace"
                )[-1000:]
            )
            return False

        if not wav_path.exists() or wav_path.stat().st_size < 100:
            print("[TTS ERROR] WAV file missing or empty")
            return False

        print(
            f"[TTS] WAV size={wav_path.stat().st_size} bytes"
        )

        env = os.environ.copy()
        env["PULSE_SINK"] = env.get(
            "PULSE_SINK",
            "stream_sink"
        )

        subprocess.run(
            [
                "pactl",
                "set-default-sink",
                env["PULSE_SINK"]
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        result = subprocess.run(
            [
                "paplay",
                str(wav_path)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=45,
            env=env
        )

        if result.returncode != 0:
            err = result.stderr.decode(
                "utf-8",
                errors="replace"
            )[-1000:]

            print("[PAPLAY ERROR]", err)

            result2 = subprocess.run(
                [
                    "paplay",
                    f"--device={env['PULSE_SINK']}",
                    str(wav_path)
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=45,
                env=env
            )

            if result2.returncode != 0:
                print(
                    "[PAPLAY ERROR2]",
                    result2.stderr.decode(
                        "utf-8",
                        errors="replace"
                    )[-1000:]
                )
                return False

        print("[TTS] Playback OK")
        return True

    except Exception as e:
        print(f"[TTS ERROR] {e}")
        return False

    finally:
        try:
            wav_path.unlink(missing_ok=True)
        except Exception:
            pass


def tts_worker():

    global last_tts_time

    while True:

        text = tts_queue.get()

        if text is None:
            break

        try:

            with tts_lock:

                now = time.time()

                elapsed = now - last_tts_time

                if elapsed < 1.0:
                    time.sleep(
                        1.0 - elapsed
                    )

                if run_piper(text):
                    last_tts_time = time.time()

        except Exception as e:

            print(f"[TTS WORKER ERROR] {e}")

        finally:
            tts_queue.task_done()


threading.Thread(
    target=tts_worker,
    daemon=True
).start()



def pick_engagement_line():
    global engagement_index
    engagement_index += 1
    return random.choice(ENGAGE_PROMOS)

def speak(text):

    text = clean_tts_text(text)

    if not text:
        return

    if len(text) > 180:
        text = text[:177] + "..."

    try:
        tts_queue.put_nowait(text)
    except queue.Full:
        print("[TTS] Queue penuh, ucapan dilewati.")


# =========================================================
def engagement_loop():

    global last_engagement_time
    global engagement_index

    print("[ENGAGEMENT] Thread aktif.")

    while True:

        try:

            time.sleep(5)

            now = time.time()

            if now - last_engagement_time < ENGAGEMENT_INTERVAL:
                continue

            last_engagement_time = now

            # Bergantian:
            # 0 = like/subscribe/share
            # 1 = join

            text = pick_engagement_line()
            # engagement_index di dalam helper

            print(
                f"[ENGAGEMENT] {text}"
            )

            speak(text)

        except Exception as e:

            print(
                f"[ENGAGEMENT ERROR] {e}"
            )

            time.sleep(5)


threading.Thread(
    target=engagement_loop,
    daemon=True
).start()


# =========================================================
# YOUTUBE LIVE DETECTION
# =========================================================

def find_live_video_id():
    """Cari live TANPA Search API (hindari quota 429).

    Urutan:
    1. YOUTUBE_LIVE_ID dari env (GitHub Actions / broadcast)
    2. Scrape channel /live (httpx)
    """
    print("[AUTO] Mencari live aktif (tanpa Search API)...")

    env_id = os.environ.get("YOUTUBE_LIVE_ID", "").strip()
    if env_id:
        print(f"[AUTO] Pakai YOUTUBE_LIVE_ID dari env: {env_id}")
        return env_id

    try:
        vid = get_live_video_id(CHANNEL_ID or None)
        if vid:
            print(f"[AUTO] Live ID dari scrape: {vid}")
            return vid
    except Exception as e:
        print(f"[AUTO] get_live_video_id error: {e}")

    try:
        vid = fetch_live_id_via_https(CHANNEL_ID)
        if vid:
            print(f"[AUTO] Live ID dari fetch_live_id_via_https: {vid}")
            return vid
    except Exception as e:
        print(f"[AUTO] fetch_live_id_via_https error: {e}")

    print("[AUTO] Tidak ditemukan live stream aktif (tanpa API).")
    return None



# =========================================================
# JOIN SYSTEM — TIDAK DIUBAH
# =========================================================

def load_state():

    if not STATE_FILE.exists():

        return {
            "active": [],
            "queue": [],
            "lastUpdate": 0
        }

    try:

        with STATE_FILE.open(
            "r",
            encoding="utf-8"
        ) as f:

            state = json.load(f)

        state.setdefault(
            "active",
            []
        )

        state.setdefault(
            "queue",
            []
        )

        state.setdefault(
            "lastUpdate",
            0
        )

        return state

    except Exception as e:

        print(
            f"[STATE ERROR] {e}"
        )

        return {
            "active": [],
            "queue": [],
            "lastUpdate": 0
        }


def save_state(state):

    state["lastUpdate"] = time.time()

    fd, temp_path = tempfile.mkstemp(
        prefix="chat_state_",
        suffix=".tmp",
        dir="."
    )

    try:

        with os.fdopen(
            fd,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                state,
                f,
                ensure_ascii=False,
                indent=2
            )

            f.flush()

            os.fsync(
                f.fileno()
            )

        os.replace(
            temp_path,
            STATE_FILE
        )

    except Exception:

        try:
            os.unlink(
                temp_path
            )
        except Exception:
            pass

        raise



# ============================================================
# COUNTRY CHAT
# Penonton cukup mengetik nama negara untuk masuk ke game.
# ============================================================

COUNTRY_ALIASES = {
    "indonesia": ("ID", "Indonesia", "🇮🇩"),
    "malaysia": ("MY", "Malaysia", "🇲🇾"),
    "singapore": ("SG", "Singapore", "🇸🇬"),
    "singapura": ("SG", "Singapore", "🇸🇬"),
    "thailand": ("TH", "Thailand", "🇹🇭"),
    "vietnam": ("VN", "Vietnam", "🇻🇳"),
    "philippines": ("PH", "Philippines", "🇵🇭"),
    "filipina": ("PH", "Philippines", "🇵🇭"),
    "brunei": ("BN", "Brunei", "🇧🇳"),
    "cambodia": ("KH", "Cambodia", "🇰🇭"),
    "myanmar": ("MM", "Myanmar", "🇲🇲"),
    "laos": ("LA", "Laos", "🇱🇦"),

    "china": ("CN", "China", "🇨🇳"),
    "japan": ("JP", "Japan", "🇯🇵"),
    "jepang": ("JP", "Japan", "🇯🇵"),
    "korea": ("KR", "South Korea", "🇰🇷"),
    "south korea": ("KR", "South Korea", "🇰🇷"),
    "india": ("IN", "India", "🇮🇳"),
    "australia": ("AU", "Australia", "🇦🇺"),
    "new zealand": ("NZ", "New Zealand", "🇳🇿"),

    "palestine": ("PS", "Palestine", "🇵🇸"),
    "palestina": ("PS", "Palestine", "🇵🇸"),

    "usa": ("US", "United States", "🇺🇸"),
    "america": ("US", "United States", "🇺🇸"),
    "amerika": ("US", "United States", "🇺🇸"),
    "united states": ("US", "United States", "🇺🇸"),
    "canada": ("CA", "Canada", "🇨🇦"),
    "mexico": ("MX", "Mexico", "🇲🇽"),
    "brazil": ("BR", "Brazil", "🇧🇷"),
    "brasil": ("BR", "Brazil", "🇧🇷"),
    "argentina": ("AR", "Argentina", "🇦🇷"),
    "chile": ("CL", "Chile", "🇨🇱"),
    "colombia": ("CO", "Colombia", "🇨🇴"),
    "peru": ("PE", "Peru", "🇵🇪"),

    "england": ("GB", "England", "🏴"),
    "uk": ("GB", "United Kingdom", "🇬🇧"),
    "united kingdom": ("GB", "United Kingdom", "🇬🇧"),
    "france": ("FR", "France", "🇫🇷"),
    "germany": ("DE", "Germany", "🇩🇪"),
    "jerman": ("DE", "Germany", "🇩🇪"),
    "italy": ("IT", "Italy", "🇮🇹"),
    "italia": ("IT", "Italy", "🇮🇹"),
    "spain": ("ES", "Spain", "🇪🇸"),
    "spanyol": ("ES", "Spain", "🇪🇸"),
    "netherlands": ("NL", "Netherlands", "🇳🇱"),
    "belanda": ("NL", "Netherlands", "🇳🇱"),
    "belgium": ("BE", "Belgium", "🇧🇪"),
    "switzerland": ("CH", "Switzerland", "🇨🇭"),
    "portugal": ("PT", "Portugal", "🇵🇹"),
    "turkey": ("TR", "Turkey", "🇹🇷"),
    "turki": ("TR", "Turkey", "🇹🇷"),
    "russia": ("RU", "Russia", "🇷🇺"),
    "ukraine": ("UA", "Ukraine", "🇺🇦"),
    "poland": ("PL", "Poland", "🇵🇱"),
    "sweden": ("SE", "Sweden", "🇸🇪"),
    "norway": ("NO", "Norway", "🇳🇴"),
    "denmark": ("DK", "Denmark", "🇩🇰"),
    "finland": ("FI", "Finland", "🇫🇮"),

    "south africa": ("ZA", "South Africa", "🇿🇦"),
    "egypt": ("EG", "Egypt", "🇪🇬"),
    "saudi arabia": ("SA", "Saudi Arabia", "🇸🇦"),
    "uae": ("AE", "United Arab Emirates", "🇦🇪"),
    "united arab emirates": ("AE", "United Arab Emirates", "🇦🇪"),
}

def detect_country(text):
    text = str(text or "").strip().lower()

    if not text or len(text) > 60:
        return None

    # exact match dulu
    hit = COUNTRY_ALIASES.get(text)
    if hit:
        return hit

    # match alias sebagai whole word di dalam pesan
    for alias, data in COUNTRY_ALIASES.items():
        if len(alias) < 3:
            continue
        if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", text):
            return data

    return None


def normalize_user(user):
    return str(user).strip()


def already_joined(state, user):
    active_names = {
        p["user"].lower()
        for p in state["active"]
    }

    queue_names = {
        p["user"].lower()
        for p in state["queue"]
    }

    return (
        user.lower() in active_names
        or user.lower() in queue_names
    )


def add_player(state, user, country):
    if already_joined(state, user):
        return "already"

    code, country_name, emoji = country

    # Negara yang sama untuk viewer yang sama tidak boleh membuat marble kedua.
    player = {
        "user": user,
        "name": user,
        "viewerName": user,
        "joinedAt": time.time(),
        "control": None,
        "controlAt": 0,
        "controlId": 0,
        "flag": emoji,
        "country": country_name,
        "countryCode": code,
        "countryName": country_name,
        "countryEmoji": emoji,
        "cloneId": 0
    }

    if len(state["active"]) < MAX_PLAYERS:
        state["active"].append(player)
        return "active"

    # Lebih dari 4 tetap boleh ikut.
    # Untuk sementara kita simpan sebagai queue; tahap game berikutnya
    # akan menghubungkan peserta tambahan ke clone marble.
    state["queue"].append(player)
    return "queue"

def rotate_after_race(eliminated_name):

    global last_processed_race

    state = load_state()

    eliminated_index = None

    for i, player in enumerate(
        state["active"]
    ):

        name = str(
            player.get(
                "name",
                player.get("user", "")
            )
        )

        user = str(
            player.get(
                "user",
                ""
            )
        )

        if (
            name.lower()
            ==
            str(eliminated_name).lower()
            or
            user.lower()
            ==
            str(eliminated_name).lower()
        ):

            eliminated_index = i

            break

    if eliminated_index is None:

        print(
            f"[ROTATE] Pemain tidak ditemukan: "
            f"{eliminated_name}"
        )

        return False

    eliminated = state["active"].pop(
        eliminated_index
    )

    incoming = None

    if (
        state["queue"]
        and
        len(state["active"]) < MAX_PLAYERS
    ):

        incoming = state["queue"].pop(0)

        state["active"].append(
            incoming
        )

    save_state(state)

    print("====================================")

    print(
        f"[ROTATE] KELUAR : "
        f"{eliminated.get('name', eliminated.get('user'))}"
    )

    if incoming:

        print(
            f"[ROTATE] MASUK  : "
            f"{incoming.get('name', incoming.get('user'))}"
        )

    else:

        print(
            "[ROTATE] MASUK  : TIDAK ADA "
            "(ANTREAN KOSONG)"
        )

    print(
        f"[ROTATE] AKTIF  : "
        f"{[p.get('name', p.get('user')) for p in state['active']]}"
    )

    print(
        f"[ROTATE] QUEUE  : "
        f"{[p.get('name', p.get('user')) for p in state['queue']]}"
    )

    print("====================================")

    return True


# =========================================================
# RACE RESULT SERVER — TIDAK DIUBAH
# =========================================================

class RaceResultHandler(
    BaseHTTPRequestHandler
):

    def send_cors_headers(self):

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

    def do_OPTIONS(self):

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


    def do_POST(self):
        if self.path == "/claim-player":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                data = json.loads(body.decode("utf-8") or "{}")
                user = str(data.get("user", "")).strip().lower()
                if not user:
                    self.send_response(400)
                    self.send_cors_headers()
                    self.end_headers()
                    return
                state = load_state()
                before_a = len(state["active"])
                before_q = len(state["queue"])
                state["active"] = [
                    p for p in state["active"]
                    if str(p.get("user", p.get("name", ""))).strip().lower() != user
                ]
                state["queue"] = [
                    p for p in state["queue"]
                    if str(p.get("user", p.get("name", ""))).strip().lower() != user
                ]
                save_state(state)
                print(
                    f"[CLAIM] {user} dihapus dari state "
                    f"(active {before_a}->{len(state['active'])}, "
                    f"queue {before_q}->{len(state['queue'])})"
                )
                self.send_response(200)
                self.send_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            except Exception as e:
                print(f"[CLAIM ERROR] {e}")
                self.send_response(500)
                self.send_cors_headers()
                self.end_headers()
            return

        if self.path != "/race-result":

    def do_POST(self):

        if self.path != "/race-result":

            self.send_response(404)

            self.send_cors_headers()

            self.end_headers()

            return

        try:

            length = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )

            body = self.rfile.read(
                length
            )

            data = json.loads(
                body.decode("utf-8")
            )

            race_id = str(
                data.get(
                    "raceId",
                    ""
                )
            ).strip()

            eliminated = str(
                data.get(
                    "eliminated",
                    ""
                )
            ).strip()

            if not race_id or not eliminated:

                self.send_response(400)

                self.send_cors_headers()

                self.end_headers()

                return

            global last_processed_race

            if race_id == last_processed_race:

                self.send_response(200)

                self.send_cors_headers()

                self.end_headers()

                self.wfile.write(
                    b"already processed"
                )

                return

            if rotate_after_race(
                eliminated
            ):

                last_processed_race = race_id

                self.send_response(200)

                self.send_cors_headers()

                self.end_headers()

                self.wfile.write(
                    b"rotation ok"
                )

            else:

                self.send_response(404)

                self.send_cors_headers()

                self.end_headers()

                self.wfile.write(
                    b"player not found"
                )

        except Exception as e:

            print(
                f"[ROTATION ERROR] {e}"
            )

            self.send_response(500)

            self.send_cors_headers()

            self.end_headers()

    def log_message(
        self,
        format,
        *args
    ):
        return


def start_rotation_server():

    server = ThreadingHTTPServer(
        (
            "127.0.0.1",
            ROTATION_PORT
        ),
        RaceResultHandler
    )

    print(
        f"[ROTATION SERVER] "
        f"http://127.0.0.1:{ROTATION_PORT}"
    )

    server.serve_forever()



# =========================================================
# TEMPLATE CHAT — TANPA AI
# =========================================================

CHAT_TEMPLATES = {}

def load_chat_templates():
    CHAT_TEMPLATES.clear()

    template_dir = Path("templates")

    if not template_dir.exists():
        print("[TEMPLATE] folder templates belum ada")
        return

    for path in sorted(template_dir.glob("*.txt")):
        try:
            lines = [
                line.strip()
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            if lines:
                CHAT_TEMPLATES[path.stem] = lines

        except Exception as e:
            print(f"[TEMPLATE ERROR] {path}: {e}")

    total = sum(len(v) for v in CHAT_TEMPLATES.values())

    print(
        f"[TEMPLATE] {len(CHAT_TEMPLATES)} kategori, "
        f"{total} template dimuat"
    )


def template_category(text):
    t = str(text or "").lower().strip()

    if "?" in t or any(
        w in t.split()
        for w in [
            "apa", "siapa", "kenapa", "kok",
            "gimana", "bagaimana", "kapan",
            "dimana", "berapa"
        ]
    ):
        return "question"

    if any(
        w in t.split()
        for w in [
            "join", "ikut", "main", "turun",
            "daftar", "gabung"
        ]
    ):
        return "join"

    if any(
        w in t
        for w in ["wkwk", "haha", "hehe", "lol"]
    ):
        return "laugh"

    if any(
        w in t
        for w in [
            "balap", "game dadu", "race", "lap",
            "mobil", "overtake", "nyalip",
            "finish", "p1", "p2", "p3"
        ]
    ):
        return "racing"

    if any(
        w in t
        for w in [
            "halo", "hai", "hi", "hello",
            "pagi", "siang", "malam"
        ]
    ):
        return "greeting"

    if any(
        w in t
        for w in [
            "gila", "buset", "anjay",
            "waduh", "wow", "wih", "wah"
        ]
    ):
        return "reaction"

    if any(
        w in t
        for w in [
            "mantap", "keren", "bagus",
            "gokil", "gas", "semangat",
            "support", "dukung"
        ]
    ):
        return "support"

    return "generic"


# =========================================================
# COMBINATORIAL CHAT ENGINE — TANPA AI
# =========================================================

COMBO_PARTS = {
    "greeting": {
        "open": ["Hey", "Yo", "Hello", "Hi", "Welcome"],
        "middle": [
            "the marble maze is heating up",
            "the race is getting wild",
            "great to see you here",
            "the arena is packed",
            "action is nonstop"
        ],
        "end": [
            "enjoy the race!",
            "don't blink!",
            "cheer for your country!",
            "have fun!",
            "let's go!"
        ],
    },
    "reaction": {
        "open": ["Whoa", "Wow", "Nice", "Insane", "Oh no"],
        "middle": [
            "that move was crazy",
            "the lead is changing fast",
            "what a close call",
            "positions keep shifting",
            "the front is intense"
        ],
        "end": [
            "don't blink!",
            "this is wild!",
            "keep watching!",
            "what a race!",
            "unreal!"
        ],
    },
    "racing": {
        "open": ["Go", "Yes", "Whoa", "Nice", "Come on"],
        "middle": [
            "the duel up front is intense",
            "what a clean overtake",
            "positions can still change",
            "the next stretch will be brutal",
            "the gap is getting thin"
        ],
        "end": [
            "don't blink!",
            "keep watching!",
            "who takes first?",
            "this is not over!",
            "let's go!"
        ],
    },
    "laugh": {
        "open": ["Haha", "Lol", "Nice", "Funny", "Hah"],
        "middle": [
            "chat is hilarious",
            "that comment made it better",
            "you cracked me up",
            "the vibe is great",
            "Luna is laughing too"
        ],
        "end": [
            "keep it coming!",
            "don't stop chatting!",
            "love it!",
            "awesome!",
            "haha!"
        ],
    },
    "support": {
        "open": ["Awesome", "Nice", "Yes", "Great", "Love it"],
        "middle": [
            "your support keeps the stream alive",
            "chat energy is strong",
            "thanks for being here",
            "the live feels better with you",
            "appreciate the support"
        ],
        "end": [
            "keep it up!",
            "don't leave!",
            "thanks!",
            "stay with us!",
            "let's go!"
        ],
    },
    "join": {
        "open": ["Go", "Hey", "Come on", "Yes", "Ready"],
        "middle": [
            "type your country name to join",
            "just type a country to enter",
            "pick a country in chat",
            "the race is open",
            "spots are still available"
        ],
        "end": [
            "join now!",
            "don't just watch!",
            "enter the arena!",
            "let's go!",
            "type a country!"
        ],
    },
    "question": {
        "open": ["Sure", "Okay", "Hey", "Alright", "Got it"],
        "middle": [
            "we are watching closely",
            "it will be clear soon",
            "positions are still changing",
            "stay tuned to the finish",
            "let's see how this plays out"
        ],
        "end": [
            "keep watching!",
            "don't blink!",
            "hang tight!",
            "almost there!",
            "let's go!"
        ],
    },
    "generic": {
        "open": ["Hey", "Yo", "Nice", "Whoa", "Yes"],
        "middle": [
            "chat is keeping the energy high",
            "the marble maze is wild",
            "the live is popping",
            "this race is intense",
            "great vibes in chat"
        ],
        "end": [
            "keep chatting!",
            "enjoy the race!",
            "don't leave!",
            "let's go!",
            "awesome!"
        ],
    },
}
def template_reply(user, text):
    category = template_category(text)
    parts = COMBO_PARTS.get(category, COMBO_PARTS["generic"])

    name = str(user or "bro").strip().split()[0][:12]

    # Kombinasi open × middle × end.
    reply = (
        f"{random.choice(parts['open'])} {name}, "
        f"{random.choice(parts['middle'])}, "
        f"{random.choice(parts['end'])}"
    )

    reply = re.sub(r"\s+", " ", reply).strip()

    return reply[:180]


load_chat_templates()


# =========================================================
# PYTCHAT
# =========================================================

def create_chat_with_retry(
    video_id,
    max_retries=10,
    delay=6
):

    for attempt in range(
        1,
        max_retries + 1
    ):

        try:

            print(
                f"[CHAT] Mencoba koneksi pytchat... "
                f"({attempt}/{max_retries})"
            )

            chat = pytchat.create(
                video_id=video_id,
                interruptable=False
            )

            if chat.is_alive():

                print(
                    f"[CHAT] Koneksi berhasil "
                    f"pada percobaan {attempt}"
                )

                return chat

            try:
                chat.terminate()
            except Exception:
                pass

        except Exception as e:

            print(
                f"[CHAT] Gagal percobaan "
                f"{attempt}: {e}"
            )

        if attempt < max_retries:

            print(
                f"[CHAT] Tunggu {delay} detik..."
            )

            time.sleep(delay)

    return None



# =========================================================
# DUAL LIVE CHAT (landscape + vertical)
# =========================================================
chat_event_queue = queue.Queue(maxsize=500)


def _chat_reader_loop(video_id, label):
    if not video_id:
        print(f"[CHAT:{label}] video_id kosong — skip")
        return
    print(f"[CHAT:{label}] start {video_id}")
    while True:
        try:
            chat = create_chat_with_retry(video_id, max_retries=8, delay=5)
            if chat is None:
                print(f"[CHAT:{label}] gagal connect, sleep 15s")
                time.sleep(15)
                continue
            print(f"[CHAT:{label}] connected")
            while chat.is_alive():
                for c in chat.get().sync_items():
                    try:
                        chat_event_queue.put_nowait((label, c))
                    except queue.Full:
                        pass
                time.sleep(0.25)
            print(f"[CHAT:{label}] disconnected")
            time.sleep(3)
        except Exception as e:
            print(f"[CHAT:{label}] ERROR {e}")
            time.sleep(5)


# =========================================================
# MAIN BOT
# =========================================================

def start_bot():
    global VIDEO_ID

    # NON-API: prioritaskan env dari GitHub Actions (broadcast)
    _eid = os.environ.get("YOUTUBE_LIVE_ID", "").strip()
    if _eid:
        VIDEO_ID = _eid
        print(f"[AUTO] YOUTUBE_LIVE_ID dari env: {VIDEO_ID}")



    print("====================================")
    print(
        " LUNA CHAT + COMMENTATOR ONLINE"
    )
    print(" Template Chat + Piper TTS")
    print("====================================")

    if VIDEO_ID:

        print(
            f"[MANUAL] Menggunakan "
            f"YOUTUBE_LIVE_ID: {VIDEO_ID}"
        )

    else:

        print(
            "[AUTO] Mencari live aktif..."
        )

        for attempt in range(
            1,
            16
        ):

            print(
                f"[AUTO] Percobaan {attempt}/15..."
            )

            found_id = find_live_video_id()

            if found_id:

                VIDEO_ID = found_id

                break

            time.sleep(5)

        if not VIDEO_ID:

            print(
                "ERROR: Tidak menemukan "
                "live stream aktif."
            )

            return

    print(
        f"[BOT] Live ID: {VIDEO_ID}"
    )

    print(
        f"[BOT] Max aktif: {MAX_PLAYERS}"
    )

    print("====================================")

    # Reset join list tiap start bot / sesi stream baru
    state = {"active": [], "queue": [], "lastUpdate": 0}
    save_state(state)
    print("[STATE] chat_state.json di-reset (active/queue kosong)")

    # Rotation server lama tetap hidup.
    threading.Thread(
        target=start_rotation_server,
        daemon=True
    ).start()

    print(
        "[CHAT] Menunggu chat siap..."
    )

    time.sleep(8)

    vertical_id = os.environ.get("YOUTUBE_VERTICAL_LIVE_ID", "").strip()
    print(f"[BOT] Landscape Live ID: {VIDEO_ID}")
    print(f"[BOT] Vertical Live ID : {vertical_id or '(tidak ada)'}")

    threading.Thread(
        target=_chat_reader_loop,
        args=(VIDEO_ID, "LAND"),
        daemon=True,
    ).start()

    if vertical_id and vertical_id != VIDEO_ID:
        threading.Thread(
            target=_chat_reader_loop,
            args=(vertical_id, "VERT"),
            daemon=True,
        ).start()
    else:
        print("[BOT] Vertical chat tidak di-start.")

    speak("Luna is ready! Enjoy the marble maze and have fun!")

    print("====================================")

    while True:

        try:

            try:
                label, c = chat_event_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            user = normalize_user(
                c.author.name
            )

            raw_msg = str(
                c.message
            ).strip()

            msg = raw_msg.lower()

            print(f"[CHAT:{label}] {user}: {raw_msg}")

            # CHAT GAME:
            # Penonton cukup mengetik nama negara.
            # Tidak ada JOIN dan tidak ada pilihan angka.

            if msg == "join" or msg.startswith("join "):
                print(f"[CHAT] JOIN diabaikan: {user}")
                continue

            # =====================================================
            # COUNTRY JOIN AUTO
            # Viewer cukup mengetik nama negara.
            # =====================================================
            country = detect_country(raw_msg)

            if country:
                state = load_state()

                result = add_player(
                    state,
                    user,
                    country
                )

                save_state(state)

                code, country_name, emoji = country

                if result == "active":
                    print(
                        f'[COUNTRY JOIN] {emoji} {country_name} <- {user} [ACTIVE]'
                    )
                    speak(f"{country_name} has joined the race!")

                elif result == "queue":
                    print(
                        f'[COUNTRY JOIN] {emoji} {country_name} <- {user} [QUEUE]'
                    )
                    speak(f"{country_name} is in the queue!")

                elif result == "already":
                    print(
                        f'[COUNTRY JOIN] {user} already joined.'
                    )

                continue

            if raw_msg:

                now = time.time()

                last_user_time = (
                    last_chat_response
                    .get(user.lower(), 0)
                )

                if (
                    now - last_user_time
                    >= CHAT_COOLDOWN
                ):

                    if len(raw_msg) <= 180:

                        print(
                            f"[CHAT IN] {user}: {raw_msg}"
                        )

                        category = template_category(raw_msg)

                        reply = template_reply(
                            user,
                            raw_msg
                        )

                        print(
                            f"[LUNA TEMPLATE] category={category} "
                            f"{user}: {raw_msg} -> {reply}"
                        )

                        speak(reply)

                        last_chat_response[
                            user.lower()
                        ] = now

        except Exception as e:

            print(
                f"[CHAT ERROR] {e}"
            )

            time.sleep(2)



if __name__ == "__main__":

    start_bot()
