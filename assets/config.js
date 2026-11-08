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
  // Optional public signup integration. Check the provider's current terms first.
  // Never expose a private API key in this frontend.
  subscribe: {
    endpoint: "", // Public signup endpoint compatible with the form; not a secret API endpoint.
    setupNoteEn: "Email subscriptions will be enabled once a subscription service is connected (see README).",
    setupNotePt: "As inscrições por e-mail serão ativadas assim que um serviço de inscrições for conectado (veja o README)."
  },
  // Social profiles for the follow buttons on the home page
  social: {
    youtube: "",
    instagram: "",
    strava: ""
  }
};
