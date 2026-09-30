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
  message: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 15a4 4 0 0 1-4 4H8l-5 3 1.5-5A7 7 0 0 1 3 13V8a5 5 0 0 1 5-5h8a5 5 0 0 1 5 5v7Z"/></svg>',
  user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
  pin: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></svg>',
  clock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  star: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m12 3 2.7 5.46 6.03.88-4.36 4.25 1.03 6-5.4-2.84-5.4 2.84 1.03-6-4.36-4.25 6.03-.88L12 3Z"/></svg>',
  chevron: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m9 18 6-6-6-6"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m5 12 4 4L19 6"/></svg>'
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

  const topbar = node('header', 'topbar')
  const mark = node(
    'div',
    'brand-mark',
    biz.logoMark || String(biz.shortName || biz.name).slice(0, 2).toUpperCase()
  )
  const brandCopy = node('div', 'brand-copy')
  add(
    brandCopy,
    node('strong', '', biz.shortName || biz.name),
    node('span', '', biz.category || 'Автосервис')
  )
  const phone = add(node('button', 'top-action'), icon('phone'))
  phone.ariaLabel = 'Позвонить'
  phone.onclick = call
  add(topbar, mark, brandCopy, phone)
  app.append(topbar)

  const home = node('main', 'home')
  const cover = bg(node('section', 'cover'), biz.hero)
  const coverMeta = node('div', 'cover-meta')
  const status = node('div', 'cover-status')
  add(status, node('i'), document.createTextNode(biz.status || 'Открыто сегодня'))
  const rating = node('div', 'cover-rating')
  add(
    rating,
    node('strong', '', (biz.rating || '4.9') + ' ★'),
    node('span', '', biz.reviewsLabel || 'по отзывам клиентов')
  )
  add(coverMeta, status, rating)
  cover.append(coverMeta)
  home.append(cover)

  const nearest = biz.nearestSlot || (biz.slots || [])[0] || '10:00'
  const bookingSection = section('Запись', 'свободное время')
  const slotRow = node('div', 'next-slot')
  const slotCopy = node('div')
  add(
    slotCopy,
    node('div', 'next-slot-label', 'Ближайшее окно'),
    node('strong', '', (biz.nearestLabel || 'Сегодня') + ', ' + nearest),
    node('small', '', biz.nearestNote || 'Подтверждение за минуту')
  )
  const slotButton = node('button', '', 'Выбрать')
  slotButton.onclick = () => openBooking(biz.services[0].id, nearest)
  add(slotRow, slotCopy, slotButton)
  bookingSection.append(slotRow)
  home.append(bookingSection)

  const serviceSection = section('Услуги', biz.services.length + ' доступно')
  const serviceList = node('div', 'service-list')
  biz.services.forEach(service => {
    const row = node('button', 'service-row')
    const copy = node('div')
    add(
      copy,
      node('div', 'service-title', service.name),
      node('div', 'service-meta', service.duration + (service.note ? ' · ' + service.note : ''))
    )
    const price = node('div', 'service-price', (service.pricePrefix ? service.pricePrefix + ' ' : '') + money(service.price))
    price.append(node('span', '', 'от'))
    add(row, copy, price)
    row.onclick = () => openBooking(service.id)
    serviceList.append(row)
  })
  serviceSection.append(serviceList)
  home.append(serviceSection)

  const shots = gallery().slice(0, 3)
  if (shots.length) {
    const workSection = section('Работы', biz.galleryLabel || 'последние')
    const grid = node('div', 'work-grid')
    shots.forEach((shot, index) => {
      const visual = bg(node('button', 'work-shot'), shot.src)
      const caption = node('span', 'work-caption')
      add(
        caption,
        node('strong', '', shot.title || 'Работа'),
        node('span', '', shot.meta || '')
      )
      visual.append(caption)
      visual.onclick = () => openWork(index)
      grid.append(visual)
    })
    workSection.append(grid)
    home.append(workSection)
  }

  const infoSection = section('Сервис', biz.city || '')
  const facts = node('div', 'fact-list')
  facts.append(
    factRow('clock', 'Сегодня', biz.hours || '09:00–21:00'),
    factRow('pin', 'Адрес', biz.address || 'Открыть на карте', route),
    factRow('star', 'Оценка', (biz.rating || '4.9') + ' · ' + (biz.reviewsLabel || 'отзывы'))
  )
  infoSection.append(facts)
  home.append(infoSection)

  home.append(node(
    'div',
    'preview-note',
    'Демо-версия. Запись не отправляется в сервис, пока приложение не подключено.'
  ))
  app.append(home)

  const nav = node('nav', 'bottom-nav')
  nav.append(
    navButton('home', 'Главная', true, () => window.scrollTo({ top:0, behavior:'smooth' })),
    navButton('calendar', 'Запись', false, () => openBooking(biz.services[0].id)),
    navButton('message', 'Помощник', false, openAssistant),
    navButton('user', 'Сервис', false, openProfile)
  )
  app.append(nav)
}

function section(title, meta) {
  const wrap = node('section', 'section')
  const head = node('div', 'section-head')
  add(head, node('h2', '', title), node('span', '', meta || ''))
  wrap.append(head)
  return wrap
}

function factRow(iconName, title, value, onClick) {
  const row = node(onClick ? 'button' : 'div', 'fact-row')
  add(row, icon(iconName), node('strong', '', title), node('span', '', value))
  if (onClick) {
    row.style.width = '100%'
    row.style.borderLeft = '0'
    row.style.borderRight = '0'
    row.style.background = 'transparent'
    row.style.textAlign = 'left'
    row.style.cursor = 'pointer'
    row.onclick = onClick
  }
  return row
}

function navButton(iconName, label, active, handler) {
  const button = node('button', 'nav-item' + (active ? ' active' : ''))
  add(button, add(node('i', 'nav-icon'), icon(iconName)), document.createTextNode(label))
  button.onclick = handler
  return button
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

  const facts = node('div', 'fact-list')
  facts.append(
    factRow('clock', 'Режим работы', biz.hours || '09:00–21:00'),
    factRow('pin', 'Адрес', biz.address || '', route),
    factRow('star', 'Оценка', (biz.rating || '4.9') + ' · ' + (biz.reviewsLabel || 'отзывы'))
  )
  sheet.append(facts)

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
