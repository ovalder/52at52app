"""
publish_week.py — publishes one week of the 52 at 52 challenge.

Reads   content/weeks/week-XX/week.md  (+ photos in the same folder or photos/)
Writes  site/data/activities.json, site/data/weeks.json,
        site/media/week-XX/*.webp  (optimized photos)
Computes actual pace/speed and the 52 credited-km goal (run km + ride km / 2).

Usage:  py tools/publish_week.py 1
Needs:  py -m pip install Pillow Markdown
"""
import json, re, shutil, sys
from build_pages import build_all, safe_id
from project_paths import ROOT, SITE, CONTENT as SOURCES, PRIVATE, ensure_new_site
from datetime import datetime
from pathlib import Path
from challenge_rules import credited_distance, score, week_score

CONTENT = SOURCES / "weeks"
DATA = SITE / "data"
NUMERIC = {"distance_km", "elevation_ft", "max_speed_kmh"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic"}

try:
    import markdown
    md = lambda t: markdown.markdown(t.strip(), extensions=["extra"]) if t.strip() else ""
except ImportError:
    md = lambda t: "".join(f"<p>{p.strip()}</p>" for p in t.split("\n\n") if p.strip())


def na(v): return v is None or str(v).strip().upper() in ("", "NA", "N/A")

def secs(hms):
    parts = [int(x) for x in hms.strip().split(":")]
    while len(parts) < 3: parts.insert(0, 0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]

def fmt_pace(s_per_km):
    m, s = divmod(round(s_per_km), 60); return f"{m}:{s:02d}"

def kv_block(text):
    out = {}
    for line in text.splitlines():
        m = re.match(r"^([a-z_]+):\s*(.*)$", line.strip())
        if m: out[m.group(1)] = m.group(2).strip()
    return out

def stories(text):
    res = {"en": "", "pt": ""}
    for lang, body in re.findall(r"#{1,3} Story \((EN|PT)\)\s*\n(.*?)(?=\n#{1,3} |\Z)", text, re.S):
        res[lang.lower()] = md(body)
    return res


def parse(md_path):
    raw = md_path.read_text(encoding="utf-8")
    fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.S)
    if not fm: sys.exit("week.md must start with a --- front-matter --- block")
    week = kv_block(fm.group(1)); body = raw[fm.end():]
    chunks = re.split(r"^## Activity\s*$", body, flags=re.M)
    head = chunks[0]
    week_story = {}
    for lang, txt in re.findall(r"# Week story \((EN|PT)\)\s*\n(.*?)(?=\n# |\Z)", head, re.S):
        week_story[lang.lower()] = md(re.sub(r"<!--.*?-->", "", txt, flags=re.S))
    acts = []
    for i, ch in enumerate(chunks[1:], 1):
        meta_txt = re.split(r"^### ", ch, maxsplit=1, flags=re.M)[0]
        a = kv_block(meta_txt)
        a["story"] = stories(ch)
        acts.append(a)
    return week, week_story, acts


def process_photos(week_no, names, src_dir):
    if not names: return []
    out_dir = SITE / "media" / f"week-{week_no:02d}"; out_dir.mkdir(parents=True, exist_ok=True)
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
            im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
            im.thumbnail((2000, 2000)); im.save(dst, "WEBP", quality=82)
        except Exception as e:
            dst = out_dir / src.name; shutil.copy2(src, dst)
            print(f"  ! copied without optimizing ({e.__class__.__name__}): {n}")
        result.append(f"media/week-{week_no:02d}/{dst.name}")
    return result


def build(week_no):
    folder = CONTENT / f"week-{week_no:02d}"
    md_path = folder / "week.md"
    if not md_path.exists(): sys.exit(f"Not found: {md_path}")
    week, week_story, acts = parse(md_path)
    if int(week.get("week", -1)) != week_no:
        sys.exit(f"week.md says week: {week.get('week')} but you asked for week {week_no}. Nothing changed.")

    records = []
    for i, a in enumerate(acts, 1):
        for req in ("type", "date", "distance_km", "duration"):
            if na(a.get(req)): sys.exit(f"Activity {i}: '{req}' is required.")
        rec = {"id": safe_id(a.get("id") or f"w{week_no:02d}-a{i}"), "week": week_no}
        for k, v in a.items():
            if k == "story": continue
            if na(v): rec[k] = None
            elif k in NUMERIC: rec[k] = float(v)
            else: rec[k] = v
        rec["type"] = rec["type"].lower()
        rec["credited_km"] = float(credited_distance(rec))
        rec["seconds"] = secs(a["duration"])
        km = rec["distance_km"]
        rec["avg_speed_kmh"] = round(km / (rec["seconds"] / 3600), 2) if rec["seconds"] else None
        rec["pace_min_km"] = fmt_pace(rec["seconds"] / km) if rec["type"] == "run" and km else None
        rec["youtube"] = [u.strip() for u in (a.get("youtube") or "").split(",") if not na(u)]
        names = [p.strip() for p in (a.get("photos") or "").split(",") if not na(p)]
        rec["photos"] = process_photos(week_no, names, folder)
        rec["story"] = a["story"]
        records.append(rec)

    total = round(sum(r["distance_km"] for r in records), 2)
    by_type = {}
    for r in records: by_type[r["type"]] = round(by_type.get(r["type"], 0) + r["distance_km"], 2)
    summary = {
        "week": week_no, "start": week.get("start"), "end": week.get("end"),
        "title_en": week.get("title_en"), "title_pt": week.get("title_pt"),
        "story": week_story, "activities": len(records),
        "total_km": total, "km_by_type": by_type,
        "seconds": sum(r["seconds"] for r in records),
        "elevation_ft": round(sum(r.get("elevation_ft") or 0 for r in records)),
        **score(records),
    }
    return summary, records


def load(p): return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []

def save(p, data):
    if p.exists():
        bk = p.with_name(f"{p.stem}.backup-{datetime.now():%Y%m%d-%H%M%S}{p.suffix}")
        shutil.copy2(p, bk)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_rss(weeks):
    """Regenerates site/rss.xml from all published weeks (free RSS-to-email
    services like Blogtrottr or follow.it can use it)."""
    base = "https://52at52.app/"
    items = []
    for w in sorted(weeks, key=lambda w: w["week"], reverse=True):
        title = w.get("title_en") or f"Week {w['week']}"
        link = f"{base}weeks/week-{w['week']:02d}/"
        desc = (f"{w['credited_km']} credited km / 52; {w['total_km']} actual km "
                f"across {w['activities']} activities; "
                f"goal {'met' if w['goal_met'] else 'not met'}.")
        items.append(f"<item><title>{title}</title><link>{link}</link>"
                    f"<description>{desc}</description><pubDate>{w.get('end') or ''}</pubDate></item>")
    rss = (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
           f"<title>52 at 52 - 52 km a Week</title><link>{base}</link>"
           f"<description>52 credited km each week: run km + ride km / 2.</description>"
           + "".join(items) + "</channel></rss>")
    (SITE / "rss.xml").write_text(rss, encoding="utf-8")


def notify_subscribers(summary, records):
    """Optional: email subscribers that a new week is up.
    Configure _private/notify.ini (see README) and keep the list in
    _private/subscribers.json (never commit this file)."""
    import smtplib
    from email.mime.text import MIMEText
    ini = PRIVATE / "notify.ini"
    subs_file = PRIVATE / "subscribers.json"
    if not ini.exists() or not subs_file.exists():
        print("Email notification skipped (_private/notify.ini or subscribers list not configured).")
        return
    cfg = dict(re.findall(r"^(\w+)\s*=\s*(.+)$", ini.read_text(encoding="utf-8"), re.M))
    subs = load(subs_file)
    if not subs:
        print("Email notification skipped (subscriber list is empty)."); return
    body = (f"Week {summary['week']} is up: {summary['credited_km']} credited km / 52 "
            f"(run km + ride km / 2), {summary['total_km']} actual km "
            f"across {summary['activities']} activities "
            f"(goal {'met' if summary['goal_met'] else 'not met'}).\n\n"
            f"Read it: https://52at52.app/weeks/week-{summary['week']:02d}/\n\n"
            "You receive this because you subscribed to 52 at 52. Unsubscribe anytime by replying.")
    msg = MIMEText(body)
    msg["Subject"] = f"52 at 52 - Week {summary['week']} published"
    msg["From"] = cfg["from_email"]
    msg["To"] = cfg["from_email"]
    with smtplib.SMTP(cfg["smtp_host"], int(cfg.get("smtp_port", 587))) as s:
        s.starttls()
        s.login(cfg["username"], cfg["password"])
        s.send_message(msg, to_addrs=[x["email"] if isinstance(x, dict) else x for x in subs])
    print(f"Notification email sent to {len(subs)} subscriber(s).")


def main():
    ensure_new_site()
    week_no = int(sys.argv[1]) if len(sys.argv) > 1 else int(input("Week number to publish: "))
    summary, records = build(week_no)
    print(f"\nWeek {week_no}  ({summary['start']} → {summary['end']})")
    for r in records:
        extra = f"pace {r['pace_min_km']}/km" if r["pace_min_km"] else f"{r['avg_speed_kmh']} km/h"
        print(f"  {r['date']}  {r['type']:<5} {r['distance_km']:>6.2f} km  {r['duration']}  {extra}  photos:{len(r['photos'])}")
    print(f"  ACTUAL {summary['total_km']} km; CREDITED {summary['credited_km']} / 52 km "
          f"(run km + ride km / 2) → goal {'MET ✔' if summary['goal_met'] else 'NOT met ✘'}")
    if input("\nType PUBLISH to write the files: ").strip() != "PUBLISH":
        print("Cancelled. Nothing written."); return
    DATA.mkdir(parents=True, exist_ok=True)
    acts = [a for a in load(DATA / "activities.json") if a.get("week") != week_no] + records
    weeks = [w for w in load(DATA / "weeks.json") if w.get("week") != week_no] + [summary]
    for a in acts:
        a["credited_km"] = float(credited_distance(a))
    for w in weeks:
        w.update(week_score(w, acts))
    ids = [safe_id(a["id"]) for a in acts]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate activity IDs. Give each new activity a unique id:. JSON files were not changed.")
    save(DATA / "activities.json", sorted(acts, key=lambda a: (a["week"], a["date"], a["id"])))
    save(DATA / "weeks.json", sorted(weeks, key=lambda w: w["week"]))
    build_all(SITE)
    write_rss(weeks)
    try:
        notify_subscribers(summary, records)
    except Exception as e:
        print(f"Email notification failed ({e.__class__.__name__}: {e}) — week is still published.")
    print(f"Public week link: https://52at52.app/weeks/week-{week_no:02d}/")
    for activity in records:
        print(f"  Activity link: https://52at52.app/activities/{activity['id']}/")
    print(f"Done. Generated website files under {SITE}. Review changes, then commit/push normally.")


if __name__ == "__main__":
    main()
