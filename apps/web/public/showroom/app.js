const params = new URLSearchParams(location.search)
const tenant = params.get('tenant') || 'graphite'
const app = document.querySelector('#app')

let biz = null
let selected = null
let selectedDate = 0
let selectedSlot = null

const icons = {
  phone: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.68 2.8a2 2 0 0 1-.45 2.11L8.07 9.9a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.9.32 1.84.55 2.8.68A2 2 0 0 1 22 16.92Z"/></svg>',
  home: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m3 11 9-8 9 8v9a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1v-9Z"/></svg>',
  calendar: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M8 3v4M16 3v4M3 10h18"/></svg>',
  user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
  tools: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M14.5 6.5a4 4 0 0 0-5-5L12 4l-3 3-2.5-2.5a4 4 0 0 0 5 5L19 17a2 2 0 1 1-2 2l-7.5-7.5"/></svg>',
  garage: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M3 10 12 4l9 6v10H3V10Z"/><path d="M7 20v-6h10v6M9 10h6"/></svg>',
  tag: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m20 13-7 7-9-9V4h7l9 9Z"/><circle cx="8.5" cy="8.5" r="1.5"/></svg>',
  grid: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
  spark: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m12 2 1.5 5.5L19 9l-5.5 1.5L12 16l-1.5-5.5L5 9l5.5-1.5L12 2Z"/><path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m5 12 4 4L19 6"/></svg>',
  pin: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></svg>',
  clock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>'
}

function node(tag, cls, text) {
  const el = document.createElement(tag)
  if (cls) el.className = cls
  if (text !== undefined && text !== null) el.textContent = String(text)
  return el
}

function add(parent, ...children) {
  children.filter(Boolean).forEach(child => parent.append(child))
  return parent
}

function icon(name, cls) {
  const el = node('i', cls || '')
  el.innerHTML = icons[name] || ''
  return el
}

function money(value) {
  return new Intl.NumberFormat('ru-RU').format(Number(value) || 0) + ' ₽'
}

function bg(el, url) {
  const safe = String(url || '').replace(/["\\]/g, '')
  const fallback = './assets/automotive-fallback.svg'
  el.style.backgroundImage = safe
    ? 'url("' + safe + '"), url("' + fallback + '")'
    : 'url("' + fallback + '")'
  return el
}

function call() {
  if (biz.phone) location.href = 'tel:' + biz.phone
}

function route() {
  window.open(
    'https://yandex.ru/maps/?text=' + encodeURIComponent(biz.address || biz.name),
    '_blank',
    'noopener'
  )
}

function gallery() {
  return (biz.gallery || [])
    .map((item, i) => typeof item === 'string'
      ? { src:item, title:'Работа ' + (i + 1), meta:biz.shortName || biz.name }
      : item)
    .filter(item => item && item.src)
}

async function boot() {
  try {
    const response = await fetch('./tenants/' + encodeURIComponent(tenant) + '.json', { cache:'no-store' })
    if (!response.ok) throw new Error('tenant not found')
    biz = await response.json()
    document.title = biz.name + ' — онлайн-запись'
    document.documentElement.style.setProperty('--accent', biz.accent || '#c9ff3d')

    const theme = document.querySelector('meta[name="theme-color"]')
    if (theme) theme.setAttribute('content', '#121311')

    render()
  } catch (_) {
    app.replaceChildren(node('div', '', 'Демо не найдено.'))
    app.firstChild.style.padding = '32px'
  }
}

function render() {
  app.replaceChildren()

  const appbar = node('header', 'appbar')
  const lockup = node('div', 'brand-lockup')
  add(lockup, node('div', 'brand-glyph'), node('div', 'brand-name', biz.shortName || biz.name))
  const profile = add(node('button', 'profile-btn'), icon('user'))
  profile.ariaLabel = 'Профиль'
  profile.onclick = openProfile
  add(appbar, lockup, profile)
  app.append(appbar)

  const screen = node('main', 'screen')

  const hero = node('section', 'hero-card')
  const photo = bg(node('div', 'hero-photo'), biz.hero)
  const cta = node('div', 'hero-cta')
  const bookHero = node('button', '', 'Записаться')
  bookHero.onclick = () => openBooking(biz.services[0].id)
  add(cta, bookHero, node('span', 'hero-arrow', '→'))
  add(hero, photo, cta)
  screen.append(hero)

  const intro = node('section', 'business-copy')
  add(
    intro,
    node('h1', '', biz.name),
    node('p', '', biz.appDescription || biz.subheadline || biz.about || '')
  )
  screen.append(intro)

  const stats = node('div', 'stat-grid')
  const serviceStat = node('div', 'stat-card')
  const serviceHead = node('div', 'stat-head')
  add(serviceHead, icon('tools'), document.createTextNode(String(biz.services.length)))
  add(serviceStat, serviceHead, node('small', '', 'услуг в прайсе'))

  const bayStat = node('div', 'stat-card')
  const bayHead = node('div', 'stat-head')
  add(bayHead, icon('garage'), document.createTextNode(String(biz.baysInWork || 3)))
  add(bayStat, bayHead, node('small', '', 'бокса в работе'))
  add(stats, serviceStat, bayStat)
  screen.append(stats)

  const minPrice = biz.priceFrom || Math.min(...biz.services.map(s => Number(s.price) || 0).filter(Boolean))
  const price = node('div', 'price-card')
  const priceMain = node('strong')
  add(priceMain, icon('tag'), document.createTextNode('от ' + money(minPrice)))
  add(price, priceMain, node('span', '', 'за услугу'))
  screen.append(price)

  const booking = node('section', 'booking-section')
  booking.append(node('h2', '', 'Запись в студию'))
  const bookingCard = node('div', 'booking-card')
  add(
    bookingCard,
    node('h3', '', biz.bookingTitle || 'Свежий вид для вашего авто'),
    node('p', '', biz.bookingCopy || 'Выберите услугу и удобное время. Остальное возьмём на себя.')
  )
  const now = node('button', 'book-now', 'Записаться')
  now.onclick = () => openBooking(biz.services[0].id, biz.nearestSlot || null)
  const ai = add(node('button', 'ai-dot'), icon('spark'))
  ai.ariaLabel = 'Запись с помощником'
  ai.onclick = openAssistant
  add(bookingCard, now, ai)
  booking.append(bookingCard)
  screen.append(booking)

  const serviceSection = node('section', 'secondary-section')
  serviceSection.id = 'services'
  serviceSection.append(node('h2', '', 'Услуги'))
  const serviceList = node('div', 'service-list')
  biz.services.forEach(service => {
    const row = node('button', 'service-row')
    const copy = node('div')
    add(copy, node('div', 'service-title', service.name), node('div', 'service-meta', service.duration + (service.note ? ' · ' + service.note : '')))
    add(row, copy, node('div', 'service-price', money(service.price)))
    row.onclick = () => openBooking(service.id)
    serviceList.append(row)
  })
  serviceSection.append(serviceList)
  screen.append(serviceSection)

  const shots = gallery()
  if (shots.length) {
    const workSection = node('section', 'secondary-section')
    workSection.append(node('h2', '', 'Работы'))
    const strip = node('div', 'work-strip')
    shots.forEach((shot, index) => {
      const visual = bg(node('button', 'work-shot'), shot.src)
      const cap = node('span', 'work-caption')
      add(cap, node('strong', '', shot.title || 'Работа'), node('span', '', shot.meta || ''))
      visual.append(cap)
      visual.onclick = () => openWork(index)
      strip.append(visual)
    })
    workSection.append(strip)
    screen.append(workSection)
  }

  screen.append(node('div', 'preview-note', 'Демо-версия. Запись никуда не отправляется до подключения сервиса.'))
  app.append(screen)

  const nav = node('nav', 'bottom-nav')
  nav.append(
    navButton('home', 'Главная', true, () => window.scrollTo({ top:0, behavior:'smooth' })),
    navButton('grid', 'Услуги', false, () => document.querySelector('#services')?.scrollIntoView({ behavior:'smooth' })),
    navButton('calendar', 'Моя запись', false, openMyBooking)
  )
  app.append(nav)
}

function navButton(iconName, label, active, handler) {
  const button = node('button', 'nav-item' + (active ? ' active' : ''))
  add(button, add(node('i', 'nav-icon'), icon(iconName)), document.createTextNode(label))
  button.onclick = handler
  return button
}

function openMyBooking() {
  const { sheet } = createSheet()
  sheetHeader(sheet, 'Моя запись')
  sheet.append(node('p', '', 'Здесь появится подтверждённая запись после подключения приложения.'))
  const row = node('div', 'booking-summary')
  add(row, node('strong', '', 'Ближайших записей нет'), node('span', '', 'демо'))
  sheet.append(row)
}
function days() {
  const names = ['Вс','Пн','Вт','Ср','Чт','Пт','Сб']
  const months = ['янв','фев','мар','апр','май','июн','июл','авг','сен','окт','ноя','дек']
  const out = []
  for (let i = 0; i < 7; i++) {
    const d = new Date()
    d.setDate(d.getDate() + i)
    out.push({
      label:i === 0 ? 'Сегодня' : i === 1 ? 'Завтра' : names[d.getDay()],
      day:d.getDate(),
      month:months[d.getMonth()]
    })
  }
  return out
}

function createSheet() {
  const backdrop = node('div', 'sheet-backdrop')
  const sheet = node('section', 'sheet')
  sheet.append(node('div', 'handle'))
  backdrop.append(sheet)
  document.body.append(backdrop)
  backdrop.onclick = event => {
    if (event.target === backdrop) backdrop.remove()
  }
  return { backdrop, sheet }
}

function sheetHeader(sheet, title, step) {
  const line = node('div', 'sheet-topline')
  add(
    line,
    node('h3', '', title),
    step ? node('span', 'sheet-step', step) : null
  )
  sheet.append(line)
}

function bookingSummary() {
  const summary = node('div', 'booking-summary')
  const copy = node('div')
  add(copy, node('strong', '', selected.name))
  add(
    summary,
    copy,
    node('span', '', selected.duration + ' · ' + money(selected.price))
  )
  return summary
}

function openBooking(id, prefillSlot) {
  selected = biz.services.find(service => service.id === id) || biz.services[0]
  selectedDate = 0
  selectedSlot = prefillSlot || null

  const { backdrop, sheet } = createSheet()
  sheetHeader(sheet, 'Выберите время', '1 / 2')
  sheet.append(
    node('p', '', selected.description || 'Выберите удобный день и свободное окно.'),
    bookingSummary()
  )

  const dates = node('div', 'date-strip')
  days().forEach((date, index) => {
    const button = node('button', 'date' + (index === 0 ? ' on' : ''))
    add(
      button,
      node('small', '', date.label),
      node('b', '', date.day),
      node('small', '', date.month)
    )
    button.onclick = () => {
      selectedDate = index
      dates.querySelectorAll('.date').forEach(item => item.classList.remove('on'))
      button.classList.add('on')
    }
    dates.append(button)
  })
  sheet.append(dates)

  const slots = node('div', 'slots')
  ;(biz.slots || ['10:00','11:30','13:00','15:30','17:00','19:00']).forEach(time => {
    const busy = (biz.busySlots || []).includes(time)
    const button = node(
      'button',
      'slot' + (time === selectedSlot ? ' on' : '') + (busy ? ' busy' : ''),
      time
    )
    button.onclick = () => {
      if (busy) return
      selectedSlot = time
      slots.querySelectorAll('.slot').forEach(item => item.classList.remove('on'))
      button.classList.add('on')
      next.disabled = false
    }
    slots.append(button)
  })
  sheet.append(slots)

  const next = node('button', 'primary', 'Продолжить')
  next.disabled = !selectedSlot
  next.onclick = () => details(backdrop, sheet)
  sheet.append(next)
}

function details(backdrop, sheet) {
  const date = days()[selectedDate]
  sheet.replaceChildren(node('div', 'handle'))
  sheetHeader(sheet, 'Контакты', '2 / 2')
  sheet.append(
    node(
      'p',
      '',
      date.label + ', ' + date.day + ' ' + date.month + ' · ' + selectedSlot
    ),
    bookingSummary()
  )

  ;[
    ['Имя','Как к вам обращаться','text'],
    ['Телефон','+7 999 000-00-00','tel'],
    ['Автомобиль','Например, BMW X5','text']
  ].forEach(([label, placeholder, type]) => {
    const field = node('div', 'field')
    const input = node('input')
    input.placeholder = placeholder
    input.type = type
    add(field, node('label', '', label), input)
    sheet.append(field)
  })

  sheet.append(node(
    'div',
    'privacy-hint',
    'В демо введённые данные никуда не отправляются.'
  ))

  const confirm = node('button', 'primary', 'Подтвердить запись')
  confirm.onclick = () => success(sheet)

  const back = node('button', 'secondary', 'Назад')
  back.onclick = () => {
    backdrop.remove()
    openBooking(selected.id, selectedSlot)
  }

  add(sheet, confirm, back)
}

function success(sheet) {
  sheet.replaceChildren(node('div', 'handle'))
  const wrap = node('div', 'success-wrap')
  add(
    wrap,
    add(node('div', 'success-mark'), icon('check')),
    node('h3', '', 'Запись готова'),
    node(
      'p',
      '',
      'В рабочей версии сервис получит запись, а клиент — подтверждение.'
    )
  )
  const close = node('button', 'primary', 'Вернуться')
  close.onclick = () => sheet.parentElement.remove()
  wrap.append(close)
  sheet.append(wrap)
}

function openAssistant() {
  const { backdrop, sheet } = createSheet()
  const head = node('div', 'chat-head')
  const copy = node('div')
  add(
    copy,
    node('strong', '', 'Помощник ' + (biz.shortName || biz.name)),
    node('span', '', 'подбор услуги и свободного времени')
  )
  add(head, copy)
  sheet.append(head)

  const log = node('div', 'chat-log')
  log.append(
    node('div', 'chat-line', 'Опишите, что нужно сделать с автомобилем.'),
    node('div', 'chat-line me', biz.aiExample || 'Хочу записаться завтра вечером'),
    node(
      'div',
      'chat-line',
      biz.aiAnswer || ('Подойдёт «' + biz.services[0].name + '». Есть свободное окно.')
    )
  )
  sheet.append(log)

  const actions = node('div', 'chat-actions')
  ;['Сколько займёт?', 'Что входит в услугу?', 'Какие окна сегодня?'].forEach(label => {
    actions.append(node('button', 'chat-action', label))
  })
  sheet.append(actions)

  const book = node('button', 'primary', 'Перейти к записи')
  book.onclick = () => {
    backdrop.remove()
    openBooking(biz.services[0].id, biz.nearestSlot || null)
  }
  sheet.append(book)
}

function openProfile() {
  const { sheet } = createSheet()
  sheetHeader(sheet, biz.name)
  sheet.append(node('p', '', biz.about || 'Информация о сервисе и контакты.'))

  const list = node('div', 'profile-list')
  ;[
    ['Режим работы', biz.hours || '09:00–21:00'],
    ['Адрес', biz.address || ''],
    ['Оценка', (biz.rating || '4.9') + ' · ' + (biz.reviewsLabel || 'отзывы')]
  ].forEach(([label, value]) => {
    const row = node('div', 'profile-row')
    add(row, node('strong', '', label), node('span', '', value))
    list.append(row)
  })
  sheet.append(list)

  const callButton = add(node('button', 'primary'), icon('phone'), document.createTextNode('Позвонить'))
  callButton.onclick = call
  const routeButton = node('button', 'secondary', 'Открыть карту')
  routeButton.onclick = route
  add(sheet, callButton, routeButton)
}
function openWork(index) {
  const shot = gallery()[index]
  if (!shot) return

  const { backdrop, sheet } = createSheet()
  const visual = bg(node('div', 'work-shot'), shot.src)
  visual.style.height = '320px'
  visual.style.gridRow = 'auto'

  const caption = node('span', 'work-caption')
  add(caption, node('strong', '', shot.title || 'Работа'), node('span', '', shot.meta || ''))
  visual.append(caption)
  sheet.append(visual)

  const book = node('button', 'primary', 'Записаться')
  book.onclick = () => {
    backdrop.remove()
    openBooking(biz.services[0].id)
  }
  sheet.append(book)
}

boot()
