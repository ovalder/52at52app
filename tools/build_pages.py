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


def article(path, en_title, pt_title, en_body, pt_body=None, description="", dark=False, wide=False, image=None):
    prefix = "../" * (len(Path(path).parts) - 1)
    canonical = PUBLIC + path.removesuffix("index.html")
    title = esc(en_title)
    description = description or f"{en_title}. Stories and notes from the 52 at 52 challenge."
    first_image = re.search(r'<img\b[^>]*\bsrc=["\']([^"\']+)', relative_media(en_body, prefix), re.I)
    image_meta = ""
    if image or first_image:
        image = urljoin(canonical, image or html.unescape(first_image.group(1)))
        if urlparse(image).scheme == "https":
            image_meta = f'<meta property="og:image" content="{esc(image)}"><meta property="og:image:alt" content="{title}">'
    body_class = "tip-frame dark" if dark else ("week-copy" if wide else "article-copy")
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
<meta name="twitter:card" content="{'summary_large_image' if image_meta else 'summary'}"><meta name="theme-color" content="#f7f5ef">
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


MONTHS = {"en": "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(),
          "pt": "jan fev mar abr mai jun jul ago set out nov dez".split()}
DAYS = {"en": "Mon Tue Wed Thu Fri Sat Sun".split(), "pt": "seg ter qua qui sex sáb dom".split()}


def nice_date(iso, lang, weekday=True, year=False):
    from datetime import date
    try:
        d = date.fromisoformat(str(iso))
    except ValueError:
        return esc(iso)
    m = MONTHS[lang][d.month - 1]
    core = f"{d.day} {m}" if lang == "pt" else f"{m} {d.day}"
    if year: core += f" {d.year}" if lang == "pt" else f", {d.year}"
    return (DAYS[lang][d.weekday()] + ", " if weekday else "") + core


def num(value, lang, digits=2):
    value = float(value)
    text = f"{value:,.{digits}f}"
    if digits: text = text.rstrip("0").rstrip(".")
    return text.translate(str.maketrans(",.", ".,")) if lang == "pt" else text


def hours(seconds):
    h, rem = divmod(int(seconds or 0), 3600)
    return f"{h}:{rem // 60:02d}:{rem % 60:02d}"


def week_title(w, lang):
    return w.get("title_" + lang) or w.get("title_en") or (f"Semana {w['week']}" if lang == "pt" else f"Week {w['week']}")


def activity_title(a, lang):
    return a.get("title_" + lang) or a.get("title_en") or a["id"]


def safe_media(url):
    return not urlparse(url).scheme and ".." not in Path(url).parts


def activity_tile(a, lang, count):
    pt = lang == "pt"
    kind = {"run": ("Run", "Corrida"), "ride": ("Ride", "Pedal")}[a["type"]][pt]
    event = a.get("event_name")
    if clean_value(event) and clean_value(a.get("event_url")) and urlparse(a["event_url"]).scheme == "https":
        event = f'<a href="{esc(a["event_url"])}" target="_blank" rel="noopener noreferrer">{esc(event)}</a>'
    elif clean_value(event):
        event = esc(event)
    facts = [
        ("Activity", "Atividade", esc(kind)),
        ("Date", "Data", nice_date(a["date"], lang)),
        ("Distance", "Distância", f'{num(a["distance_km"], lang)} km'),
        ("Moving time", "Tempo em movimento", esc(a.get("moving_time") or a.get("duration"))),
        ("Elapsed time", "Tempo total", esc(a.get("elapsed_time")) if a.get("elapsed_time") else None),
        ("Pace", "Ritmo", f'{esc(a["pace_min_km"])} /km' if a.get("pace_min_km") else None),
        ("Average speed", "Velocidade média", f'{num(a["avg_speed_kmh"], lang, 1)} km/h' if a["type"] == "ride" and a.get("avg_speed_kmh") else None),
        ("Max speed", "Velocidade máxima", f'{num(a["max_speed_kmh"], lang, 1)} km/h' if clean_value(a.get("max_speed_kmh")) else None),
        ("Elevation gain", "Ganho de elevação", f'{num(a["elevation_m"], lang, 0)} m' if clean_value(a.get("elevation_m")) else None),
        ("Calories", "Calorias", f'{num(a["calories"], lang, 0)} kcal' if clean_value(a.get("calories")) else None),
        ("Event", "Evento", event if clean_value(a.get("event_name")) else None),
        ("Location", "Local", esc(a["location"]) if clean_value(a.get("location")) else None),
        ("Company", "Companhia", esc(a["company"]) if clean_value(a.get("company")) else None),
        ("Shoes", "Tênis", esc(a["shoes"]) if clean_value(a.get("shoes")) else None),
        ("Bike", "Bike", esc(a["bike"]) if clean_value(a.get("bike")) else None),
        ("Audiobook", "Audiolivro", esc(a["audiobook"]) if clean_value(a.get("audiobook")) else None),
    ]
    dl = "".join(f"<div><dt>{label_pt if pt else label_en}</dt><dd>{value}</dd></div>"
                 for label_en, label_pt, value in facts if value)
    aid = safe_id(a["id"])
    photos = [u for u in a.get("photos") or [] if safe_media(u)]
    gallery = ""
    if photos:
        alt = "Foto da atividade" if pt else "Activity photo"
        slides = "".join(f'<figure><a href="../../{esc(u)}" target="_blank" rel="noopener"><img loading="lazy" src="../../{esc(u)}" alt="{alt} {i}"></a></figure>'
                         for i, u in enumerate(photos, 1))
        controls = ("" if len(photos) == 1 else
                    f'<button type="button" class="slide-btn prev" aria-label="{"Foto anterior" if pt else "Previous photo"}">‹</button>'
                    f'<button type="button" class="slide-btn next" aria-label="{"Próxima foto" if pt else "Next photo"}">›</button>'
                    f'<span class="slide-count">1 / {len(photos)}</span>')
        gallery = f'<div class="slideshow" data-slideshow><div class="slides">{slides}</div>{controls}</div>'
    links = []
    for key, label in (("strava_url", "Strava"), ("telecoach_url", "teleCOACH")):
        if clean_value(a.get(key)) and urlparse(a[key]).scheme == "https":
            links.append(f'<a href="{esc(a[key])}" target="_blank" rel="noopener noreferrer">{label} ↗</a>')
    for url in a.get("youtube") or []:
        if urlparse(url).scheme == "https":
            links.append(f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">YouTube ↗</a>')
    tagline = a.get("tagline_" + lang) or a.get("tagline_en")
    summary = a.get("summary_" + lang) or a.get("summary_en")
    story = (a.get("story") or {}).get(lang) or (a.get("story") or {}).get("en", "")
    of = f'{"Atividade" if pt else "Activity"} {a.get("number", "")} {"de" if pt else "of"} {count}'
    credit = float(credited_distance(a))
    credit_note = (f'{num(credit, lang)} {"km creditados" if pt else "credited km"}'
                   + (f' ({"bicicleta conta pela metade" if pt else "cycling counts at half"})' if a["type"] == "ride" else ""))
    return f"""<article class="activity-tile" id="{aid}">
<header class="tile-head"><p class="tile-num"><span class="badge {'cyan' if a['type'] == 'ride' else 'orange'}">{esc(of)}</span>
<span class="muted">{nice_date(a['date'], lang)} · {esc(kind)} · {credit_note}</span></p>
<h3>{esc(activity_title(a, lang))}</h3>
{f'<p class="tile-tagline">{esc(tagline)}</p>' if clean_value(tagline) else ''}
<a class="tile-anchor" href="#{aid}">{"Link para esta atividade" if pt else "Link to this activity"}</a></header>
{gallery}
{f'<p class="tile-summary">{esc(summary)}</p>' if clean_value(summary) else ''}
<dl class="activity-facts">{dl}</dl>
{f'<p class="tile-links">{" · ".join(links)}</p>' if links else ''}
<div class="tile-story">{story}</div>
</article>"""


def week_body(w, acts, scoring, lang):
    pt = lang == "pt"
    credited = scoring["credited_km"]
    pct = min(100, credited / 52 * 100)
    left = max(0.0, 52 - credited)
    if scoring["goal_met"]:
        status = (f'<p class="week-status done">✓ {"Desafio da semana cumprido!" if pt else "Weekly challenge achieved!"}'
                  f' <span>{num(credited, lang)} / 52 km</span></p>')
    else:
        status = (f'<p class="week-status open">{"Faltam" if pt else ""} <b>{num(left, lang)} km</b> '
                  f'{"para a meta" if pt else "to go"} · {"semana em andamento" if pt else "week in progress"}</p>')
    by_type = w.get("km_by_type") or {}
    split = " + ".join(f'{num(km, lang)} km {({"run": "corrida", "ride": "bicicleta"} if pt else {"run": "run", "ride": "ride"})[k]}'
                       for k, km in by_type.items())
    stats = [
        (len(acts), "atividades" if pt else ("activity" if len(acts) == 1 else "activities")),
        (f'{num(w["total_km"], lang)} km', ("km reais" if pt else "actual km") if not split or len(by_type) < 2 else split),
        (hours(w.get("seconds")), "em movimento" if pt else "moving time"),
    ]
    if w.get("elevation_m"):
        stats.append((f'{num(w["elevation_m"], lang, 0)} m', "de subida" if pt else "climbed"))
    stat_html = "".join(f"<li><b>{v}</b><span>{esc(l)}</span></li>" for v, l in stats)
    body = f"""<div class="week-hero{' achieved' if scoring['goal_met'] else ''}">
<p class="week-dates">{nice_date(w['start'], lang)} → {nice_date(w['end'], lang, year=True)}</p>
<p class="week-total"><b>{num(credited, lang)}</b><span>/ 52 {"km creditados" if pt else "credited km"}</span></p>
<div class="meter-bar" role="progressbar" aria-valuemin="0" aria-valuemax="52" aria-valuenow="{credited:g}"><span style="width:{pct:.1f}%"></span></div>
{status}
<ul class="week-stats">{stat_html}</ul>
<p class="score-note">{"Corrida + bicicleta ÷ 2. Cada atividade mostra a distância, o ritmo e a velocidade reais." if pt else "Run km + ride km ÷ 2. Each activity shows its actual distance, pace and speed."}</p>
</div>"""
    story = (w.get("story") or {}).get(lang) or (w.get("story") or {}).get("en", "")
    if story:
        body += f'<div class="week-story">{story}</div>'
    body += f'<h2 class="week-acts-title">{"Atividades da semana" if pt else "This week’s activities"} <span>({len(acts)})</span></h2>'
    body += '<ol class="activity-index">'
    for a in acts:
        kind = {"run": ("Run", "Corrida"), "ride": ("Ride", "Pedal")}[a["type"]][pt]
        thumb = next((u for u in a.get("photos") or [] if safe_media(u)), None)
        img = f'<img src="../../{esc(thumb)}" alt="" loading="lazy">' if thumb else f'<span class="noimg">{a.get("number", "")}</span>'
        body += (f'<li><a href="#{safe_id(a["id"])}">{img}<span class="ai-text"><span class="ai-num">'
                 f'{"Atividade" if pt else "Activity"} {a.get("number", "")} · {nice_date(a["date"], lang)}</span>'
                 f'<span class="ai-title">{esc(activity_title(a, lang))}</span>'
                 f'<span class="ai-meta">{esc(kind)} · {num(a["distance_km"], lang)} km</span></span></a></li>')
    body += "</ol>"
    body += "".join(activity_tile(a, lang, len(acts)) for a in acts)
    return body


def activity_redirect(a, week_no):
    """Short, shareable /activities/<id>/ URL that opens the week page at that activity
    (one page and one comment thread per week). Keeps its own preview title/photo."""
    aid = safe_id(a["id"])
    week_url = f"{PUBLIC}weeks/week-{week_no:02d}/"
    target = f"../../weeks/week-{week_no:02d}/index.html#{aid}"
    title = esc(activity_title(a, "en"))
    desc = esc(f"{a['distance_km']} km · {a.get('moving_time') or a.get('duration')}. Week {week_no} of 52 at 52.")
    photo = next((u for u in a.get("photos") or [] if safe_media(u)), None)
    image = f'<meta property="og:image" content="{esc(PUBLIC + photo)}">' if photo else ""
    content = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · 52 at 52</title><meta name="description" content="{desc}">
<link rel="canonical" href="{week_url}">
<meta property="og:type" content="article"><meta property="og:url" content="{PUBLIC}activities/{aid}/">
<meta property="og:title" content="{title} · 52 at 52"><meta property="og:description" content="{desc}">{image}
<meta name="twitter:card" content="{'summary_large_image' if photo else 'summary'}">
<meta http-equiv="refresh" content="0; url={target}">
<script>location.replace("{target}");</script>
</head><body><p><a href="{target}">{title}</a></p></body></html>"""
    out = SITE / "activities" / aid / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")


def build_weeks():
    activities = read_data("activities")
    weeks = read_data("weeks")
    ids = [safe_id(a["id"]) for a in activities]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate activity IDs; use unique, permanent id: values.")
    for w in weeks:
        n = int(w["week"])
        acts = sorted((a for a in activities if a["week"] == n),
                      key=lambda a: (a.get("number", 0), a["date"], a["id"]))
        for a in acts:
            activity_redirect(a, n)
        scoring = week_score(w, activities)
        cover = next((u for a in acts for u in a.get("photos") or [] if safe_media(u)), None)
        state = "goal achieved" if scoring["goal_met"] else f"{max(0, 52 - scoring['credited_km']):.2f} km to go"
        article(f"weeks/week-{n:02d}/index.html", week_title(w, "en"), week_title(w, "pt"),
                week_body(w, acts, scoring, "en"), week_body(w, acts, scoring, "pt"),
                description=f"Week {n}: {scoring['credited_km']:g}/52 credited km across {len(acts)} activities ({state}).",
                wide=True, image=(PUBLIC + cover) if cover else None)
    index_bodies = []
    for lang in ("en", "pt"):
        pt = lang == "pt"
        body = ""
        if weeks:
            cumulative = score(activities)["credited_km"]
            actual = sum(w["total_km"] for w in weeks)
            met = sum(week_score(w, activities)["goal_met"] for w in weeks)
            body = (f'<p><strong>{num(cumulative, lang)} {"km creditados no desafio" if pt else "challenge credited km"}</strong>'
                    f' · {num(actual, lang)} {"km reais" if pt else "actual km"}'
                    f' · {met}/{len(weeks)} {"semanas com meta atingida" if pt else "weeks meeting the goal"}</p>')
        body += '<ul class="week-list">'
        for w in sorted(weeks, key=lambda row: row["week"], reverse=True):
            sc = week_score(w, activities)
            pct = min(100, sc["credited_km"] / 52 * 100)
            flag = (f'<span class="badge green">✓ {"Meta cumprida" if pt else "Goal achieved"}</span>' if sc["goal_met"]
                    else f'<span class="badge orange">{"Em andamento" if pt else "In progress"}</span>')
            body += (f'<li><a href="week-{int(w["week"]):02d}/index.html"><span class="wl-head"><b>{esc(week_title(w, lang))}</b>{flag}</span>'
                     f'<span class="muted">{nice_date(w["start"], lang, weekday=False)} → {nice_date(w["end"], lang, weekday=False, year=True)}'
                     f' · {w.get("activities", 0)} {"atividades" if pt else "activities"}</span>'
                     f'<span class="meter-bar"><span style="width:{pct:.1f}%"></span></span>'
                     f'<span>{num(sc["credited_km"], lang)} / 52 {"km creditados" if pt else "credited km"}</span></a></li>')
        index_bodies.append(body + "</ul>" if weeks else "<p>" + (
            "Nenhuma semana publicada ainda. O desafio começa em 7 de novembro de 2026."
            if pt else "No weeks published yet. The challenge starts November 7, 2026.") + "</p>")
    article("weeks/index.html", "Weeks & activities", "Semanas e atividades", *index_bodies, wide=True)


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
