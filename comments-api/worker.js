import { findBlockedTerm } from "./policy.js";

const json = (value, status = 200) => new Response(JSON.stringify(value), {
  status, headers:{"Content-Type":"application/json; charset=utf-8", "Cache-Control":"no-store"}
});
async function digest(value) {
  const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return [...new Uint8Array(bytes)].map(b => b.toString(16).padStart(2,"0")).join("");
}
async function smallJson(request) {
  if ((Number(request.headers.get("content-length")) || 0) > 15000) {
    throw Object.assign(new Error("too_large"), {status:413});
  }
  const reader = request.body?.getReader();
  if (!reader) throw Object.assign(new Error("invalid_json"), {status:400});
  let size = 0, text = "";
  const decoder = new TextDecoder();
  for (;;) {
    const {done,value} = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > 15000) { await reader.cancel(); throw Object.assign(new Error("too_large"), {status:413}); }
    text += decoder.decode(value,{stream:true});
  }
  try { return JSON.parse(text + decoder.decode()); }
  catch { throw Object.assign(new Error("invalid_json"), {status:400}); }
}
async function admin(request, env) {
  if (!env.ADMIN_TOKEN || env.ADMIN_TOKEN.length < 32) return false;
  const header = request.headers.get("Authorization") || "";
  const expected = await digest("Bearer " + env.ADMIN_TOKEN);
  const actual = await digest(header);
  let mismatch = 0;
  for (let i = 0; i < expected.length; i++) mismatch |= expected.charCodeAt(i) ^ actual.charCodeAt(i);
  return mismatch === 0;
}
export function validateComment(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) return {error:"invalid_comment"};
  const page = typeof input.page === "string" ? input.page : "";
  const name = typeof input.name === "string" ? input.name.trim() : "";
  const body = typeof input.body === "string" ? input.body.trim() : "";
  if (!/^\/[a-zA-Z0-9/_\-.]*$/.test(page) || page.startsWith("//") || page.includes("..") || page.length > 250 ||
      !name || name.length > 80 || !body || body.length > 3000) return {error:"invalid_comment"};
  if (input.parent_id && !/^[a-f0-9-]{36}$/.test(input.parent_id)) return {error:"invalid_parent"};
  return {page, name, body, parent_id:input.parent_id || null};
}

async function handle(request, env) {
  const url = new URL(request.url);
  if (!env.DB) return json({code:"not_configured"}, 503);
  if (request.method === "GET" && url.pathname === "/comments") {
    const page = url.searchParams.get("page") || "/";
    if (!/^\/[a-zA-Z0-9/_\-.]*$/.test(page) || page.startsWith("//") || page.includes("..") || page.length > 250) return json({code:"invalid_page"},400);
    const result = await env.DB.prepare("SELECT * FROM (SELECT id,page,parent_id,name,body,is_owner,created_at FROM comments WHERE page=? AND status='published' ORDER BY created_at DESC LIMIT 300) ORDER BY created_at ASC").bind(page).all();
    return json({comments:result.results});
  }
  if (url.pathname.startsWith("/admin")) {
    if (!await admin(request, env)) return json({code:"unauthorized"},401);
    if (request.method === "GET" && url.pathname === "/admin/comments") {
      const cursor = url.searchParams.get("cursor") || "";
      let query = "SELECT id,page,parent_id,name,body,status,is_owner,created_at FROM comments WHERE status!='deleted'";
      let args = [];
      if (cursor) {
        const [date,id] = cursor.split("|");
        if (!/^\d{4}-\d\d-\d\dT[\d:.]+Z$/.test(date || "") || !/^[a-f0-9-]{36}$/.test(id || "")) return json({code:"invalid_cursor"},400);
        query += " AND (created_at<? OR (created_at=? AND id<?))"; args=[date,date,id];
      }
      const result = await env.DB.prepare(query + " ORDER BY created_at DESC,id DESC LIMIT 101").bind(...args).all();
      const rows = result.results.slice(0,100), last=rows.at(-1);
      return json({comments:rows,cursor:result.results.length>100 ? last.created_at+"|"+last.id : null});
    }
    if (request.method === "POST" && /^\/admin\/comments\/[a-f0-9-]{36}$/.test(url.pathname)) {
      const id = url.pathname.split("/").pop(), input = await smallJson(request);
      if (!input || typeof input !== "object") return json({code:"invalid_action"},400);
      if (!["approve","delete","reply"].includes(input.action)) return json({code:"invalid_action"},400);
      const existing = await env.DB.prepare("SELECT id,page,status FROM comments WHERE id=?").bind(id).first();
      if (!existing) return json({code:"not_found"},404);
      if (input.action === "reply") {
        const value = validateComment({page:existing.page, parent_id:id, name:"52 at 52", body:input.body});
        if (value.error) return json({code:value.error},400);
        const word = findBlockedTerm(value.body, (env.EXTRA_BLOCKED_TERMS || "").split(","));
        if (word) return json({code:"blocked_word",word},400);
        if (existing.status !== "published") return json({code:"approve_parent_first"},409);
        await env.DB.prepare("INSERT INTO comments(id,page,parent_id,name,body,status,is_owner,created_at) VALUES(?,?,?,?,?,'published',1,?)")
          .bind(crypto.randomUUID(), value.page, id, value.name, value.body, new Date().toISOString()).run();
      } else {
        await env.DB.prepare("UPDATE comments SET status=?,name=CASE WHEN ?='deleted' THEN '[deleted]' ELSE name END,body=CASE WHEN ?='deleted' THEN '' ELSE body END,ip_hash=CASE WHEN ?='deleted' THEN NULL ELSE ip_hash END WHERE id=?")
          .bind(input.action === "approve" ? "published" : "deleted", input.action === "delete" ? "deleted" : "published",
            input.action === "delete" ? "deleted" : "published", input.action === "delete" ? "deleted" : "published",id).run();
      }
      return json({ok:true});
    }
    return json({code:"not_found"},404);
  }
  if (request.method === "POST" && url.pathname === "/comments") {
    const input = await smallJson(request);
    if (!input || typeof input !== "object" || Array.isArray(input)) return json({code:"invalid_comment"},400);
    if (input.website) return json({code:"spam"},400);
    const value = validateComment(input);
    if (value.error) return json({code:value.error},400);
    const word = findBlockedTerm(value.name + "\n" + value.body, (env.EXTRA_BLOCKED_TERMS || "").split(","));
    if (word) return json({code:"blocked_word",word},400);
    // Public submissions fail closed until real bot-check and admin secrets exist.
    if (!env.TURNSTILE_SECRET || !env.TURNSTILE_HOSTNAME || !env.ADMIN_TOKEN || env.ADMIN_TOKEN.length < 32) return json({code:"not_configured"},503);
    if (!input.token || typeof input.token !== "string" || input.token.length > 2048) return json({code:"bot_check"},400);
    const result = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
      method:"POST", body:new URLSearchParams({secret:env.TURNSTILE_SECRET,response:input.token})
    });
    const verified = await result.json();
    if (!verified.success || verified.hostname !== env.TURNSTILE_HOSTNAME || verified.action !== "comment") return json({code:"bot_check"},400);
    const ip = request.headers.get("CF-Connecting-IP");
    if (!ip) return json({code:"missing_client_ip"},400);
    const ipHash = await digest(ip + "|" + env.ADMIN_TOKEN);
    const cutoff = new Date(Date.now() - 60*60*1000).toISOString();
    const recent = await env.DB.prepare("SELECT COUNT(*) AS total FROM comments WHERE ip_hash=? AND created_at>?").bind(ipHash,cutoff).first();
    if (recent.total >= 5) return json({code:"rate_limited"},429);
    if (value.parent_id) {
      const parent = await env.DB.prepare("SELECT id FROM comments WHERE id=? AND page=? AND status='published'").bind(value.parent_id,value.page).first();
      if (!parent) return json({code:"invalid_parent"},400);
    }
    // Retain the rate-limit identifier for at most a day.
    await env.DB.prepare("UPDATE comments SET ip_hash=NULL WHERE ip_hash IS NOT NULL AND created_at<?")
      .bind(new Date(Date.now()-86400000).toISOString()).run();
    const inserted = await env.DB.prepare("INSERT INTO comments(id,page,parent_id,name,body,status,created_at,ip_hash) SELECT ?,?,?,?,?,'pending',?,? WHERE (SELECT COUNT(*) FROM comments WHERE ip_hash=? AND created_at>?)<5")
      .bind(crypto.randomUUID(),value.page,value.parent_id,value.name,value.body,new Date().toISOString(),ipHash,ipHash,cutoff).run();
    if (inserted.meta?.changes === 0) return json({code:"rate_limited"},429);
    return json({ok:true,status:"pending"},201);
  }
  return json({code:"not_found"},404);
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const allowed = (env.ALLOWED_ORIGINS || "").split(",").map(s=>s.trim()).filter(Boolean);
    if (!allowed.includes(origin)) return json({code:"origin_not_allowed"},403);
    const headers = {"Access-Control-Allow-Origin":origin, "Vary":"Origin",
      "Access-Control-Allow-Methods":"GET, POST, OPTIONS", "Access-Control-Allow-Headers":"Content-Type, Authorization"};
    if (request.method === "OPTIONS") return new Response(null,{status:204,headers});
    let response;
    try { response = await handle(request,env); }
    catch (error) { response = json({code:error.status ? error.message : "service_error"}, error.status || 500); }
    for (const [key,value] of Object.entries(headers)) response.headers.set(key,value);
    response.headers.set("X-Content-Type-Options","nosniff");
    return response;
  }
};
