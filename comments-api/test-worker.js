import test from "node:test";
import assert from "node:assert/strict";
import {webcrypto} from "node:crypto";
import worker, {validateComment} from "./worker.js";
import {findBlockedTerm} from "./policy.js";
globalThis.crypto ||= webcrypto;

class Database {
  rows = [];
  prepare(sql) {
    const db=this;
    return {
      args:[], bind(...args){this.args=args;return this;},
      async all(){
        let rows=db.rows.filter(r=>sql.includes("WHERE page=") ? r.page===this.args[0]&&r.status==="published" : r.status!=="deleted");
        return {results:rows.map(({ip_hash,...row})=>row)};
      },
      async first(){
        if(sql.includes("COUNT")) return {total:db.rows.filter(r=>r.ip_hash===this.args[0]).length};
        return db.rows.find(r=>r.id===this.args[0]&&(!sql.includes("AND page=")||(r.page===this.args[1]&&r.status==="published")))||null;
      },
      async run(){
        if(sql.startsWith("INSERT")){
          const [id,page,parent_id,name,body,...rest]=this.args;
          const owner=sql.includes("'published',1");
          db.rows.push({id,page,parent_id,name,body,status:owner?"published":"pending",is_owner:owner?1:0,created_at:rest[0],ip_hash:rest[1]});
        }else if(sql.startsWith("UPDATE comments SET status=")){
          const row=db.rows.find(r=>r.id===this.args.at(-1));row.status=this.args[0];
          if(row.status==="deleted"){row.name="[deleted]";row.body="";row.ip_hash=null;}
        }
        return {success:true};
      }
    };
  }
}
const origin="https://52at52.app";
function env(){return {DB:new Database(),ALLOWED_ORIGINS:origin,ADMIN_TOKEN:"test-only-".repeat(5),TURNSTILE_SECRET:"test-only",TURNSTILE_HOSTNAME:"52at52.app"};}
function request(path, body, token) {
  return new Request("https://comments.test"+path,{method:body?"POST":"GET",
    headers:{Origin:origin,"CF-Connecting-IP":"192.0.2.1",...(token?{Authorization:"Bearer "+token}:{})},
    ...(body?{body:JSON.stringify(body)}:{})});
}
test("word policy: case, accents, spacing, substitutions, whole words",()=>{
  for(const value of ["SHIT","sh1t","s.h.i.t","s h i t","méRda"]) assert.ok(findBlockedTerm(value));
  for(const value of ["Great run!","Scunthorpe","I am gay and proud.","Sou brasileiro."]) assert.equal(findBlockedTerm(value),null);
  assert.equal(findBlockedTerm("customword",["customword"]),"customword");
});
test("validation rejects invalid payloads and traversal",()=>{
  for(const value of [null,[],{page:"/../",name:"A",body:"x"},{page:"/",name:"",body:"x"}]) assert.ok(validateComment(value).error);
});
test("server blocks bad words even when browser check is bypassed",async()=>{
  const e=env();
  const r=await worker.fetch(request("/comments",{page:"/",name:"Reader",body:"SHIT",token:"anything"}),e);
  assert.equal(r.status,400);assert.equal((await r.json()).code,"blocked_word");assert.equal(e.DB.rows.length,0);
});
test("origin and admin authentication fail closed",async()=>{
  const e=env();
  assert.equal((await worker.fetch(new Request("https://comments.test/comments",{headers:{Origin:"https://evil.test"}}),e)).status,403);
  assert.equal((await worker.fetch(request("/admin/comments"),e)).status,401);
  assert.equal((await worker.fetch(request("/admin/comments",null,"wrong"),e)).status,401);
});
test("unconfigured public posting does not accept comments",async()=>{
  const e=env();delete e.TURNSTILE_SECRET;
  const r=await worker.fetch(request("/comments",{page:"/",name:"Reader",body:"Great run!",token:"token"}),e);
  assert.equal(r.status,503);assert.equal(e.DB.rows.length,0);
});
test("wrong Turnstile hostname is rejected",async()=>{
  const e=env(), original=globalThis.fetch;
  globalThis.fetch=async()=>new Response(JSON.stringify({success:true,hostname:"evil.test",action:"comment"}));
  try {
    const r=await worker.fetch(request("/comments",{page:"/",name:"Reader",body:"Great run!",token:"test"}),e);
    assert.equal(r.status,400);assert.equal(e.DB.rows.length,0);
  } finally {globalThis.fetch=original;}
});
test("submit, hold for review, approve, reply and delete",async()=>{
  const e=env(), original=globalThis.fetch;
  globalThis.fetch=async()=>new Response(JSON.stringify({success:true,hostname:"52at52.app",action:"comment"}));
  try{
    const r=await worker.fetch(request("/comments",{page:"/weeks/week-01/",name:"Reader",body:"Great run!",token:"test-token"}),e);
    assert.equal(r.status,201);assert.equal(e.DB.rows[0].status,"pending");
    let publicList=await worker.fetch(request("/comments?page=/weeks/week-01/"),e);
    assert.equal((await publicList.json()).comments.length,0);
    const id=e.DB.rows[0].id;
    assert.equal((await worker.fetch(request("/admin/comments/"+id,{action:"approve"},e.ADMIN_TOKEN),e)).status,200);
    publicList=await worker.fetch(request("/comments?page=/weeks/week-01/"),e);
    assert.equal((await publicList.json()).comments.length,1);
    assert.equal((await worker.fetch(request("/admin/comments/"+id,{action:"reply",body:"Thank you!"},e.ADMIN_TOKEN),e)).status,200);
    assert.equal(e.DB.rows[1].is_owner,1);assert.equal(e.DB.rows[1].parent_id,id);
    const reply=await worker.fetch(request("/comments",{page:"/weeks/week-01/",name:"Another reader",body:"I agree!",parent_id:id,token:"test-token"}),e);
    assert.equal(reply.status,201);assert.equal(e.DB.rows[2].status,"pending");assert.equal(e.DB.rows[2].is_owner,0);
    assert.equal((await worker.fetch(request("/admin/comments/"+id,{action:"delete"},e.ADMIN_TOKEN),e)).status,200);
    assert.equal(e.DB.rows[0].body,"");assert.equal(e.DB.rows[0].status,"deleted");
  }finally{globalThis.fetch=original;}
});
