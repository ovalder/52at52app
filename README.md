# 52at52: clean-start website

This ZIP is a complete root-layout starter, not a migration/update package.
It already includes your uploaded **52at52.jpg**, the matching website logo,
and 192px/512px smartphone home-screen icons. There is ONE website, optionally
installable through a compatible browser, not a separate mobile application.

No Python migration, branding or logo script is needed to set up this package.

## Back up before replacing files

Make a full copy of the existing destination folder somewhere else first.
Keep your untouched original 52@52 website safe too.

If the destination is already a Git repository, do NOT delete its hidden `.git`
folder or existing `.github` configuration. Do not copy a second `.git` folder
from the old website. Keep any private settings/credentials outside public files.

## Extract directly into your new website folder

Extract the CONTENTS of this ZIP into your `52at52` folder. There is no extra
top-level folder and no `site/` folder. You should immediately see:

```text
52at52/
  index.html
  assets/
  icons/
  data/
  tips.html
  tips/
  reviews.html
  reviews/
  weeks/
  activities/
  manifest.webmanifest
  sw.js
  CNAME
  archive/
    index.html
    original/
      COPY-OLD-SITE-HERE.md
  content/
  tools/
  comments-api/
  README.md
  PUBLISHING.md
```

The homepage already has the new challenge introduction, with weeks beginning
Saturday November 7, 2026, through Friday November 13, 2026.
The launch data has no published weeks or reviews. Example Markdown files in
`content/` are editing templates, not your real activity history.
The weekly target is 52 credited km: running km + cycling km / 2. A cycling-only
week requires 104 actual km. Activity distance, pace and speed remain actual values.
The Summary section includes the first Season 2 story in English and Portuguese.

## Copy the old website manually

Leave the NEW `archive/index.html` in place. It is an outer viewer with a
permanent link back to the new challenge.

Copy your ORIGINAL website's public files INTO `archive/original/`:

```text
archive/original/
  index.html              Original 52@52 homepage
  posts.json
  run_images.json
  media/                  Original logo, photos and other public media
  posts/
  summaries/
  tips/
  guides/
  data/
  ...other public assets used by the old website
```

Copy the old folder's CONTENTS, not an extra enclosing `52-at-52` folder.
Use an untouched backup if an earlier branding update altered your old site:
the viewer does not restore or rebrand what you copy.
Do not copy `.git`, `.github`, `_private`, `.env`, subscriber lists, local
maintenance scripts or local draft/source folders that are not public assets.
You do not need the old CNAME inside the archive.

The old site's logo and all its HTML/JSON/media remain unchanged. Its relative
links resolve inside `archive/original/`. The viewer also normalizes common
public HTML asset paths at runtime, such as `../media/` in injected fragments
and `/media/`, without editing your copied files. Arbitrary custom paths, CSS
URLs and external integrations are not generally rewritten; review them after
copying. This package does not create
redirects for all old root-level article URLs.

Visitors click “Original challenge” on the new site to open the viewer.
The return bar remains above the old website, including when it changes tabs
or opens a relative article within the viewer.

## Upload through your usual GitHub workflow

Use your existing repository/upload process, with `index.html` at the published
website root. No npm build and no migration script are needed.
This assumes your current hosting publishes the repository root.

The included CNAME is `52at52.app`. DNS and the GitHub Pages custom-domain setting
must already be configured for that domain, or configured separately. Extracting
a ZIP does not change domain or hosting settings.

Do not judge the JSON-driven pages by double-clicking `index.html`: browsers may
block local-file data requests. Check the published HTTPS website instead.

## Check after uploading

- New homepage: your uploaded 52at52 logo and the new weekly challenge.
- Tips/Reviews/Weeks: correct navigation; EN/PT buttons work.
- Original challenge: original 52@52 title/logo, Data, runs, photos and summary.
- Return bar: takes you back to the new homepage.
- Smartphone installation: instructions are under Tips → Install the app.
- Permanent page links and Share/Copy link: use the published `52at52.app` URLs.

## Features requiring separate service setup

Comments appear on the pages, but the package is NOT connected to a live comment
service. Until configured, the form explicitly checks drafts only: nothing is
posted or stored. The word filter is active in the draft checker. For moderation,
replies and owner deletion, follow `comments-api/README.md` and set the public
service details in `assets/config.js`. The moderation page is `admin/comments.html`.
Do not put private API tokens in frontend config.

Email signup/notifications are also not connected. The form displays an honest
setup message. Social URLs are blank rather than fake profile links; add your
actual profile URLs in `assets/config.js` if desired.

## Publishing future weeks

The setup needs no Python. Future weekly/review publishing still uses the included
local scripts, as originally requested. See `PUBLISHING.md`.
Do not run the old site's maintenance scripts against the new website folder.
