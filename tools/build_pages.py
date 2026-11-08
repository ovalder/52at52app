"""Build static, directly shareable pages. No server-side framework required.

Run after editing guides/comparison data: py tools/build_pages.py
Weekly and review publishers call build_all() automatically.
URLs use immutable activity IDs and review slugs, never article titles.
"""
import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse, urljoin
from project_paths import ROOT, SITE, ensure_new_site
from challenge_rules import credited_distance, score, week_score

PUBLIC = "https://52at52.app/"


def esc(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def bi(en, pt, tag="span", attrs=""):
    return f'<{tag} class="txt" data-en="{esc(en)}" data-pt="{esc(pt)}" {attrs}>{en}</{tag}>'


def safe_id(value):
    value = str(value)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,99}", value):
        raise ValueError(f"Unsafe page identifier: {value!r}")
    return value


def read_data(name):
    path = SITE / "data" / (name + ".json")
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def relative_media(body, prefix):
    """Old fragments were injected into root pages, so ../media means site/media."""
    return re.sub(r'(src|href)=(["\'])(?:\.\./)*media/',
                  lambda m: m[1] + "=" + m[2] + prefix + "media/", body)


def article(path, en_title, pt_title, en_body, pt_body=None, description="", dark=False):
    prefix = "../" * (len(Path(path).parts) - 1)
    canonical = PUBLIC + path.removesuffix("index.html")
    title = esc(en_title)
    description = description or f"{en_title}. Stories and notes from the 52 at 52 challenge."
    first_image = re.search(r'<img\b[^>]*\bsrc=["\']([^"\']+)', relative_media(en_body, prefix), re.I)
    image_meta = ""
    if first_image:
        image = urljoin(canonical, html.unescape(first_image.group(1)))
        if urlparse(image).scheme == "https":
            image_meta = f'<meta property="og:image" content="{esc(image)}"><meta property="og:image:alt" content="{title}">'
    body_class = "tip-frame dark" if dark else "article-copy"
    body = (
        f'<div class="{body_class}" data-language="en">{relative_media(en_body, prefix)}</div>'
        f'<div class="{body_class}" data-language="pt" hidden>{relative_media(pt_body or en_body, prefix)}</div>'
    )
    content = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · 52 at 52</title><meta name="description" content="{esc(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article"><meta property="og:url" content="{canonical}">
<meta property="og:title" content="{title} · 52 at 52"><meta property="og:description" content="{esc(description)}">
{image_meta}
<meta name="twitter:card" content="summary"><meta name="theme-color" content="#f7f5ef">
<link rel="manifest" href="{prefix}manifest.webmanifest">
<link rel="apple-touch-icon" href="{prefix}icons/icon-192.png">
<link rel="icon" href="{prefix}icons/icon-192.png">
<link href="https://api.fontshare.com/v2/css?f[]=cabinet-grotesk@500,700,800&amp;f[]=satoshi@400,500,700&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefix}assets/style.css">
</head><body>
<header class="topbar"><a class="brand" href="{prefix}index.html" aria-label="52 at 52 home"><img src="{prefix}assets/brand-shield.png" alt="" width="48" height="46" style="width:48px;height:46px;object-fit:contain;vertical-align:middle;margin-right:8px">52<span>at</span>52 <small>km/week</small></a>
<nav><a class="site-link" href="{prefix}summaries/index.html">{bi("Summary", "Resumos")}</a>
<a class="site-link" href="{prefix}weeks/index.html">{bi("Weeks", "Semanas")}</a>
<a class="site-link" href="{prefix}tips.html">{bi("Tips", "Dicas")}</a>
<a class="site-link" href="{prefix}reviews.html">Reviews</a>
<a class="link-old" href="{prefix}archive/index.html">{bi("Original challenge ↗", "Desafio original ↗")}</a>
<div class="lang" role="group" aria-label="Language"><button data-lang="en" aria-pressed="true">EN</button>
<button data-lang="pt" aria-pressed="false">PT</button></div></nav></header>
<main><section class="page-head">
<p class="breadcrumb"><a href="{prefix}index.html">{bi("Challenge home", "Início do desafio")}</a></p>
<h1 data-page-title-en="{esc(en_title)}" data-page-title-pt="{esc(pt_title)}">{bi(esc(en_title), esc(pt_title))}</h1>
{body}</section>
<section class="comments"><h2>{bi("Comments", "Comentários")}</h2>
<p class="disclaimer">{bi(
    "Comments reflect their authors' opinions. I am not responsible for others' comments and may delete any comment I consider inappropriate at my sole discretion.",
    "Os comentários refletem a opinião de seus autores. Não me responsabilizo pelos comentários de outras pessoas e posso apagar qualquer comentário que considere inadequado, a meu exclusivo critério."
)}</p><div id="giscus-slot"></div></section></main>
<footer class="foot"><span>52 at 52 · San Jose, CA</span><a href="{prefix}index.html">{bi("Challenge home", "Início do desafio")}</a></footer>
<script src="{prefix}assets/config.js"></script><script src="{prefix}assets/app.js"></script>
<script type="module" src="{prefix}assets/comments.js"></script>
</body></html>"""
    target = SITE / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or target.read_text(encoding="utf-8") != content:
        target.write_text(content, encoding="utf-8")


def comparison(rows, columns, lang):
    head = "".join(f"<th>{esc(label[lang])}</th>" for _, label in columns)
    cells = []
    for row in rows:
        vals = [row.get(key + "_" + lang, row.get(key)) for key, _ in columns]
        cells.append("<tr>" + "".join(f"<td>{esc(v) if v not in (None, '') else '—'}</td>" for v in vals) + "</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(cells)}</tbody></table></div>'


def build_tips():
    for slug, en, pt in [
        ("runners-loop", "Runner's Loop (Heel Lock)", "Nó do Corredor (Heel Lock)"),
        ("runners-coffee", "The Runner's Coffee Boost", "O Ritual do Café para Corredores"),
        ("fuel-nutrition", "Fuel & Nutrition Strategy", "Estratégia de Nutrição & Hidratação"),
    ]:
        bodies = [(SITE / "guides" / f"{slug}-{lang}.html").read_text(encoding="utf-8") for lang in ("en", "pt")]
        if slug != "fuel-nutrition":
            bodies = [re.sub(r"<h[12]\b[^>]*>.*?</h[12]>", "", body, count=1, flags=re.S)
                      for body in bodies]
        for i, body in enumerate(bodies):
            video_ids = re.findall(r'https://www\.youtube(?:-nocookie)?\.com/embed/([A-Za-z0-9_-]+)', body)
            for video_id in dict.fromkeys(video_ids):
                label = "Abrir vídeo no YouTube" if i else "Open video on YouTube"
                body += f'<p><a href="https://www.youtube.com/watch?v={video_id}" target="_blank" rel="noopener noreferrer">{label}</a></p>'
            bodies[i] = body
        article(f"tips/{slug}/index.html", en, pt, *bodies, dark=(slug == "fuel-nutrition"))
    # Reuse original installation instructions, without translating them into invented advice.
    tips = (SITE / "tips.html").read_text(encoding="utf-8")
    match = re.search(r'<section[^>]*>\s*<h2[^>]*[^<]*.*?Install this site as an app.*?</section>', tips, re.S)
    if match:
        installation = re.sub(r'<p><a href="tips/install-the-app/[^"]*".*?</p>', "", match.group(0), flags=re.S)
        article("tips/install-the-app/index.html", "Install the app", "Instale o app", installation)
    columns = [
        ("category", {"en": "Category", "pt": "Categoria"}),
        ("name", {"en": "Product", "pt": "Produto"}),
        ("verdict", {"en": "Verdict", "pt": "Veredito"}),
        ("price", {"en": "Historical estimated price", "pt": "Preço estimado histórico"}),
        ("used_on", {"en": "Used on", "pt": "Usado em"}),
        ("note", {"en": "Notes", "pt": "Notas"}),
    ]
    note = "<p>Imported from the original challenge. Historical prices and personal experiences, not current quotations or medical advice.</p>"
    note_pt = "<p>Importado do desafio original. Preços históricos e experiências pessoais, não cotações atuais nem orientação médica.</p>"
    nutrition = read_data("nutrition")
    article("tips/nutrition/index.html", "Nutrition comparison", "Comparação de nutrição",
            note + comparison(nutrition, columns, "en"), note_pt + comparison(nutrition, columns, "pt"))
    shoe_columns = [
        ("name", {"en": "Shoe", "pt": "Tênis"}), ("use", {"en": "Use", "pt": "Uso"}),
        ("terrain", {"en": "Terrain", "pt": "Terreno"}), ("drop", {"en": "Drop", "pt": "Drop"}),
        ("stack", {"en": "Stack", "pt": "Stack"}), ("weight", {"en": "Weight", "pt": "Peso"}),
        ("mileage", {"en": "Recorded mileage", "pt": "Quilometragem registrada"}),
        ("status", {"en": "Status", "pt": "Situação"}), ("note", {"en": "Notes", "pt": "Notas"}),
    ]
    shoes = read_data("shoes")
    article("tips/shoes/index.html", "Shoe comparison", "Comparação de tênis",
            comparison(shoes, shoe_columns, "en"), comparison(shoes, shoe_columns, "pt"))


def clean_value(value):
    return value not in (None, "", "NA", "N/A")


def activity_body(a, lang):
    pt = lang == "pt"
    week = int(a["week"])
    fields = [
        ("type", "Activity", "Atividade"), ("date", "Date", "Data"),
        ("distance_km", "Distance (km)", "Distância (km)"), ("duration", "Duration", "Duração"),
        ("elevation_ft", "Elevation gain (ft)", "Ganho de elevação (ft)"),
        ("max_speed_kmh", "Maximum speed (km/h)", "Velocidade máxima (km/h)"),
        ("avg_speed_kmh", "Average speed (km/h)", "Velocidade média (km/h)"),
        ("pace_min_km", "Pace (min/km)", "Ritmo (min/km)"),
        ("location", "Location", "Local"), ("company", "Company", "Companhia"),
        ("shoes", "Shoes", "Tênis"), ("bike", "Bike", "Bike"),
        ("audiobook", "Audiobook", "Audiolivro"), ("event_name", "Event", "Evento"),
    ]
    facts = "".join(f"<div><dt>{esc(label_pt if pt else label_en)}</dt><dd>{esc(a[key])}</dd></div>"
                    for key, label_en, label_pt in fields if clean_value(a.get(key)))
    body = f'<p><a href="../../weeks/week-{week:02d}/index.html">{"Voltar para a semana" if pt else "Back to week"} {week}</a></p>'
    body += f'<dl class="activity-facts">{facts}</dl>'
    credit = float(credited_distance(a))
    body += (f'<p class="score-note">{credit:g} ' +
             ("km creditados para a meta semanal. Corrida conta integralmente; bicicleta conta pela metade."
              if pt else "credited km toward the weekly goal. Running counts in full; cycling counts at half distance.") +
             "</p>")
    body += (a.get("story") or {}).get(lang) or (a.get("story") or {}).get("en", "")
    for url in a.get("youtube") or []:
        if urlparse(url).scheme == "https":
            body += f'<p><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{"Assistir no" if pt else "Watch on"} YouTube</a></p>'
    coach = a.get("telecoach_url")
    if coach and urlparse(coach).scheme == "https":
        body += f'<p><a href="{esc(coach)}" target="_blank" rel="noopener noreferrer">teleCOACH dashboard</a></p>'
    photos = [f'<a href="../../{esc(url)}"><img loading="lazy" src="../../{esc(url)}" alt="{"Foto da atividade" if pt else "Activity photo"}"></a>'
              for url in a.get("photos") or [] if not urlparse(url).scheme and ".." not in Path(url).parts]
    return body + '<div class="photo-grid">' + "".join(photos) + "</div>"


def build_weeks():
    activities = read_data("activities")
    weeks = read_data("weeks")
    ids = [safe_id(a["id"]) for a in activities]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate activity IDs; use unique, permanent id: values.")
    for a in activities:
        title_en = a.get("title_en") or a["id"]
        title_pt = a.get("title_pt") or title_en
        article(f"activities/{safe_id(a['id'])}/index.html", title_en, title_pt,
                activity_body(a, "en"), activity_body(a, "pt"),
                description=f"{title_en}: {a.get('distance_km', '')} km, {a.get('duration', '')}. Week {a['week']} of 52 at 52.")
    for w in weeks:
        n = int(w["week"])
        scoring = week_score(w, activities)
        bodies = []
        for lang in ("en", "pt"):
            pt = lang == "pt"
            body = f'<p>{esc(w.get("start"))} → {esc(w.get("end"))}</p>'
            body += f'<p><strong>{scoring["credited_km"]:g} / 52 {"km creditados" if pt else "credited km"}</strong>'
            body += " · " + (("Meta atingida" if scoring["goal_met"] else "Meta não atingida") if pt
                             else ("Goal met" if scoring["goal_met"] else "Goal not met")) + "</p>"
            body += f'<p>{esc(w["total_km"])} {"km reais" if pt else "actual km"} · {esc(w.get("activities"))} {"atividades" if pt else "activities"}</p>'
            body += '<p class="score-note">' + ("Corrida + bicicleta ÷ 2. Distância, ritmo e velocidade de cada atividade continuam sendo os valores reais."
                      if pt else "Run km + ride km ÷ 2. Each activity retains its actual distance, pace and speed.") + "</p>"
            body += (w.get("story") or {}).get(lang) or (w.get("story") or {}).get("en", "")
            body += '<ul class="article-links">'
            for a in activities:
                if a["week"] == n:
                    title = a.get("title_" + lang) or a.get("title_en") or a["id"]
                    body += f'<li><a href="../../activities/{safe_id(a["id"])}/index.html">{esc(title)}</a> · {esc(a["date"])} · {esc(a["distance_km"])} km</li>'
            bodies.append(body + "</ul>")
        article(f"weeks/week-{n:02d}/index.html", w.get("title_en") or f"Week {n}",
                w.get("title_pt") or f"Semana {n}", *bodies,
                description=f"Week {n}: {scoring['credited_km']:g}/52 credited km; {w['total_km']} actual km.")
    index_bodies = []
    for lang in ("en", "pt"):
        body = ""
        if weeks:
            cumulative = score(activities)["credited_km"]
            actual = sum(w["total_km"] for w in weeks)
            met = sum(week_score(w, activities)["goal_met"] for w in weeks)
            body = (f'<p><strong>{cumulative:g} {"km creditados no desafio" if lang == "pt" else "challenge credited km"}</strong>'
                    f' · {actual:g} {"km reais" if lang == "pt" else "actual km"}'
                    f' · {met}/{len(weeks)} {"semanas com meta atingida" if lang == "pt" else "published weeks meeting the goal"}</p>')
        body += '<ul class="article-links">'
        for w in sorted(weeks, key=lambda row: row["week"], reverse=True):
            title = w.get("title_" + lang) or f"Week {w['week']}"
            credit = week_score(w, activities)["credited_km"]
            body += f'<li><a href="week-{int(w["week"]):02d}/index.html">{esc(title)}</a> · {credit:g}/52 {"km creditados" if lang == "pt" else "credited km"} · {esc(w["total_km"])} {"km reais" if lang == "pt" else "actual km"}</li>'
        index_bodies.append(body + "</ul>" if weeks else "<p>" + (
            "Nenhuma semana publicada ainda. O desafio começa em 7 de novembro de 2026."
            if lang == "pt" else "No weeks published yet. The challenge starts November 7, 2026.") + "</p>")
    article("weeks/index.html", "Weeks & activities", "Semanas e atividades", *index_bodies)


def build_summaries():
    import markdown
    entries = sorted(read_data("summaries"), key=lambda s: s["date"], reverse=True)
    for entry in entries:
        slug = safe_id(entry["slug"])
        bodies = []
        for lang in ("en", "pt"):
            source = ROOT / "content" / "summaries" / slug / f"{lang}.md"
            bodies.append(markdown.markdown(source.read_text(encoding="utf-8"), extensions=["extra"]))
        article(f"summaries/{slug}/index.html", entry["title_en"], entry["title_pt"],
                *bodies, description=entry["description_en"])
    bodies = []
    for lang in ("en", "pt"):
        body = "<p>" + ("Os motivos e os marcos do novo desafio." if lang == "pt"
                        else "The reasons and milestones behind the new challenge.") + "</p>"
        body += '<div class="tip-grid">'
        for entry in entries:
            body += (f'<a class="tip-card" href="{safe_id(entry["slug"])}/index.html">'
                     f'<span class="badge green">{esc(entry["date"])}</span>'
                     f'<span class="tip-title">{esc(entry["title_" + lang])}</span>'
                     f'<span class="tip-desc">{esc(entry["description_" + lang])}</span></a>')
        bodies.append(body + "</div>")
    article("summaries/index.html", "Summary", "Resumos", *bodies)

def build_reviews():
    for review in read_data("reviews"):
        slug = safe_id(review["slug"])
        bodies = []
        for lang in ("en", "pt"):
            path = SITE / "reviews" / f"{slug}-{lang}.html"
            fallback = SITE / "reviews" / f"{slug}-en.html"
            body = (path if path.exists() else fallback).read_text(encoding="utf-8")
            bodies.append(re.sub(r"<h2>.*?</h2>", "", body, count=1, flags=re.S))
        article(f"reviews/{slug}/index.html", review["title_en"],
                review.get("title_pt") or review["title_en"], *bodies,
                description=f"{review.get('product', '')}: {review['title_en']}")


def build_all(site=None):
    global SITE
    if site is not None:
        SITE = Path(site)
    build_tips()
    build_weeks()
    build_reviews()
    build_summaries()


if __name__ == "__main__":
    ensure_new_site()
    build_all()
    print("Built permanent pages for tips, comparisons, reviews, weeks and activities.")
