# 52 at 52: moderated comments

The frontend is included on every public new-site page and, as an additive
section, on the original archive's main page. Until the endpoint is configured,
visitors see a clearly labeled draft checker; nothing is stored or published.
Redirect stubs and the owner-only moderation utility do not have public threads.
The original archive is one legacy SPA, so its tabs share the `/archive/` thread.

## Behavior and limits

- Browser and server both check the submitted name and comment for the supplied
  English/Portuguese profanity/slur list. A blocked submission opens a popup
  identifying the term. The server rejects it even if browser JavaScript is bypassed.
- Matching normalizes case, accents, selected substitutions and punctuation between
  letters. It uses word boundaries to avoid common substring false positives.
- This is not AI moderation and does not detect all discriminatory speech, context,
  harassment, coded language or evasions. Legitimate quotations or reclaimed terms
  can be blocked. Edit the list to match your policy, and review every submission.
  Neutral identities and group names should not be blocked.
- All accepted visitor comments and replies are pending by default. Only approved
  comments appear publicly. Visitors can reply to published comments.
  The public widget loads the latest 300 published comments per page. The owner
  moderation screen provides pagination over pending and published comments.
- Owner approval, deletion and author replies require the server admin token.
  Deletion removes the displayed name/body and IP hash from the active record;
  database backups may still contain earlier copies. Replies are separate records.
- Public posts require a verified Turnstile result with the expected hostname/action.
  The Worker limits submissions to five per hour per hashed IP. This is basic
  anti-abuse protection, not a guarantee against a determined distributed attack.
- No visitor email field or login is required. Display names and comments are public
  after approval. A salted IP hash is used for rate limiting; old hashes are cleared
  on subsequent submissions after 24 hours. Cloudflare processes requests separately.

The giscus alternative remains available, but this custom popup/filter does not
apply inside giscus. Giscus documents GitHub-based storage/authentication and
moderation at https://giscus.app/.

## One-time deployment, performed by you

Use a Cloudflare account and install Node.js. Workers and D1 have free allowances,
not unlimited free capacity; verify the current limits and keep your account on
the intended plan: https://developers.cloudflare.com/workers/platform/pricing/.
This package does not sign you up, deploy resources, enable billing, or collect keys.

From the installed repository's `comments-api` folder (or the extracted package):

```powershell
npx wrangler login
npx wrangler d1 create 52at52-comments
```

Copy the returned database ID into `wrangler.toml`. Then apply the additive schema:

```powershell
npx wrangler d1 execute 52at52-comments --remote --file=schema.sql
```

Create a Turnstile widget for `52at52.app` in Cloudflare. Put its public site key
in the website's `assets/config.js`; keep its secret exclusively in the Worker:

```powershell
npx wrangler secret put TURNSTILE_SECRET
npx wrangler secret put ADMIN_TOKEN
```

Enter a long, randomly generated admin token (at least 32 characters) in the secure
Wrangler prompt. Generate it locally and keep it in your password manager. Never
put either secret in source files, Git, frontend config, URLs or chat.
The Worker deliberately refuses visitor posts without both secrets.
Check `ALLOWED_ORIGINS` and `TURNSTILE_HOSTNAME` in `wrangler.toml`, then:

```powershell
npx wrangler deploy
```

Set `comments.endpoint` in `assets/config.js` to the Worker HTTPS base URL
(without `/comments`), `comments.provider` to `"moderated"`, and
`comments.turnstileSiteKey` to the public key. Commit/push the website files normally.
For the uninstalled starter package, the config is under `site/assets/config.js`.

Turnstile server verification follows Cloudflare's Siteverify endpoint and requires
success, matching hostname and `comment` action. Tokens are single-use and expire:
https://developers.cloudflare.com/turnstile/get-started/server-side-validation/.
Production submissions must use your real widget, not test credentials.

## Owner moderation

Visit `https://52at52.app/admin/comments.html` and enter the admin token.
It is kept only in tab memory, not browser storage. Disconnect after use.
Approve pending comments, delete inappropriate ones, and reply as the author.
Deletion has an extra confirmation button. Load more comments to review older pages.
Never share the token. Rotate it with `wrangler secret put ADMIN_TOKEN` if exposed.

To extend the list, edit `site/assets/comment-policy.js` in the starter, or
`assets/comment-policy.js` after installation, and copy it to
`comments-api/policy.js`. Deploy the API and website together.
`EXTRA_BLOCKED_TERMS` can add comma-separated backend terms; put the same terms
in frontend `comments.additionalBlockedTerms` for immediate client feedback.
The backend remains authoritative if the browser list is out of date.

## Tests

```powershell
node --test test-worker.js
```

These use an in-memory database double and stubbed bot verification. They do not
prove your real Cloudflare deployment, keys, D1 binding, hostname configuration,
or real browser bot challenge works. Test those after configuring the service.
Do not deploy the test database or mock verification code.
