# Publishing future weeks and reviews

These scripts are for FUTURE content. They are not needed to unzip or install
the clean-start website. Run them from the root folder containing `index.html`,
`tools/`, and `content/`.

## Weekly posts

Install the publishing dependencies once:

```powershell
py -m pip install Pillow Markdown
```

Edit `content/weeks/week-01/week.md`. The supplied activities are EXAMPLES;
replace them before publishing. Add/remove `## Activity` blocks as needed,
provide EN/PT stories, and put named photos beside the Markdown file or inside
that week's `photos/` folder. Provide YouTube links for videos.

Publish locally:

```powershell
py tools\publish_week.py 1
```

Review the printed totals, type `PUBLISH`, then review the generated pages.
Use your normal GitHub commit/upload process to publish the changes online.
The script does not push to GitHub. Optional email sending is skipped unless
you have explicitly configured private SMTP settings and a subscriber list.

For week 2, copy the source folder to `week-02`, update the front matter,
dates and stable activity IDs, then run `py tools\publish_week.py 2`.
Each week runs Saturday through Friday. Week 1 is November 7–13, 2026.

The goal is 52 CREDITED km: running km + cycling km / 2. Use `type: run` or
`type: ride`. Enter the ACTUAL distance, duration and elevation in the Markdown,
never pre-divide a bike distance. For example, 52 km of cycling earns 26 credited
km; 104 km of cycling or 26 km running + 52 km cycling meets the weekly goal.
JSON keeps `total_km` and `distance_km` as actual distance, and adds `credited_km`
for the score. Pace, speed, elevation and equipment mileage use actual activity data.

Keep published activity IDs stable so shared URLs keep working after title
changes. Week, activity and review pages have individual addresses and share
controls. Do not publish placeholder activities as real results.

The scripts recognize the clean-start root layout automatically. They update
root `data/`, `media/`, `weeks/`, `activities/` and related new-site pages.
They do not modify `archive/` or recalculate your old races.

## Reviews

Copy `content/reviews/template/` to a new product slug folder, edit the Markdown,
add photos, then run:

```powershell
py tools\publish_review.py product-slug
```

## Tips and comparisons

The existing Tips pages and nutrition/shoe comparison tables are already built.
After editing the relevant guide fragments or comparison JSON, regenerate the
new site's pages:

```powershell
py tools\build_pages.py
```

The comparison rows are editable starter content, not automatically collected
reviews. Keep claims accurate when replacing them with your own notes.

## Summary stories

The first bilingual story lives in `content/summaries/season-two/en.md` and
`pt.md`. Edit it and run `py tools\build_pages.py` to regenerate the pages.
To add a later summary, make a new stable-slug folder with `en.md` and `pt.md`,
then add its slug, date, English/Portuguese titles and descriptions to
`data/summaries.json`, following the first entry. The Summary index sorts newest first.
Keep the slug unchanged once you have shared the page URL. Summary pages include
sharing, comments and browser-detected language just like weekly pages.

## Logo

Your uploaded JPG is already included as `assets/52at52.jpg`; the prepared header
asset is `assets/brand-shield.png`. No logo script is needed initially.
The home-screen icons have already been generated from your uploaded image.
If you later replace `brand-shield.png`, the optional icon rebuild command is:

```powershell
py tools\build_brand_icons.py
```

Do not change the original logo under `archive/original/media/`.

## Service setup

Comments and email subscriptions are not activated by publishing a week.
Set up the chosen service separately and enter its public settings in
`assets/config.js`. The optional comments backend instructions are in
`comments-api/README.md`.

Keep credentials and subscriber lists outside the public repository/upload.
Do not include `_private/`, `.env`, `.dev.vars` or similar private files.
