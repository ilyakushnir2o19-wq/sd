const params=new URLSearchParams(location.search)
const tenant=params.get("tenant")||"graphite"
const app=document.querySelector("#app")
let biz=null,selected=null,selectedDate=0,selectedSlot=null
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))
const money=n=>new Intl.NumberFormat("ru-RU").format(n)+" ₽"
const icon={home:"⌂",book:"◫",profile:"○"}
async function boot(){
  try{
    const r=await fetch("./tenants/"+encodeURIComponent(tenant)+".json",{cache:"no-store"})
    if(!r.ok) throw new Error("tenant not found")
    biz=await r.json()
    document.title=biz.name+" — запись"
    document.documentElement.style.setProperty("--accent",biz.accent||"#c6ff38")
    render()
  }catch(e){app.innerHTML='<div style="padding:32px">Демо не найдено.</div>'}
}
function render(){
  app.innerHTML=`
    <section class="hero">
      <div class="hero-media" style="background-image:url('${esc(biz.hero)}')"></div>
      <div class="hero-top">
        <div class="brand-pill"><i class="brand-dot"></i>${esc(biz.shortName||biz.name)}</div>
        <button class="icon-btn" data-call aria-label="Позвонить">↗</button>
      </div>
      <div class="hero-copy">
        <div class="eyebrow">${esc(biz.category||"Сервис")}</div>
        <h1>${esc(biz.headline||"Запишитесь за минуту")}</h1>
        <div class="hero-sub">${esc(biz.subheadline||biz.address||"")}</div>
      </div>
    </section>
    <main class="content">
      <div class="quick-row">
        <div class="quick"><strong>Сегодня открыто</strong><span>${esc(biz.hours||"09:00–21:00")}</span></div>
        <div class="quick"><strong>${esc(biz.rating||"4.9")} ★</strong><span>${esc(biz.reviewsLabel||"по отзывам клиентов")}</span></div>
      </div>
      <div class="section-head"><h2>Выберите услугу</h2><span>${biz.services.length} услуг</span></div>
      <div class="service-list">
        ${biz.services.map(s=>`<article class="service" data-service="${esc(s.id)}">
          <div><div class="service-title">${esc(s.name)}</div><div class="service-meta"><span>${esc(s.duration)}</span><span>·</span><span>${esc(s.note||"")}</span></div></div>
          <div class="service-price">${money(s.price)}</div>
        </article>`).join("")}
      </div>
      <div class="section-head"><h2>Почему к нам</h2></div>
      <div class="quick-row">
        <div class="quick"><strong>${esc(biz.proof?.[0]?.title||"Гарантия")}</strong><span>${esc(biz.proof?.[0]?.text||"Фиксируем результат")}</span></div>
        <div class="quick"><strong>${esc(biz.proof?.[1]?.title||"Без звонков")}</strong><span>${esc(biz.proof?.[1]?.text||"Запись онлайн 24/7")}</span></div>
      </div>
    </main>
    <button class="ai-bubble" data-ai aria-label="AI помощник">✦</button>
    <nav class="bottom-nav">
      <button class="nav-item active"><b>${icon.home}</b>Главная</button>
      <button class="nav-item" data-book><b>${icon.book}</b>Запись</button>
      <button class="nav-item"><b>${icon.profile}</b>Профиль</button>
    </nav>`
  document.querySelectorAll("[data-service]").forEach(el=>el.onclick=()=>openBooking(el.dataset.service))
  document.querySelector("[data-book]").onclick=()=>openBooking(biz.services[0].id)
  document.querySelector("[data-call]").onclick=()=>location.href="tel:"+biz.phone
  document.querySelector("[data-ai]").onclick=openAI
}
function days(){
  const names=["Вс","Пн","Вт","Ср","Чт","Пт","Сб"],out=[]
  for(let i=0;i<6;i++){const d=new Date();d.setDate(d.getDate()+i);out.push({label:i===0?"Сегодня":names[d.getDay()],day:d.getDate()})}
  return out
}
function openBooking(id){
  selected=biz.services.find(s=>s.id===id)||biz.services[0];selectedDate=0;selectedSlot=null
  const wrap=document.createElement("div");wrap.className="sheet-backdrop";wrap.innerHTML=`
    <section class="sheet">
      <div class="handle"></div><div class="steps"><i class="step on"></i><i class="step"></i><i class="step"></i></div>
      <h3>${esc(selected.name)}</h3><p>${esc(selected.description||"Выберите удобное время. Подтверждение придёт сразу после записи.")}</p>
      <div class="date-strip">${days().map((d,i)=>`<button class="date ${i===0?"on":""}" data-date="${i}"><small>${d.label}</small><b>${d.day}</b></button>`).join("")}</div>
      <div class="slots">${(biz.slots||["10:00","11:30","13:00","15:30","17:00","19:00"]).map(t=>`<button class="slot" data-slot="${t}">${t}</button>`).join("")}</div>
      <button class="primary" data-next disabled>Продолжить · ${money(selected.price)}</button>
    </section>`
  document.body.append(wrap);wrap.onclick=e=>{if(e.target===wrap)wrap.remove()}
  wrap.querySelectorAll("[data-date]").forEach(b=>b.onclick=()=>{selectedDate=+b.dataset.date;wrap.querySelectorAll(".date").forEach(x=>x.classList.remove("on"));b.classList.add("on")})
  wrap.querySelectorAll("[data-slot]").forEach(b=>b.onclick=()=>{selectedSlot=b.dataset.slot;wrap.querySelectorAll(".slot").forEach(x=>x.classList.remove("on"));b.classList.add("on");wrap.querySelector("[data-next]").disabled=false})
  wrap.querySelector("[data-next]").onclick=()=>details(wrap)
}
function details(wrap){
  const d=days()[selectedDate]
  wrap.querySelector(".sheet").innerHTML=`
    <div class="handle"></div><div class="steps"><i class="step on"></i><i class="step on"></i><i class="step"></i></div>
    <h3>Почти готово</h3><p>${esc(selected.name)} · ${esc(d.label)} ${d.day}, ${esc(selectedSlot)}</p>
    <div class="field"><label>Имя</label><input id="book-name" autocomplete="name" placeholder="Как к вам обращаться"></div>
    <div class="field"><label>Телефон</label><input id="book-phone" autocomplete="tel" inputmode="tel" placeholder="+7 999 000-00-00"></div>
    <button class="primary" data-confirm>Записаться · ${money(selected.price)}</button>
    <button class="secondary" data-back>Назад</button>`
  wrap.querySelector("[data-back]").onclick=()=>{wrap.remove();openBooking(selected.id)}
  wrap.querySelector("[data-confirm]").onclick=()=>success(wrap)
}
function success(wrap){
  wrap.querySelector(".sheet").innerHTML=`
    <div class="handle"></div><div class="success-mark">✓</div>
    <h3>Запись создана</h3><p>Мы забронировали время. В live-версии клиент получит push/Telegram/SMS, а запись появится у владельца.</p>
    <button class="primary" data-close>Готово</button>`
  wrap.querySelector("[data-close]").onclick=()=>wrap.remove()
}
function openAI(){
  const wrap=document.createElement("div");wrap.className="sheet-backdrop";wrap.innerHTML=`
    <section class="sheet"><div class="handle"></div><h3>Помощник ${esc(biz.shortName||biz.name)}</h3>
    <p>Демо AI-консультанта. В live-версии он видит услуги и свободные слоты, но не имеет доступа к чужим данным.</p>
    <div class="chat-line">Привет! Помогу подобрать услугу и время. Что хотите сделать?</div>
    <div class="chat-line me">${esc(biz.aiExample||"Хочу записаться завтра после 18:00")}</div>
    <div class="chat-line">Есть окно в 19:00. Могу подготовить запись на «${esc(biz.services[0].name)}».</div>
    <button class="primary" data-ai-book>Выбрать 19:00</button></section>`
  document.body.append(wrap);wrap.onclick=e=>{if(e.target===wrap)wrap.remove()}
  wrap.querySelector("[data-ai-book]").onclick=()=>{wrap.remove();openBooking(biz.services[0].id)}
}
boot()
