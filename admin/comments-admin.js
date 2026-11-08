const endpoint = (window.SITE_CONFIG?.comments?.endpoint || "").replace(/\/$/,"");
let token = "", cursor = "", session = 0;
const status = document.querySelector(".admin-status"), queue = document.querySelector("#queue");
const more = document.querySelector("#more");
async function api(path, input) {
  const response = await fetch(endpoint + path, {method:input ? "POST" : "GET",
    headers:{"Authorization":"Bearer " + token, ...(input ? {"Content-Type":"application/json"} : {})},
    ...(input ? {body:JSON.stringify(input)} : {})});
  const data = await response.json();
  if (!response.ok) throw new Error(data.code || "Request failed");
  return data;
}
async function action(id, input) {
  try { await api("/admin/comments/" + id,input); await load(); status.textContent = "Saved."; }
  catch (error) { status.textContent = "Not saved: " + error.message; }
}
function card(comment) {
  const article = document.createElement("article"); article.className = "admin-card";
  const heading = document.createElement("h2"); heading.textContent = comment.name + " · " + comment.status;
  const page = document.createElement("a"); page.textContent = comment.page;
  page.href = "https://52at52.app" + comment.page; page.target="_blank"; page.rel="noopener";
  const text = document.createElement("p"); text.textContent = comment.body;
  const actions = document.createElement("div"); actions.className="admin-actions";
  if (comment.status === "pending") {
    const approve = document.createElement("button"); approve.textContent="Approve";
    approve.onclick = () => action(comment.id,{action:"approve"}); actions.append(approve);
  }
  const remove = document.createElement("button"); remove.textContent="Delete…";
  remove.onclick = () => {
    remove.hidden=true;
    const confirm = document.createElement("button"); confirm.textContent="Confirm deletion";
    const cancel = document.createElement("button"); cancel.textContent="Cancel";
    confirm.onclick=()=>action(comment.id,{action:"delete"});
    cancel.onclick=()=>{confirm.remove();cancel.remove();remove.hidden=false;};
    actions.append(confirm,cancel);
  };
  actions.append(remove);
  article.append(heading,page,text,actions);
  if (comment.status === "published") {
    const reply = document.createElement("textarea"); reply.maxLength=3000; reply.setAttribute("aria-label","Author reply");
    const send = document.createElement("button"); send.textContent="Publish author reply";
    send.onclick=()=>action(comment.id,{action:"reply",body:reply.value});
    article.append(reply,send);
  }
  return article;
}
async function load(append=false) {
  const activeSession = session;
  if (!append) { cursor=""; queue.replaceChildren(); }
  const data = await api("/admin/comments" + (cursor ? "?cursor="+encodeURIComponent(cursor) : ""));
  if (activeSession !== session || !token) return;
  for (const comment of data.comments || []) queue.append(card(comment));
  cursor=data.cursor || ""; more.hidden=!cursor;
  status.textContent=queue.children.length ? "Review comments below. Only approved comments are public." : "No comments to review.";
}
document.querySelector("#login").onsubmit=async event=>{
  event.preventDefault();
  if (!endpoint) {status.textContent="Configure the comment endpoint in assets/config.js first.";return;}
  session++; token=document.querySelector("#admin-token").value; document.querySelector("#admin-token").value="";
  try {await load();} catch {status.textContent="Could not connect. Check endpoint and token.";token="";}
};
document.querySelector("#logout").onclick=()=>{session++;token="";cursor="";queue.replaceChildren();more.hidden=true;document.querySelector("#admin-token").value="";status.textContent="Disconnected.";};
more.onclick=()=>load(true).catch(()=>{status.textContent="Could not load more comments.";});
