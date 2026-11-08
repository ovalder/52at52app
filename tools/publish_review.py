"""
publish_review.py — publishes a product review to the REVIEW space.

Reads   content/reviews/<slug>/review.md  (+ optional image file in the same folder)
Writes  site/data/reviews.json and site/reviews/<slug>-en.html / -pt.html

Usage:  py tools/publish_review.py
Needs:  py -m pip install Markdown
"""
import json, re, shutil, sys
from build_pages import build_all, safe_id
from project_paths import ROOT, SITE, CONTENT as SOURCES, ensure_new_site
from datetime import datetime
from pathlib import Path

CONTENT = SOURCES / "reviews"
DATA, PAGES = SITE / "data" / "reviews.json", SITE / "reviews"
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic"}

try:
    import markdown
    md = lambda t: markdown.markdown(t.strip(), extensions=["extra"]) if t.strip() else ""
except ImportError:
    md = lambda t: "".join(f"<p>{p.strip()}</p>" for p in t.split("\n\n") if p.strip())


def na(v): return v is None or str(v).strip().upper() in ("", "NA", "N/A")

def kv_block(text):
    out = {}
    for line in text.splitlines():
        m = re.match(r"^([a-z_]+):\s*(.*)$", line.strip())
        if m: out[m.group(1)] = m.group(2).strip()
    return out

def stories(text):
    res = {"en": "", "pt": ""}
    for lang, body in re.findall(r"#\s*Story \((EN|PT)\)\s*\n(.*?)(?=\n#\s|\Z)", text, re.S):
        res[lang.lower()] = md(body)
    return res


def main():
    ensure_new_site()
    folders = sorted(f for f in CONTENT.iterdir() if (f / "review.md").exists())
    if not folders: sys.exit("No review folders found in content/reviews.")
    print("Available reviews:")
    for f in folders: print(f"  - {f.name}")
    slug = (sys.argv[1] if len(sys.argv) > 1 else input("\nSlug to publish: ")).strip()
    safe_id(slug)
    folder = CONTENT / slug
    md_path = folder / "review.md"
    if not md_path.exists(): sys.exit(f"Not found: {md_path}")

    raw = md_path.read_text(encoding="utf-8")
    fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.S)
    if not fm: sys.exit("review.md must start with a --- front-matter --- block")
    meta = kv_block(fm.group(1))
    if meta.get("slug") != slug:
        sys.exit(f"Slug mismatch: file says '{meta.get('slug')}' but folder is '{slug}'. Nothing changed.")
    story = stories(raw[fm.end():])
    if not story["en"]: sys.exit("No '# Story (EN)' section found. Nothing changed.")

    rating = int(meta.get("rating", 0))
    if not 0 <= rating <= 5: sys.exit("rating must be 0-5.")

    print(f"\nPublishing: {meta.get('title_en', slug)} ({meta.get('product', '')}, {rating} stars)")
    if input("Type PUBLISH to write the files: ").strip() != "PUBLISH":
        print("Cancelled. Nothing changed."); return
    PAGES.mkdir(parents=True, exist_ok=True)
    for lang in ("en", "pt"):
        if story[lang]:
            img = ""
            for f in sorted(folder.iterdir()):
                if f.suffix.lower() in IMG_EXT and not na(meta.get("image")) and f.stem in meta["image"]:
                    dst = SITE / "media" / "reviews" / f"{slug}{f.suffix.lower()}"
                    dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(f, dst)
                    img = f'<p><img src="../media/reviews/{dst.name}" alt="" style="max-width:100%;border-radius:12px"></p>'
                    break
            html = (f"<h2>{meta.get('title_' + lang, meta.get('title_en', slug))}</h2>"
                    f"<p class='muted'>{meta.get('product','')} · {'★'*rating}{'☆'*(5-rating)} · {meta.get('date','')}</p>"
                    + img + story[lang])
            (PAGES / f"{slug}-{lang}.html").write_text(html, encoding="utf-8")

    entry = {
        "slug": slug, "product": meta.get("product", ""), "category": meta.get("category", ""),
        "rating": rating, "date": meta.get("date", ""),
        "title_en": meta.get("title_en", slug), "title_pt": meta.get("title_pt", meta.get("title_en", slug)),
    }
    reviews = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else []
    reviews = [r for r in reviews if r["slug"] != slug] + [entry]
    reviews.sort(key=lambda r: r.get("date", ""), reverse=True)
    if DATA.exists():
        shutil.copy2(DATA, DATA.with_name(f"reviews.backup-{datetime.now():%Y%m%d-%H%M%S}.json"))
    DATA.write_text(json.dumps(reviews, ensure_ascii=False, indent=2), encoding="utf-8")
    build_all(SITE)
    print(f"Public review link: https://52at52.app/reviews/{slug}/")
    print(f"Done. Generated website files under {SITE}. Review changes, then commit/push normally.")


if __name__ == "__main__":
    main()
