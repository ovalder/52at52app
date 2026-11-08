import { findBlockedTerm } from "./comment-policy.js";

const config = window.SITE_CONFIG?.comments || {};
const currentScript = new URL(import.meta.url);
const siteRoot = new URL("../", currentScript);
const endpoint = (config.endpoint || "").replace(/\/$/, "");
let language = document.documentElement.lang?.startsWith("pt") ||
  (!document.documentElement.lang && navigator.language.startsWith("pt")) ? "pt" : "en";
const t = (en, pt) => language === "pt" ? pt : en;
const canonical = document.querySelector('link[rel="canonical"]')?.href;
let page = document.querySelector("[data-comment-page]")?.dataset.commentPage ||
  (canonical ? new URL(canonical).pathname : "/" + location.pathname.replace(siteRoot.pathname, ""));
page = page.replace(/index\.html$/, "");
if (!page.startsWith("/")) page = "/" + page;
let slot = document.getElementById("giscus-slot");
let added = false;
if (!slot && document.querySelector("main")) {
  const section = document.createElement("section");
  section.className = "comments";
  section.innerHTML = `<h2 class="txt" data-en="Comments" data-pt="Comentários">${t("Comments","Comentários")}</h2>
<p class="disclaimer txt" data-en="Comments reflect their authors' opinions. I am not responsible for other people's comments and may delete any comment I consider inappropriate at my sole discretion." data-pt="Os comentários refletem a opinião de seus autores. Não me responsabilizo pelos comentários de outras pessoas e posso apagar qualquer comentário que considere inadequado, a meu exclusivo critério.">${t(
  "Comments reflect their authors' opinions. I am not responsible for other people's comments and may delete any comment I consider inappropriate at my sole discretion.",
  "Os comentários refletem a opinião de seus autores. Não me responsabilizo pelos comentários de outras pessoas e posso apagar qualquer comentário que considere inadequado, a meu exclusivo critério.")}</p>
<div id="giscus-slot"></div>`;
  document.querySelector("main").append(section);
  slot = section.querySelector("#giscus-slot"); added = true;
}
if (slot && config.provider !== "giscus") init(slot);
else if (added) window.loadComments?.(language);

function init(slot) {
  const css = document.createElement("link");
  css.rel = "stylesheet"; css.href = new URL("assets/comments.css", siteRoot).href;
  document.head.append(css);
  const root = document.createElement("div");
  root.className = "comment-thread";
  const notice = document.createElement("p"); notice.className = "comment-notice";
  const list = document.createElement("div"); list.setAttribute("aria-live", "polite");
  const form = document.createElement("form");
  form.innerHTML = `<p class="comment-replying"></p>
<label data-label="name" for="comment-name"></label><input id="comment-name" name="name" maxlength="80" required autocomplete="nickname">
<label data-label="body" for="comment-body"></label><textarea id="comment-body" name="body" maxlength="3000" required></textarea>
<div class="comment-trap" aria-hidden="true"><label for="comment-website">Leave empty</label><input id="comment-website" name="website" tabindex="-1" autocomplete="off"></div>
<div class="comment-bot"></div><p><button type="submit"></button></p>
<p class="comment-status" role="status"></p>`;
  const dialog = document.createElement("dialog");
  dialog.className = "comment-dialog";
  dialog.innerHTML = '<h2></h2><p></p><button type="button"></button>';
  dialog.querySelector("button").onclick = () => dialog.close();
  root.append(notice, list, form, dialog);
  slot.replaceChildren(root);
  let parentId = null, botToken = "", widgetId = null, comments = [];
  const status = form.querySelector(".comment-status");
  function labels() {
    notice.textContent = endpoint
      ? t("Please be respectful. Comments and replies are reviewed before appearing. No email address is collected.",
          "Seja respeitoso. Comentários e respostas são revisados antes da publicação. Não coletamos e-mail.")
      : t("Comments are not connected yet. You can check a draft below, but it will not be published.",
          "Os comentários ainda não estão conectados. Você pode verificar um rascunho abaixo, mas ele não será publicado.");
    form.querySelector('[data-label="name"]').textContent = t("Your display name", "Seu nome público");
    form.querySelector('[data-label="body"]').textContent = t("Your comment", "Seu comentário");
    form.querySelector('[type="submit"]').textContent = endpoint ? t("Submit for review", "Enviar para revisão") : t("Check draft", "Verificar rascunho");
    dialog.querySelector("h2").textContent = t("Please keep it respectful", "Por favor, mantenha o respeito");
    dialog.querySelector("button").textContent = t("Edit my comment", "Editar meu comentário");
  }
  function blocked(word) {
    dialog.querySelector("p").textContent = t(
      `Please avoid the word “${word}”. Edit your name or comment before trying again.`,
      `Evite a palavra “${word}”. Edite seu nome ou comentário antes de tentar novamente.`);
    dialog.showModal();
    dialog.addEventListener("close", () => form.elements.body.focus(), {once:true});
  }
  function renderList() {
    list.replaceChildren();
    const byId = new Map(comments.map(c => [c.id, c]));
    const children = new Map();
    for (const c of comments) {
      const parent = byId.has(c.parent_id) ? c.parent_id : null;
      if (!children.has(parent)) children.set(parent, []);
      children.get(parent).push(c);
    }
    const seen = new Set();
    function draw(parent, container, depth = 0) {
      for (const c of children.get(parent) || []) {
        if (seen.has(c.id)) continue;
        seen.add(c.id);
        const card = document.createElement("article"); card.className = "comment-card";
        const author = document.createElement("strong");
        author.textContent = c.name + (c.is_owner ? t(" · Author", " · Autor") : "");
        const time = document.createElement("time");
        time.dateTime = c.created_at; time.textContent = new Date(c.created_at).toLocaleDateString(language);
        const body = document.createElement("p"); body.textContent = c.body;
        const reply = document.createElement("button"); reply.type = "button"; reply.className = "comment-reply";
        reply.textContent = t("Reply", "Responder");
        reply.onclick = () => {
          parentId = c.id;
          const line = form.querySelector(".comment-replying");
          line.textContent = t(`Replying to ${c.name}. `, `Respondendo a ${c.name}. `);
          const cancel = document.createElement("button"); cancel.type = "button"; cancel.className = "comment-reply";
          cancel.textContent = t("Cancel", "Cancelar");
          cancel.onclick = () => { parentId = null; line.replaceChildren(); };
          line.append(cancel); form.elements.body.focus();
        };
        const replies = document.createElement("div"); replies.className = depth < 3 ? "comment-children" : "";
        card.append(author, time, body, reply, replies); container.append(card); draw(c.id, replies, depth + 1);
      }
    }
    draw(null, list);
    if (!comments.length && endpoint) list.textContent = t("No published comments yet.", "Ainda não há comentários publicados.");
  }
  async function load() {
    if (!endpoint) return;
    try {
      const response = await fetch(endpoint + "/comments?page=" + encodeURIComponent(page));
      if (!response.ok) throw new Error("load");
      const data = await response.json(); comments = data.comments || []; renderList();
    } catch { list.textContent = t("Comments are temporarily unavailable. Please try later.", "Comentários indisponíveis no momento. Tente mais tarde."); }
  }
  form.onsubmit = async event => {
    event.preventDefault();
    const name = form.elements.name.value.trim(), body = form.elements.body.value.trim();
    const word = findBlockedTerm(name + "\n" + body, config.additionalBlockedTerms || []);
    if (word) { blocked(word); return; }
    if (!endpoint) { status.textContent = t("No blocked words found. This draft was not posted: the comment service is not connected yet.",
      "Nenhuma palavra bloqueada encontrada. Este rascunho não foi publicado: o serviço ainda não está conectado."); return; }
    if (!botToken) { status.textContent = t("Complete the anti-spam check first.", "Conclua a verificação antispam primeiro."); return; }
    const submit = form.querySelector('[type="submit"]'); submit.disabled = true;
    try {
      const response = await fetch(endpoint + "/comments", {method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({page, name, body, parent_id:parentId, token:botToken, website:form.elements.website.value})});
      const data = await response.json();
      if (data.code === "blocked_word") { blocked(data.word); return; }
      if (!response.ok) throw new Error(data.code || "post");
      status.textContent = t("Thank you. Your comment is awaiting approval.", "Obrigado. Seu comentário aguarda aprovação.");
      form.elements.body.value = ""; parentId = null; form.querySelector(".comment-replying").replaceChildren();
    } catch {
      status.textContent = t("Your comment was not posted. Please try again later.", "Seu comentário não foi publicado. Tente novamente mais tarde.");
    } finally {
      submit.disabled = false; botToken = "";
      if (widgetId !== null && window.turnstile) window.turnstile.reset(widgetId);
    }
  };
  if (endpoint && config.turnstileSiteKey) {
    const start = () => {
      if (!window.turnstile) return;
      widgetId = window.turnstile.render(form.querySelector(".comment-bot"), {
        sitekey:config.turnstileSiteKey, action:"comment",
        callback:token => { botToken = token; },
        "expired-callback":() => { botToken = ""; }
      });
    };
    if (window.turnstile) start();
    else {
      const script = document.createElement("script");
      script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
      script.async = true; script.onload = start; document.head.append(script);
    }
  }
  document.addEventListener("site:language", event => { language = event.detail; labels(); renderList(); });
  labels(); load();
}
