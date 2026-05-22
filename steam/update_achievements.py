import os
import re
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

STEAM_API_KEY = os.environ.get("STEAM_API_KEY", "")
STEAM_ID = os.environ.get("STEAM_ID", "")
PROXY = os.environ.get("STEAM_PROXY", "")
REQUEST_TIMEOUT = 20
REQUEST_RETRY = 3
REQUEST_DELAY = 1.5

GAMES_DIR = Path(os.environ.get("OBSIDIAN_VAULT", str(Path(__file__).parent))) / "Steam Games"

if not STEAM_API_KEY or not STEAM_ID:
    print("❌ 缺少必要配置，请在 .env 文件中设置 STEAM_API_KEY 和 STEAM_ID")
    print("   参考 .env.example 文件创建 .env")
    exit(1)

session = requests.Session()
if PROXY:
    session.proxies.update({"http": PROXY, "https": PROXY})
    print(f"🔧 使用代理: {PROXY}")
else:
    print("🔧 未配置代理，使用直连")


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
            if resp.status_code == 400:
                return None
            print(f"  ⚠ HTTP {resp.status_code}")
            return None
        except requests.RequestException as e:
            print(f"  ⚠ 请求失败: {e} ({attempt+1}/{retries})")
            if attempt < retries - 1:
                time.sleep(delay)
    return None


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


md_files = sorted(GAMES_DIR.glob("*.md"))
print(f"发现 {len(md_files)} 个游戏文件，开始获取成就数据...\n")

updated = 0
skipped = 0
failed = 0

for i, md_file in enumerate(md_files, 1):
    content = md_file.read_text(encoding="utf-8")

    if "achievements:" in content:
        print(f"  [{i}/{len(md_files)}] ⏭️ {md_file.stem} (已有成就数据)")
        skipped += 1
        continue

    appid_match = re.search(r"^appid: (\d+)", content, re.MULTILINE)
    if not appid_match:
        print(f"  [{i}/{len(md_files)}] ⚠️ {md_file.stem} (无 appid)")
        failed += 1
        continue

    appid = appid_match.group(1)
    completed, total = fetch_achievements(appid)

    if total is not None:
        rate = round(completed / total * 100, 1) if total > 0 else 0
        achievements_line = f'achievements: "{completed}/{total}"'
        rate_line = f"achievement_rate: {rate}"

        content = content.replace(
            "tags:",
            f"{achievements_line}\n{rate_line}\ntags:",
        )
        md_file.write_text(content, encoding="utf-8")
        print(f"  [{i}/{len(md_files)}] ✅ {md_file.stem} → {completed}/{total} ({rate}%)")
        updated += 1
    else:
        print(f"  [{i}/{len(md_files)}] ➖ {md_file.stem} (无成就)")
        failed += 1

    if i < len(md_files):
        time.sleep(REQUEST_DELAY)

print(f"\n完成！更新 {updated} 个，跳过 {skipped} 个，无成就 {failed} 个")
