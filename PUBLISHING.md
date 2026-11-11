# Publishing future weeks and reviews

These scripts are for FUTURE content. They are not needed to unzip or install
the clean-start website. Run them from the root folder containing `index.html`,
`tools/`, and `content/`.

## Weekly posts (one folder per activity)

Install the publishing dependencies once:

```powershell
py -m pip install Pillow Markdown
```

Each activity has its own folder inside `content/activities/`, named
`Week X Activity N`:

```text
content/
  activities/
    _template/activity.md          <- copy this folder for every new activity
    Week 1 Activity 1/
      activity.md                  <- stats + EN/PT story
      IMG_0001.jpg, IMG_0002.jpg   <- photos (any names; or put them in photos/)
    Week 1 Activity 2/
      ...
  weeks/
    _template-week.md              <- OPTIONAL week title/intro (save as week-01.md)
```

To add an activity: copy `content/activities/_template`, rename the copy
(for example `Week 1 Activity 2`), fill in `activity.md`, and drop the photos in.
`photos: NA` uses every image in the folder, sorted by file name.

Publish (asks for the week number):

```powershell
py tools\publish_week.py
```

The script collects every `Week X Activity N` folder for that week, shows the
credited total, and after you type `PUBLISH` rebuilds the week page. You can run
it after the first activity, after each new one, or only once at the end of the
week: each run replaces the week page with the current state. When the week
reaches 52 credited km the page shows "Weekly challenge achieved!".

The week page has the week total and progress bar at the top, a list of the
week's activities, then one tile per activity with its photo slideshow, stats
and story. Comments at the bottom are for the whole week.
`https://52at52.app/activities/w01-a1/` links open the week page at that activity.

Activity IDs (`w01-a1`, ...) come from the folder name, so keep folder names
stable once shared. Week dates are automatic: Saturday to Friday, Week 1 is
November 7–13, 2026. Commit/push with your usual GitHub workflow afterwards; the
script never pushes. Backups of the JSON data go to `_private/backups/`.

The goal is 52 CREDITED km: running km + cycling km / 2. Use `type: run` or
`type: ride` and enter the ACTUAL distance, never a pre-divided bike distance.
`moving_time` is required; `pace` is optional (blank = calculated from moving time).

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
