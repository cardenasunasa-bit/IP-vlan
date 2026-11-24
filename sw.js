/* PIPE NET: app shell offline, etapa 1. No almacena datos de Supabase en Cache Storage. */
const CACHE_NAME='pipe-net-shell-v15';
const SHELL=['./','./index.html','./manifest.json','./icons/icon-192.png','./icons/icon-512.png'];
const SUPABASE_LIB='https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2';
self.addEventListener('install',event=>{
 event.waitUntil((async()=>{
  const cache=await caches.open(CACHE_NAME);
  await cache.addAll(SHELL);
  try {const response=await fetch(SUPABASE_LIB);if(response.ok)await cache.put(SUPABASE_LIB,response)}catch(e){console.warn('Biblioteca externa no precargada',e)}
  await self.skipWaiting();
 })());
});
self.addEventListener('activate',event=>{
 event.waitUntil((async()=>{
  const keys=await caches.keys();
  await Promise.all(keys.filter(k=>k.startsWith('pipe-net-shell-')&&k!==CACHE_NAME).map(k=>caches.delete(k)));
  await self.clients.claim();
 })());
});
self.addEventListener('fetch',event=>{
 const req=event.request;
 if(req.method!=='GET')return;
 const url=new URL(req.url);
 const isLibrary=url.href.startsWith('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2');
 if(url.origin!==self.location.origin&&!isLibrary)return;
 if(isLibrary){event.respondWith((async()=>{
  const cache=await caches.open(CACHE_NAME);
  try{const response=await fetch(req);if(response.ok)await cache.put(SUPABASE_LIB,response.clone());return response}catch(e){return (await cache.match(SUPABASE_LIB))||Response.error()}
 })());return}
 if(req.mode==='navigate'){
  event.respondWith(fetch(req).catch(async()=> (await caches.match('./index.html'))||Response.error()));return;
 }
 event.respondWith((async()=>{
  const cached=await caches.match(req);
  if(cached)return cached;
  try{const response=await fetch(req);if(response.ok){const cache=await caches.open(CACHE_NAME);await cache.put(req,response.clone())}return response}catch(e){return Response.error()}
 })());
});
