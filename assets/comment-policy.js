// Shared by the browser and comment API. Edit terms, then deploy both copies.
// Never block neutral identity/group names. This is a word filter, not a judgement
// of intent or a comprehensive discrimination detector; human review is required.
export const blockedTerms = [
  "fuck", "shit", "bitch", "cunt", "motherfucker",
  "caralho", "porra", "merda", "puta", "foda", "fodase",
  "nigger", "nigga", "faggot", "kike",
  "viado", "bicha"
];

function normalize(value) {
  return String(value).normalize("NFKD").replace(/\p{M}/gu, "")
    .toLowerCase().replace(/[\u200B-\u200D\uFEFF]/g, "")
    .replace(/[013457@$]/g, c => ({"0":"o","1":"i","3":"e","4":"a","5":"s","7":"t","@":"a","$":"s"})[c]);
}

export function findBlockedTerm(value, additional = []) {
  const text = normalize(value);
  for (const term of [...blockedTerms, ...additional]) {
    const clean = normalize(term).replace(/[^a-z]/g, "");
    if (!clean) continue;
    const letters = [...clean].join("[\\W_]*");
    const match = text.match(new RegExp("(^|[^a-z0-9])(" + letters + ")(?=$|[^a-z0-9])", "i"));
    if (match) return term;
  }
  return null;
}
