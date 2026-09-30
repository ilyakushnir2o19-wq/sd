const params = new URLSearchParams(location.search)
const tenant = params.get('tenant') || 'graphite'
const app = document.querySelector('#app')
let biz = null
let selected = null
let selectedDate = 0
let selectedSlot = null

const icons = {
  phone: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.68 2.8a2 2 0 0 1-.45 2.11L8.07 9.9a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.9.32 1.84.55 2.8.68A2 2 0 0 1 22 16.92Z"/></svg>',
  arrow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
  home: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m3 11 9-8 9 8v9a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1v-9Z"/></svg>',
  calendar: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M8 3v4M16 3v4M3 10h18"/></svg>',
  user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
  spark: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m12 2 1.55 5.45L19 9l-5.45 1.55L12 16l-1.55-5.45L5 9l5.45-1.55L12 2Z"/><path d="m19 15 .75 2.25L22 18l-2.25.75L19 21l-.75-2.25L16 18l2.25-.75L19 15Z"/></svg>',
  pin: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></svg>',
  shield: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/></svg>',
  camera: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M14.5 4 16 6h4a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l1.5-2h5Z"/><circle cx="12" cy="13" r="4"/></svg>',
  clock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m5 12 4 4L19 6"/></svg>',
  chevron: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m9 18 6-6-6-6"/></svg>'
}

function node(tag, cls, text) {
  const n = document.createElement(tag)
  if (cls) n.className = cls
  if (text !== undefined && text !== null) n.textContent = String(text)
  return n
}
function add(parent, ...children) { children.filter(Boolean).forEach(c => parent.append(c)); return parent }
function icon(name, cls) { const n = node('i', cls || ''); n.innerHTML = icons[name] || ''; return n }
function money(value) { return new Intl.NumberFormat('ru-RU').format(Number(value) || 0) + ' ₽' }
function bg(el, url) { if (url) el.style.backgroundImage = 'url("' + String(url).replace(/["\\]/g, '') + '")'; return el }
function call() { if (biz.phone) location.href = 'tel:' + biz.phone }
function route() { window.open('https://yandex.ru/maps/?text=' + encodeURIComponent(biz.address || biz.name), '_blank', 'noopener') }
function gallery() { return (biz.gallery || []).map((g, i) => typeof g === 'string' ? { src:g, title:'Работа ' + (i + 1), meta:biz.shortName || biz.name } : g).filter(g => g && g.src) }
function proofItems() {
  const fallback = [
    { icon:'shield', title:'Цена заранее', text:'Согласуем до начала работ' },
    { icon:'camera', title:'Фотоотчёт', text:'Фиксируем результат' },
    { icon:'clock', title:'По записи', text:'Без ожидания в очереди' }
  ]
  return [...(biz.proof || []), ...fallback].slice(0, 3)
}

async function boot() {
  try {
    const r = await fetch('./tenants/' + encodeURIComponent(tenant) + '.json', { cache:'no-store' })
    if (!r.ok) throw new Error('tenant not found')
    biz = await r.json()
    document.title = biz.name + ' — онлайн-запись'
    document.documentElement.style.setProperty('--accent', biz.accent || '#caff3e')
    document.documentElement.style.setProperty('--accent-2', biz.accentSecondary || biz.accent || '#8cff64')
    const theme = document.querySelector('meta[name="theme-color"]')
    if (theme) theme.setAttribute('content', biz.themeColor || '#08090b')
    render()
    bindParallax()
  } catch (_) {
    app.replaceChildren(node('div', '', 'Демо не найдено.'))
    app.firstChild.style.padding = '32px'
  }
}

function render() {
  const shots = gallery()
  const nearest = biz.nearestSlot || (biz.slots || [])[0] || '10:00'
  app.replaceChildren()

  const hero = node('section', 'hero')
  const heroMedia = bg(node('div', 'hero-media'), biz.hero)
  const top = node('div', 'hero-top')
  const brand = node('div', 'brand-lockup glass')
  const mark = node('div', 'logo-mark', biz.logoMark || String(biz.shortName || biz.name).slice(0, 2).toUpperCase())
  const brandText = add(node('div', 'brand-text'), node('strong', '', biz.shortName || biz.name), node('small', '', biz.brandLine || 'online booking'))
  add(brand, mark, brandText)
  const topCall = add(node('button', 'icon-btn glass'), icon('phone')); topCall.ariaLabel = 'Позвонить'; topCall.onclick = call
  add(top, brand, topCall)

  const status = add(node('div', 'hero-status glass'), node('i', 'status-dot'), document.createTextNode(biz.status || 'Открыто сегодня'))
  const copy = node('div', 'hero-copy')
  add(copy, node('div', 'eyebrow', biz.category || 'Автосервис'), node('h1', '', biz.headline || 'Запишитесь без звонка.'), node('div', 'hero-sub', biz.subheadline || biz.address || ''))
  const heroActions = node('div', 'hero-actions')
  const bookHero = add(node('button', 'hero-primary'), icon('calendar'), document.createTextNode('Записаться')); bookHero.onclick = () => openBooking(biz.services[0].id)
  const callHero = add(node('button', 'hero-secondary'), icon('phone')); callHero.ariaLabel = 'Позвонить'; callHero.onclick = call
  add(heroActions, bookHero, callHero); copy.append(heroActions)
  add(hero, heroMedia, top, status, copy)
  app.append(hero)

  const main = node('main', 'content')
  const fast = node('button', 'availability')
  const fastCopy = node('div')
  add(fastCopy, node('div', 'availability-kicker', 'Ближайшее свободное окно'), node('strong', '', (biz.nearestLabel || 'Сегодня') + ', ' + nearest), node('span', '', biz.nearestNote || 'Подтверждение записи за минуту'))
  add(fast, fastCopy, add(node('i', 'arrow-disc'), icon('arrow'))); fast.onclick = () => openBooking(biz.services[0].id, nearest)
  main.append(fast)

  main.append(sectionHead('Услуги', biz.services.length + ' доступно'))
  const services = node('div', 'service-list')
  biz.services.forEach(s => {
    const card = node('article', 'service')
    const copy = node('div', 'service-copy')
    const meta = node('div', 'service-meta')
    add(meta, node('span', '', s.duration), node('i', 'meta-dot'), node('span', '', s.note || 'по записи'))
    add(copy, node('div', 'service-title', s.name), meta)
    const side = node('div', 'service-side')
    add(side, node('div', 'service-price', (s.pricePrefix ? s.pricePrefix + ' ' : '') + money(s.price)), add(node('i', 'service-arrow'), icon('chevron')))
    add(card, copy, side); card.onclick = () => openBooking(s.id); services.append(card)
  })
  main.append(services)

  if (shots.length) {
    main.append(sectionHead('Работы', biz.galleryLabel || 'до / после'))
    const strip = node('div', 'gallery')
    shots.forEach((g, i) => {
      const shot = bg(node('button', 'work-shot'), g.src)
      const cap = node('span', 'work-caption')
      add(cap, node('strong', '', g.title || 'Работа'), node('span', '', g.meta || 'детейлинг'))
      shot.append(cap); shot.onclick = () => openWork(i); strip.append(shot)
    })
    main.append(strip)
  }

  main.append(sectionHead('Спокойно оставляйте авто', 'сервис'))
  const proofs = node('div', 'proof-grid')
  proofItems().forEach((p, i) => {
    const card = node('div', 'proof-card')
    add(card, add(node('i', 'proof-icon'), icon(p.icon || ['shield','camera','clock'][i])), node('strong', '', p.title), node('span', '', p.text)); proofs.append(card)
  })
  main.append(proofs)

  main.append(sectionHead('Где мы', biz.city || ''))
  const locationCard = node('button', 'location-card')
  const lc = node('span', 'location-copy'); add(lc, node('strong', '', biz.address || 'Адрес сервиса'), node('span', '', biz.routeNote || 'Построить маршрут'))
  add(locationCard, add(node('i', 'location-icon'), icon('pin')), lc, icon('chevron')); locationCard.onclick = route
  main.append(locationCard, node('div', 'preview-note', 'Персональная демо-версия · запись не отправляется в сервис, пока приложение не подключено.'))
  app.append(main)

  const ai = add(node('button', 'ai-bubble'), icon('spark')); ai.ariaLabel = 'Помощник'; ai.onclick = openAI; app.append(ai)
  const nav = node('nav', 'bottom-nav')
  nav.append(navButton('home', 'Главная', true, () => window.scrollTo({ top:0, behavior:'smooth' })), navButton('calendar', 'Запись', false, () => openBooking(biz.services[0].id)), navButton('user', 'Сервис', false, openProfile))
  app.append(nav)
}

function sectionHead(title, meta) { const h = node('div', 'section-head'); add(h, node('h2', '', title), node('span', '', meta)); return h }
function navButton(iconName, label, active, fn) { const b = node('button', 'nav-item' + (active ? ' active' : '')); add(b, add(node('i', 'nav-icon'), icon(iconName)), document.createTextNode(label)); b.onclick = fn; return b }
function bindParallax() {
  const hero = document.querySelector('.hero-media')
  if (!hero || matchMedia('(prefers-reduced-motion: reduce)').matches) return
  let ticking = false
  addEventListener('scroll', () => {
    if (ticking) return
    ticking = true
    requestAnimationFrame(() => { hero.style.transform = 'scale(1.035) translateY(' + Math.min(scrollY * .045, 12) + 'px)'; ticking = false })
  }, { passive:true })
}

function days() {
  const names = ['Вс','Пн','Вт','Ср','Чт','Пт','Сб']
  const months = ['янв','фев','мар','апр','май','июн','июл','авг','сен','окт','ноя','дек']
  const out = []
  for (let i = 0; i < 7; i++) { const d = new Date(); d.setDate(d.getDate() + i); out.push({ label:i === 0 ? 'Сегодня' : i === 1 ? 'Завтра' : names[d.getDay()], day:d.getDate(), month:months[d.getMonth()] }) }
  return out
}

function createSheet() {
  const wrap = node('div', 'sheet-backdrop')
  const sheet = node('section', 'sheet')
  sheet.append(node('div', 'handle')); wrap.append(sheet); document.body.append(wrap)
  wrap.onclick = e => { if (e.target === wrap) wrap.remove() }
  return { wrap, sheet }
}
function steps(active) { const s = node('div', 'steps'); for (let i = 1; i <= 3; i++) s.append(node('i', 'step' + (i <= active ? ' on' : ''))); return s }
function bookingSummary() {
  const box = node('div', 'booking-summary')
  const image = bg(node('div', 'booking-thumb'), selected.image || (gallery()[0] || {}).src || biz.hero)
  const copy = node('div'); add(copy, node('strong', '', selected.name), node('span', '', selected.duration + ' · ' + money(selected.price)))
  add(box, image, copy); return box
}

function openBooking(id, prefillSlot) {
  selected = biz.services.find(s => s.id === id) || biz.services[0]
  selectedDate = 0; selectedSlot = prefillSlot || null
  const { wrap, sheet } = createSheet()
  add(sheet, steps(1), node('div', 'sheet-kicker', 'Шаг 1 · время'), node('h3', '', 'Когда удобно?'), node('p', '', selected.description || 'Выберите свободное время. Детали подтвердит мастер.'), bookingSummary())
  const dates = node('div', 'date-strip')
  days().forEach((d, i) => {
    const b = node('button', 'date' + (i === 0 ? ' on' : '')); add(b, node('small', '', d.label), node('b', '', d.day), node('small', '', d.month))
    b.onclick = () => { selectedDate = i; dates.querySelectorAll('.date').forEach(x => x.classList.remove('on')); b.classList.add('on') }; dates.append(b)
  })
  sheet.append(dates)
  const slots = node('div', 'slots')
  ;(biz.slots || ['10:00','11:30','13:00','15:30','17:00','19:00']).forEach(t => {
    const busy = (biz.busySlots || []).includes(t)
    const b = node('button', 'slot' + (t === selectedSlot ? ' on' : '') + (busy ? ' busy' : ''), t)
    b.onclick = () => { if (busy) return; selectedSlot = t; slots.querySelectorAll('.slot').forEach(x => x.classList.remove('on')); b.classList.add('on'); next.disabled = false }; slots.append(b)
  })
  sheet.append(slots)
  const next = node('button', 'primary', 'Продолжить · ' + money(selected.price)); next.disabled = !selectedSlot; next.onclick = () => details(wrap, sheet); sheet.append(next)
}

function details(wrap, sheet) {
  const d = days()[selectedDate]
  sheet.replaceChildren(node('div', 'handle'), steps(2), node('div', 'sheet-kicker', 'Шаг 2 · контакты'), node('h3', '', 'Куда подтвердить запись?'), node('p', '', d.label + ', ' + d.day + ' ' + d.month + ' · ' + selectedSlot), bookingSummary())
  ;[['Имя','Как к вам обращаться','name'],['Телефон','+7 999 000-00-00','tel'],['Автомобиль','Например, BMW X5','text']].forEach(([label, placeholder, type]) => {
    const field = node('div', 'field'); const input = node('input'); input.placeholder = placeholder; input.type = type === 'tel' ? 'tel' : 'text'; add(field, node('label', '', label), input); sheet.append(field)
  })
  sheet.append(node('div', 'privacy-hint', 'Это демонстрация интерфейса. Введённые данные никуда не отправляются.'))
  const confirm = node('button', 'primary', 'Подтвердить · ' + money(selected.price)); confirm.onclick = () => success(sheet)
  const back = node('button', 'secondary', 'Назад'); back.onclick = () => { wrap.remove(); openBooking(selected.id, selectedSlot) }
  add(sheet, confirm, back)
}
function success(sheet) {
  const wrap = node('div', 'success-wrap'); add(wrap, add(node('div', 'success-mark'), icon('check')), node('div', 'sheet-kicker', 'Демо готово'), node('h3', '', 'Вот так клиент завершает запись.'), node('p', '', 'Сейчас заявка никуда не отправлена. После подключения она появится у сервиса, а клиент получит подтверждение.'))
  const close = node('button', 'primary', 'Вернуться в приложение'); close.onclick = () => sheet.parentElement.remove(); wrap.append(close); sheet.replaceChildren(node('div', 'handle'), wrap)
}
function openAI() {
  const { wrap, sheet } = createSheet()
  const head = node('div', 'chat-head'); const avatar = add(node('i', 'ai-avatar'), icon('spark')); const copy = node('div'); add(copy, node('strong', '', 'Помощник ' + (biz.shortName || biz.name)), node('span', '', 'демо · отвечает по услугам и записи')); add(head, avatar, copy); sheet.append(head)
  sheet.append(node('div', 'chat-line', 'Привет. Помогу понять, какая услуга нужна, и подобрать свободное время.'), node('div', 'chat-line me', biz.aiExample || 'Хочу записаться завтра после 18:00'), node('div', 'chat-line', biz.aiAnswer || ('Подойдёт «' + biz.services[0].name + '». Завтра есть окно в 19:00. Подготовить запись?')))
  const suggestions = node('div', 'chat-suggestions'); ['Сколько займёт?','Что входит?','Есть сегодня?'].forEach(x => suggestions.append(node('button', 'suggestion', x))); sheet.append(suggestions)
  const book = node('button', 'primary', 'Выбрать ближайшее время'); book.onclick = () => { wrap.remove(); openBooking(biz.services[0].id, biz.nearestSlot || null) }; sheet.append(book)
}
function openProfile() {
  const { sheet } = createSheet(); add(sheet, node('div', 'sheet-kicker', 'Сервис'), node('h3', '', biz.name), node('p', '', biz.about || 'Запись, услуги и связь с сервисом в одном приложении.'))
  const loc = node('div', 'location-card'); const lc = node('span', 'location-copy'); add(lc, node('strong', '', biz.address || ''), node('span', '', biz.hours || '')); add(loc, add(node('i', 'location-icon'), icon('pin')), lc, icon('chevron')); sheet.append(loc)
  const callBtn = add(node('button', 'primary'), icon('phone'), document.createTextNode(' Позвонить в сервис')); callBtn.onclick = call
  const routeBtn = node('button', 'secondary', 'Построить маршрут'); routeBtn.onclick = route; add(sheet, callBtn, routeBtn)
}
function openWork(index) {
  const shot = gallery()[index]; if (!shot) return
  const { wrap, sheet } = createSheet(); const visual = bg(node('div', 'work-shot'), shot.src); visual.style.height = '330px'
  const cap = node('span', 'work-caption'); add(cap, node('strong', '', shot.title || 'Работа'), node('span', '', shot.meta || '')); visual.append(cap); sheet.append(visual)
  const book = node('button', 'primary', 'Записаться на услугу'); book.onclick = () => { wrap.remove(); openBooking(biz.services[0].id) }; sheet.append(book)
}

boot()
