"""
publish_week.py — publishes (or re-publishes) one week of the 52 at 52 challenge.

Every activity lives in its own folder:

    content/activities/Week 1 Activity 1/activity.md   (+ its photos)
    content/activities/Week 1 Activity 2/activity.md   (+ its photos)
    content/activities/Week 2 Activity 1/...

The script asks which week to publish, collects EVERY "Week X Activity N"
folder for that week, and rebuilds that week's page with the running total,
the progress toward 52 credited km and, once reached, a "goal achieved" badge.
Run it after the first activity, after each new one, or once at the end of the
week: each run simply replaces that week's page with the current state.

Optional week intro/title: content/weeks/week-XX.md (see _template-week.md).

Usage:  py tools/publish_week.py        (asks for the week number)
        py tools/publish_week.py 1
Needs:  py -m pip install Pillow Markdown
"""
import json, re, shutil, sys
from datetime import date, datetime, timedelta
from build_pages import build_all, safe_id
from project_paths import ROOT, SITE, CONTENT as SOURCES, PRIVATE, ensure_new_site
from challenge_rules import credited_distance, score, week_score

ACTIVITIES_DIR = SOURCES / "activities"
WEEKS_DIR = SOURCES / "weeks"
DATA = SITE / "data"
SEASON_START = date(2026, 11, 7)          # Week 1 = Saturday Nov 7 → Friday Nov 13, 2026
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
FOLDER_RE = re.compile(r"^week\s*0*(\d+)\s*[-_ ]*\s*activity\s*0*(\d+)\s*$", re.I)
NUMERIC = {"distance_km", "elevation_m", "elevation_ft", "max_speed_kmh", "calories"}

try:
    import markdown
    md = lambda t: markdown.markdown(t.strip(), extensions=["extra"]) if t.strip() else ""
except ImportError:
    md = lambda t: "".join(f"<p>{p.strip()}</p>" for p in t.split("\n\n") if p.strip())


def na(v): return v is None or str(v).strip().upper() in ("", "NA", "N/A", "NONE")

def secs(hms):
    parts = [int(x) for x in str(hms).strip().split(":")]
    while len(parts) < 3: parts.insert(0, 0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]

def fmt_hms(s):
    h, rem = divmod(int(s), 3600); m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"

def fmt_pace(s_per_km):
    m, s = divmod(round(s_per_km), 60); return f"{m}:{s:02d}"

def week_dates(n):
    start = SEASON_START + timedelta(days=7 * (n - 1))
    return start, start + timedelta(days=6)

def kv_block(text):
    out = {}
    for line in text.splitlines():
        m = re.match(r"^([a-z_]+):\s*(.*)$", line.strip())
        if m: out[m.group(1)] = m.group(2).strip()
    return out

def front_matter(path):
    raw = path.read_text(encoding="utf-8-sig")
    fm = re.match(r"^---\s*\n(.*?)\n---\s*\n?", raw, re.S)
    if not fm: sys.exit(f"{path} must start with a --- front-matter --- block.")
    body = re.sub(r"<!--.*?-->", "", raw[fm.end():], flags=re.S)
    return kv_block(fm.group(1)), body

def stories(body, marker="Story"):
    """Text after '# Story (EN)' / '# Story (PT)' up to the next such marker.
    Sub-headings (##, ###) inside a story are kept."""
    res = {"en": "", "pt": ""}
    parts = re.split(rf"^#{{1,3}}\s*{marker}\s*\((EN|PT)\)\s*$", body, flags=re.M | re.I)
    for lang, text in zip(parts[1::2], parts[2::2]):
        res[lang.lower()] = md(text)
    return res


def find_activity_folders(week_no):
    if not ACTIVITIES_DIR.exists(): return []
    found = []
    for d in ACTIVITIES_DIR.iterdir():
        m = FOLDER_RE.match(d.name) if d.is_dir() else None
        if m and int(m.group(1)) == week_no:
            found.append((int(m.group(2)), d))
    numbers = [n for n, _ in found]
    dupes = {n for n in numbers if numbers.count(n) > 1}
    if dupes:
        sys.exit(f"Two folders use the same activity number for week {week_no}: {sorted(dupes)}. Nothing changed.")
    return sorted(found)


def process_photos(week_no, act_id, names, src_dir):
    out_dir = SITE / "media" / f"week-{week_no:02d}" / act_id
    if out_dir.exists(): shutil.rmtree(out_dir)          # re-publishing replaces old photos
    if not names: return []
    out_dir.mkdir(parents=True, exist_ok=True)
    result = []
    for n in names:
        src = next((p for p in (src_dir / n, src_dir / "photos" / n) if p.exists()), None)
        if not src:
            print(f"  ! photo not found: {n}"); continue
        if src.suffix.lower() not in IMG_EXT:
            print(f"  ! skipped (not an image): {n}"); continue
        dst = out_dir / (src.stem + ".webp")
        try:
            from PIL import Image, ImageOps
            if src.suffix.lower() == ".heic":
                from pillow_heif import register_heif_opener; register_heif_opener()
            im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
            im.thumbnail((2000, 2000)); im.save(dst, "WEBP", quality=82)
        except Exception as e:
            dst = out_dir / src.name; shutil.copy2(src, dst)
            print(f"  ! copied without optimizing ({e.__class__.__name__}): {n}")
        result.append(f"media/week-{week_no:02d}/{act_id}/{dst.name}")
    return result


def read_activity(week_no, number, folder):
    md_path = folder / "activity.md"
    if not md_path.exists():
        sys.exit(f"Missing {md_path}. Copy content/activities/_template/activity.md into that folder.")
    a, body = front_matter(md_path)
    # Accept the older field name 'duration' as moving time.
    if na(a.get("moving_time")) and not na(a.get("duration")): a["moving_time"] = a["duration"]
    for req in ("type", "date", "distance_km", "moving_time"):
        if na(a.get(req)): sys.exit(f"{folder.name}: '{req}' is required.")

    rec = {"id": safe_id(a["id"] if not na(a.get("id")) else f"w{week_no:02d}-a{number}"),
           "week": week_no, "number": number, "folder": folder.name}
    for k, v in a.items():
        if k in ("id", "photos", "youtube", "duration"): continue
        if na(v): rec[k] = None
        elif k in NUMERIC: rec[k] = float(v.replace(",", ""))
        else: rec[k] = v
    rec["type"] = rec["type"].lower()
    if rec["type"] not in ("run", "ride"):
        sys.exit(f"{folder.name}: type must be 'run' or 'ride'.")
    try: day = date.fromisoformat(rec["date"])
    except ValueError: sys.exit(f"{folder.name}: date must look like 2026-11-07.")
    start, end = week_dates(week_no)
    if not (start <= day <= end):
        print(f"  ! WARNING: {folder.name} is dated {day}, outside week {week_no} ({start} → {end}).")

    # Elevation: meters preferred; feet still accepted.
    if rec.get("elevation_m") is None and rec.get("elevation_ft") is not None:
        rec["elevation_m"] = round(rec["elevation_ft"] * 0.3048)
    if rec.get("elevation_m") is not None:
        rec["elevation_ft"] = round(rec["elevation_m"] / 0.3048)

    km = rec["distance_km"]
    rec["seconds"] = secs(rec["moving_time"])
    rec["moving_time"] = fmt_hms(rec["seconds"])
    rec["duration"] = rec["moving_time"]                     # kept for older pages/data
    if rec.get("elapsed_time"):
        rec["elapsed_seconds"] = secs(rec["elapsed_time"]); rec["elapsed_time"] = fmt_hms(rec["elapsed_seconds"])
    rec["credited_km"] = float(credited_distance(rec))
    rec["avg_speed_kmh"] = round(km / (rec["seconds"] / 3600), 2) if rec["seconds"] else None
    if rec["type"] == "run":
        # A pace typed in activity.md (e.g. copied from Strava) wins; otherwise use moving time.
        rec["pace_min_km"] = rec.pop("pace", None) or (fmt_pace(rec["seconds"] / km) if km else None)
    else:
        rec.pop("pace", None); rec["pace_min_km"] = None

    rec["youtube"] = [u.strip() for u in (a.get("youtube") or "").split(",") if not na(u)]
    if na(a.get("photos")):    # default: every image in the folder (and photos/), sorted by name
        names = sorted(p.name if p.parent == folder else f"photos/{p.name}"
                       for p in list(folder.iterdir()) + list((folder / "photos").glob("*"))
                       if p.is_file() and p.suffix.lower() in IMG_EXT)
    else:
        names = [p.strip() for p in a["photos"].split(",") if p.strip()]
    rec["photos"] = process_photos(week_no, rec["id"], names, folder)
    rec["story"] = stories(body)
    return rec


def build(week_no):
    folders = find_activity_folders(week_no)
    if not folders:
        sys.exit(f"No folders named 'Week {week_no} Activity N' found in {ACTIVITIES_DIR}. Nothing changed.")
    records = [read_activity(week_no, n, f) for n, f in folders]

    start, end = week_dates(week_no)
    week = {}; week_story = {}
    intro = WEEKS_DIR / f"week-{week_no:02d}.md"
    if intro.exists():
        week, body = front_matter(intro)
        week_story = stories(body, "Week story")
    total = round(sum(r["distance_km"] for r in records), 2)
    by_type = {}
    for r in records: by_type[r["type"]] = round(by_type.get(r["type"], 0) + r["distance_km"], 2)
    summary = {
        "week": week_no, "start": start.isoformat(), "end": end.isoformat(),
        "title_en": None if na(week.get("title_en")) else week["title_en"],
        "title_pt": None if na(week.get("title_pt")) else week["title_pt"],
        "story": week_story, "activities": len(records),
        "total_km": total, "km_by_type": by_type,
        "seconds": sum(r["seconds"] for r in records),
        "elevation_m": round(sum(r.get("elevation_m") or 0 for r in records)),
        "calories": round(sum(r.get("calories") or 0 for r in records)) or None,
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        **score(records),
    }
    return summary, records


def load(p): return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []

def save(p, data):
    if p.exists():
        bk_dir = ROOT / "_private" / "backups"; bk_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, bk_dir / f"{p.stem}.backup-{datetime.now():%Y%m%d-%H%M%S}{p.suffix}")
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_rss(weeks):
    """Regenerates rss.xml from all published weeks (free RSS-to-email
    services like Blogtrottr or follow.it can use it)."""
    base = "https://52at52.app/"
    items = []
    for w in sorted(weeks, key=lambda w: w["week"], reverse=True):
        title = w.get("title_en") or f"Week {w['week']}"
        link = f"{base}weeks/week-{w['week']:02d}/"
        desc = (f"{w['credited_km']:g} credited km / 52; {w['total_km']} actual km "
                f"across {w['activities']} activities; "
                f"goal {'achieved' if w['goal_met'] else 'in progress'}.")
        items.append(f"<item><title>{title}</title><link>{link}</link><guid>{link}</guid>"
                     f"<description>{desc}</description></item>")
    rss = (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
           f"<title>52 at 52 - 52 km a Week</title><link>{base}</link>"
           f"<description>52 credited km each week: run km + ride km / 2.</description>"
           + "".join(items) + "</channel></rss>")
    (SITE / "rss.xml").write_text(rss, encoding="utf-8")


def notify_subscribers(summary):
    """Optional: email subscribers. Configure _private/notify.ini and keep the list in
    _private/subscribers.json (never commit these)."""
    import smtplib
    from email.mime.text import MIMEText
    ini = PRIVATE / "notify.ini"; subs_file = PRIVATE / "subscribers.json"
    if not ini.exists() or not subs_file.exists():
        print("Email notification skipped (not configured)."); return
    if input("Email subscribers about this update? (y/N): ").strip().lower() != "y":
        print("Email notification skipped."); return
    cfg = dict(re.findall(r"^(\w+)\s*=\s*(.+)$", ini.read_text(encoding="utf-8"), re.M))
    subs = load(subs_file)
    if not subs: print("Email notification skipped (subscriber list is empty)."); return
    body = (f"Week {summary['week']} update: {summary['credited_km']:g} / 52 credited km "
            f"across {summary['activities']} activities "
            f"({'goal achieved!' if summary['goal_met'] else 'in progress'}).\n\n"
            f"Read it: https://52at52.app/weeks/week-{summary['week']:02d}/\n\n"
            "You receive this because you subscribed to 52 at 52. Unsubscribe anytime by replying.")
    msg = MIMEText(body)
    msg["Subject"] = f"52 at 52 - Week {summary['week']} update"
    msg["From"] = cfg["from_email"]; msg["To"] = cfg["from_email"]
    with smtplib.SMTP(cfg["smtp_host"], int(cfg.get("smtp_port", 587))) as s:
        s.starttls(); s.login(cfg["username"], cfg["password"])
        s.send_message(msg, to_addrs=[x["email"] if isinstance(x, dict) else x for x in subs])
    print(f"Notification email sent to {len(subs)} subscriber(s).")


def main():
    ensure_new_site()
    week_no = int(sys.argv[1]) if len(sys.argv) > 1 else int(input("Week number to publish: "))
    summary, records = build(week_no)
    print(f"\nWeek {week_no}  ({summary['start']} → {summary['end']})  —  {len(records)} activit{'y' if len(records) == 1 else 'ies'}")
    for r in records:
        extra = f"pace {r['pace_min_km']}/km" if r["pace_min_km"] else f"{r['avg_speed_kmh']} km/h"
        print(f"  #{r['number']}  {r['date']}  {r['type']:<4} {r['distance_km']:>7.2f} km  "
              f"{r['moving_time']}  {extra}  photos:{len(r['photos'])}   [{r['folder']}]")
    left = max(0, 52 - summary["credited_km"])
    print(f"  ACTUAL {summary['total_km']} km; CREDITED {summary['credited_km']:g} / 52 km → "
          + ("GOAL ACHIEVED ✔" if summary["goal_met"] else f"{left:.2f} km to go"))
    if input("\nType PUBLISH to write the files: ").strip().upper() != "PUBLISH":
        print("Cancelled. Nothing written."); return
    DATA.mkdir(parents=True, exist_ok=True)
    acts = [a for a in load(DATA / "activities.json") if a.get("week") != week_no] + records
    weeks = [w for w in load(DATA / "weeks.json") if w.get("week") != week_no] + [summary]
    for a in acts: a["credited_km"] = float(credited_distance(a))
    for w in weeks: w.update(week_score(w, acts))
    ids = [safe_id(a["id"]) for a in acts]
    if len(set(ids)) != len(ids):
        sys.exit("Duplicate activity IDs. Give each activity a unique id:. JSON files were not changed.")
    # Remove pages of activities that no longer exist in this week (e.g. a folder was renamed).
    for old in load(DATA / "activities.json"):
        if old.get("week") == week_no and old["id"] not in ids:
            shutil.rmtree(SITE / "activities" / safe_id(old["id"]), ignore_errors=True)
    save(DATA / "activities.json", sorted(acts, key=lambda a: (a["week"], a.get("number", 0), a["date"], a["id"])))
    save(DATA / "weeks.json", sorted(weeks, key=lambda w: w["week"]))
    build_all(SITE)
    write_rss(weeks)
    try: notify_subscribers(summary)
    except Exception as e: print(f"Email notification failed ({e.__class__.__name__}: {e}) — week is still published.")
    print(f"\nWeek page: https://52at52.app/weeks/week-{week_no:02d}/")
    for r in records:
        print(f"  Activity {r['number']} link: https://52at52.app/activities/{r['id']}/  (opens the week page at that activity)")
    print(f"Done. Review the changes locally, then commit/push normally.")


if __name__ == "__main__":
    main()
