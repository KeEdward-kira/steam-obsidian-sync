import os
import re
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# =========================
# 配置区域
# =========================

STEAM_API_KEY = os.environ.get("STEAM_API_KEY", "")
STEAM_ID = os.environ.get("STEAM_ID", "")

OBSIDIAN_VAULT = os.environ.get("OBSIDIAN_VAULT", str(Path(__file__).parent))
OUTPUT_FOLDER = "Steam Games"

REQUEST_TIMEOUT = 20
REQUEST_RETRY = 3
REQUEST_DELAY = 2.5

PROXY = os.environ.get("STEAM_PROXY", "")

if not STEAM_API_KEY or not STEAM_ID:
    print("❌ 缺少必要配置，请在 .env 文件中设置 STEAM_API_KEY 和 STEAM_ID")
    print("   参考 .env.example 文件创建 .env")
    exit(1)

# =========================
# 构建 session
# =========================

session = requests.Session()
if PROXY:
    session.proxies.update({"http": PROXY, "https": PROXY})
    print(f"🔧 使用代理: {PROXY}")
else:
    print("🔧 未配置代理，使用直连")

# =========================
# 工具函数
# =========================

def safe_filename(name):
    sanitized = "".join(c for c in name if c not in '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\\/:*?"<>|')
    sanitized = sanitized.strip(". ")
    return sanitized or "Unknown Game"


def fetch_with_retry(url, retries=REQUEST_RETRY, delay=REQUEST_DELAY):
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:
                wait = delay * (attempt + 2)
                print(f"  ⚠ 限流，等待 {wait:.1f}s 后重试 ({attempt+1}/{retries})...")
                time.sleep(wait)
                continue
            print(f"  ⚠ HTTP {resp.status_code}")
            return None
        except requests.ConnectionError:
            print(f"  ⚠ 连接被拒绝/拦截 ({attempt+1}/{retries})")
            if attempt < retries - 1:
                time.sleep(delay * 2)
        except requests.Timeout:
            print(f"  ⚠ 请求超时 ({attempt+1}/{retries})")
            if attempt < retries - 1:
                time.sleep(delay)
        except requests.RequestException as e:
            print(f"  ⚠ 请求失败: {e} ({attempt+1}/{retries})")
            if attempt < retries - 1:
                time.sleep(delay)
    return None


def test_connectivity():
    print("🔍 正在检测网络连通性...")
    test_url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
    test_params = {"key": STEAM_API_KEY, "steamids": STEAM_ID}

    try:
        resp = session.get(test_url, params=test_params, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            print("✅ Steam API 连接正常\n")
            return True
        print(f"⚠️ Steam API 返回 HTTP {resp.status_code}")
        return False
    except requests.ConnectionError:
        print("❌ 无法连接 Steam API（连接被拒绝/拦截）")
        print("   请尝试以下方法：")
        print("   1. 开启代理/VPN 后重新运行")
        print("   2. 设置环境变量指定代理：")
        print("      PowerShell: $env:STEAM_PROXY=\"http://127.0.0.1:7890\"")
        print("      CMD:        set STEAM_PROXY=http://127.0.0.1:7890")
        print("   3. 如果使用 Clash/v2rayN，确认本地代理端口正确")
        return False
    except requests.Timeout:
        print("❌ 连接 Steam API 超时")
        print("   网络可能受限，请开启代理后重试")
        return False
    except Exception as e:
        print(f"❌ 网络检测失败: {e}")
        return False


def parse_existing_notes(filepath):
    if not filepath.exists():
        return ""
    try:
        content = filepath.read_text(encoding="utf-8")
        match = re.search(r"^## 我的游戏笔记\s*\n(.*)", content, re.DOTALL)
        if match:
            return match.group(1).rstrip()
    except Exception:
        pass
    return ""


def fetch_achievements(appid):
    url = f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={STEAM_API_KEY}&steamid={STEAM_ID}&appid={appid}"
    data = fetch_with_retry(url)
    if not data:
        return None, None
    try:
        stats = data.get("playerstats", {})
        achievements = stats.get("achievements", [])
        if not achievements:
            return None, None
        total = len(achievements)
        completed = sum(1 for a in achievements if a.get("achieved", 0) == 1)
        return completed, total
    except (KeyError, TypeError):
        return None, None


def build_frontmatter(name, appid, playtime_hours, recommendations, release_date, genres, cover_url, achievements_completed=None, achievements_total=None):
    lines = [
        "---",
        f"title: \"{name}\"",
        f"appid: {appid}",
        f"playtime: {playtime_hours}",
        f"recommendations: {recommendations}",
        f"release_date: \"{release_date}\"",
    ]
    if achievements_total is not None:
        lines.append(f"achievements: \"{achievements_completed}/{achievements_total}\"")
        rate = round(achievements_completed / achievements_total * 100, 1) if achievements_total > 0 else 0
        lines.append(f"achievement_rate: {rate}")
    lines.append("tags:")
    for genre in genres:
        lines.append(f"  - {genre.lower()}")
    lines.append(f"cover: {cover_url}")
    lines.append("---")
    return "\n".join(lines)


def build_body(name, appid, playtime_hours, recommendations, release_date, genres, cover_url, existing_notes):
    genre_lines = "\n".join(f"- {g}" for g in genres) if genres else ""

    parts = [
        f"# {name}",
        "",
        f"![cover]({cover_url})",
        "",
        "## 游戏信息",
        "",
        f"- Steam AppID：{appid}",
        f"- 游玩时间：{playtime_hours} 小时",
        f"- 推荐人数：{recommendations}",
        f"- 发售日期：{release_date}",
        "",
        "## 类型",
        "",
        genre_lines,
        "",
        "## 我的游戏笔记",
        "",
        existing_notes.strip() if existing_notes.strip() else "",
        "",
        "## 想法",
        "",
        "",
        "## 值得记录的内容",
        "",
        "",
    ]
    return "\n".join(parts)


# =========================
# 主逻辑
# =========================

if not test_connectivity():
    exit(1)

owned_games_url = (
    f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
    f"?key={STEAM_API_KEY}&steamid={STEAM_ID}&include_appinfo=true"
    f"&include_played_free_games=true"
)

print("正在获取游戏列表...")
data = fetch_with_retry(owned_games_url)
if not data:
    print("❌ 无法获取游戏列表，请检查 API Key 和网络连接")
    exit(1)

games = data.get("response", {}).get("games", [])
if not games:
    print("❌ 游戏列表为空，请检查 Steam ID 是否正确")
    exit(1)

output_path = Path(OBSIDIAN_VAULT) / OUTPUT_FOLDER
output_path.mkdir(parents=True, exist_ok=True)

print(f"发现 {len(games)} 个游戏，开始同步...\n")

success_count = 0
fail_count = 0

for i, game in enumerate(games, 1):
    appid = game.get("appid")
    name = game.get("name", "Unknown Game")
    playtime_minutes = game.get("playtime_forever", 0)
    playtime_hours = round(playtime_minutes / 60, 1)

    release_date = "Unknown"
    recommendations = 0
    genres = []

    store_url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=schinese"
    store_data = fetch_with_retry(store_url)

    if store_data:
        try:
            app_data = store_data[str(appid)]["data"]
            release_date = app_data.get("release_date", {}).get("date", "Unknown")
            recommendations = app_data.get("recommendations", {}).get("total", 0)
            genres = [g.get("description", "") for g in app_data.get("genres", []) if g.get("description")]
        except (KeyError, TypeError):
            pass

    cover_url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg"

    achievements_completed, achievements_total = fetch_achievements(appid)

    safe_name = safe_filename(name)
    file_path = output_path / f"{safe_name}.md"

    existing_notes = parse_existing_notes(file_path)

    frontmatter = build_frontmatter(name, appid, playtime_hours, recommendations, release_date, genres, cover_url, achievements_completed, achievements_total)
    body = build_body(name, appid, playtime_hours, recommendations, release_date, genres, cover_url, existing_notes)

    md_content = frontmatter + "\n\n" + body

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    status = "✅" if release_date != "Unknown" else "⚠️(商店数据缺失)"
    print(f"  [{i}/{len(games)}] {status} {safe_name}.md")
    if release_date != "Unknown":
        success_count += 1
    else:
        fail_count += 1

    if i < len(games):
        time.sleep(REQUEST_DELAY)

print(f"\n同步完成！成功 {success_count} 个，商店数据缺失 {fail_count} 个")
