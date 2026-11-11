// Site configuration
window.SITE_CONFIG = {
  // Custom moderated comments. Blank endpoint = draft-check preview only.
  // Deploy comments-api/ and enter its HTTPS Worker URL plus public Turnstile key.
  comments: {
    provider: "moderated", // "giscus" remains an alternative, without this word filter.
    endpoint: "",
    turnstileSiteKey: "",
    additionalBlockedTerms: []
  },
  // Comments: giscus (free, GitHub Discussions). Get repoId/categoryId at https://giscus.app
  giscus: {
    repo: "ovalder/52-at-52",
    repoId: "",
    category: "Comments",
    categoryId: ""
  },
  // Email subscriptions through follow.it (reads https://52at52.app/rss.xml).
  // "https://api.follow.it/subscribe" works right away (follow.it recognizes the site).
  // After claiming the feed on follow.it you may paste your feed's own "action URL" here.
  subscribe: {
    provider: "followit",
    action: "https://api.follow.it/subscribe"
  },
  // Social profiles for the follow buttons on the home page
  social: {
    youtube: "",
    instagram: "",
    strava: ""
  }
};
