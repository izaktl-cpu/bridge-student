'use strict';

const SUIT_SYM = { S: '♠', H: '♥', D: '♦', C: '♣' };
const SUIT_CLASS = { S: 'spades', H: 'hearts', D: 'diamonds', C: 'clubs' };
const SUIT_RED = { H: true, D: true, S: false, C: false };
const SEAT_NAME = { N: 'North', E: 'East', S: 'South ★', W: 'West' };
const PLAYERS = ['N', 'E', 'S', 'W'];

let STATE = null;      // תמונת המצב האחרונה מהשרת
let LESSON_IDX = 0;

// ── קריאות שרת ──────────────────────────────────────────────────────────────
async function api(path, body) {
  const res = await fetch('/api/' + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'שגיאת שרת');
  }
  return res.json();
}

async function newDeal(idx) {
  LESSON_IDX = idx;
  const state = await api('new_deal', { lesson_idx: idx, session_id: STATE?.session_id });
  render(state);
}

async function sendBid(bid) {
  const state = await api('bid', { session_id: STATE.session_id, bid });
  render(state);
}

async function replay() {
  const state = await api('replay', { session_id: STATE.session_id, bid: '' });
  render(state);
}

// ── סרגל שיעורים ────────────────────────────────────────────────────────────
async function loadLessons() {
  const res = await fetch('/api/lessons');
  const { buttons } = await res.json();
  const bar = document.getElementById('lesson-bar');
  bar.innerHTML = '';
  // שתי שורות: 8 עליונה, 7 תחתונה
  const chunks = [buttons.slice(0, 8), buttons.slice(8)];
  chunks.forEach(group => {
    const row = document.createElement('div');
    row.className = 'lesson-row';
    group.forEach(({ label, idx }) => {
      const b = document.createElement('button');
      b.className = 'lesson-btn';
      b.dataset.idx = idx;
      b.innerHTML = htmlBids(label);
      b.onclick = () => newDeal(idx);
      row.appendChild(b);
    });
    bar.appendChild(row);
  });
}

// בנייד המשוב מוצמד לתיבת המכרז במרכז השולחן; בדסקטופ נשאר בסיידבר.
const _fbMobileMQ = window.matchMedia('(max-width: 700px)');
function placeFeedback() {
  const fb = document.getElementById('feedback');
  if (!fb) return;
  if (_fbMobileMQ.matches) {
    document.querySelector('.center').appendChild(fb);              // נייד: מתחת למכרז
  } else {
    document.getElementById('side')
      .insertBefore(fb, document.getElementById('bidding-box'));    // דסקטופ: בסיידבר (order:2)
  }
}

// ── ציור ───────────────────────────────────────────────────────────────────
function render(state) {
  STATE = state;
  LESSON_IDX = state.lesson_idx;
  markActiveLesson();
  renderHands(state.hands);
  renderAuction(state.auction);
  renderPanel(state.panel);
  placeFeedback();
  renderFeedback(state.feedback);
  renderBiddingBox(state.bidding_box);
  markActiveSeat(state);
}

// מסמן בקו צהוב את המושב שתורו להכריז (המושב הבא אחרי ההכרזה האחרונה)
function markActiveSeat(state) {
  const a = state.auction;
  const dealerIdx = PLAYERS.indexOf(a.dealer);
  const activeSeat = state.done ? null : PLAYERS[(dealerIdx + a.bids.length) % 4];
  PLAYERS.forEach(seat => {
    const el = document.querySelector(`.seat[data-seat="${seat}"]`);
    if (el) el.classList.toggle('active', seat === activeSeat);
  });
}

function markActiveLesson() {
  document.querySelectorAll('.lesson-btn').forEach(b => {
    b.classList.toggle('active', Number(b.dataset.idx) === LESSON_IDX);
  });
}

function renderHands(hands) {
  PLAYERS.forEach(seat => {
    const el = document.querySelector(`.seat[data-seat="${seat}"]`);
    const h = hands[seat];
    if (!h) { el.innerHTML = ''; return; }
    let html = `<div class="seat-name">${SEAT_NAME[seat]}</div>`;
    if (h.visible) {
      html += `<div class="seat-hcp"><bdi>${h.hcp}</bdi> נק׳</div>`;
      ['S', 'H', 'D', 'C'].forEach(s => {
        const cards = h.suits[s];
        const txt = cards.length ? cards.join(' ') : '—';
        const cls = SUIT_RED[s] ? 'red' : 'black';
        html += `<div class="suit-row"><span class="suit-sym ${cls}">${SUIT_SYM[s]}</span>` +
                `<span class="suit-cards ${cls}">${txt}</span></div>`;
      });
      el.classList.remove('hidden-hand');
    } else {
      ['S', 'H', 'D', 'C'].forEach(s => {
        const cls = SUIT_RED[s] ? 'red' : 'black';
        html += `<div class="suit-row"><span class="suit-sym ${cls}">${SUIT_SYM[s]}</span>` +
                `<span class="suit-cards">■ ■ ■</span></div>`;
      });
      el.classList.add('hidden-hand');
    }
    el.innerHTML = html;
  });
}

function auctionGridHTML(auction) {
  const dealerIdx = PLAYERS.indexOf(auction.dealer);
  let cells = [];
  // תאים ריקים עד המחלק
  for (let i = 0; i < dealerIdx; i++) cells.push(null);
  auction.bids.forEach(b => cells.push(b));

  let html = '<div class="auction-grid">';
  PLAYERS.forEach(p => html += `<div class="ah">${p}</div>`);
  cells.forEach(c => {
    if (c === null) { html += '<div class="ac"></div>'; return; }
    const hl = c.highlight ? ' hl' : '';
    html += `<div class="ac${hl}"><span class="bid">${bidText(c.bid)}</span></div>`;
  });
  html += '</div>';
  return html;
}

function renderAuction(auction) {
  document.getElementById('auction').innerHTML = auctionGridHTML(auction);
}

function renderPanel(panel) {
  const el = document.getElementById('panel');
  let html = '';
  if (panel.header) html += `<div class="panel-header">${htmlBids(panel.header)}</div>`;
  if (panel.text) {
    html += '<div class="panel-text">';
    panel.text.split('\n').forEach(line => {
      html += `<div class="line">${htmlBids(line)}</div>`;
    });
    html += '</div>';
  }
  (panel.tables || []).forEach(rows => { html += optTable(rows); });
  el.innerHTML = html;
  el.style.display = html ? '' : 'none';
}

function optTable(rows) {
  if (!rows.length) return '';
  const threeCol = rows[0].length === 3;
  let html = '<table class="opt-table">';
  if (threeCol) {
    html += '<tr><th>הכרזה</th><th>תמיכה עם</th><th>נקודות</th></tr>';
    rows.forEach(([pts, sup, bid]) => {
      html += `<tr><td class="opt-bid"><span class="bid">${bidText(bid)}</span></td>` +
              `<td>${htmlBids(sup)}</td><td>${htmlBids(pts)}</td></tr>`;
    });
  } else {
    rows.forEach(([bid, cond]) => {
      html += `<tr><td class="opt-bid"><span class="bid">${bidText(bid)}</span></td>` +
              `<td style="text-align:right">${htmlBids(cond)}</td></tr>`;
    });
  }
  html += '</table>';
  return html;
}

function renderFeedback(fb) {
  const el = document.getElementById('feedback');
  if (!fb.shown || (!fb.text && !fb.ok)) {
    el.className = ''; el.innerHTML = ''; return;
  }
  el.className = 'show ' + (fb.ok ? 'ok' : 'wrong');
  const lines = (fb.text || (fb.ok ? 'נכון' : '')).split('\n').filter(l => l.trim());
  el.innerHTML = lines.map((l, i) =>
    `<div class="fb-line${i === 0 ? ' fb-big' : ''}">${htmlBids(l)}</div>`).join('');
}

function bidClass(bid) {
  if (bid === 'Pass') return 's-pass';
  if (bid === 'X') return 's-x';
  if (bid === 'XX') return 's-xx';
  const s = bid.slice(1);
  return { '♣': 's-clubs', '♦': 's-diamonds', '♥': 's-hearts', '♠': 's-spades', 'NT': 's-nt' }[s] || 's-nt';
}

function bidText(bid) {
  return bid === 'Pass' ? 'פס' : bid;
}

function renderBiddingBox(bb) {
  const el = document.getElementById('bidding-box');
  const enabled = new Set(bb.enabled);
  const SUITS = ['♣', '♦', '♥', '♠', 'NT'];
  let html = '<div class="bb-title">בבקשה הכרז</div>';

  html += '<div class="bb-row">';
  ['Pass', 'X', 'XX'].forEach(b => html += bbBtn(b, enabled.has(b) && !bb.locked));
  html += '</div>';

  for (let lvl = 1; lvl <= 7; lvl++) {
    html += '<div class="bb-row">';
    SUITS.forEach(s => {
      const bid = lvl + s;
      html += bbBtn(bid, enabled.has(bid) && !bb.locked);
    });
    html += '</div>';
  }
  el.innerHTML = html;
  el.querySelectorAll('.bb-btn').forEach(btn => {
    if (!btn.disabled) btn.onclick = () => sendBid(btn.dataset.bid);
  });
}

function bbBtn(bid, on) {
  const dis = on ? '' : 'disabled';
  return `<button class="bb-btn ${bidClass(bid)}" data-bid="${bid}" ${dis}>${bidText(bid)}</button>`;
}

// עוטף כל אשכול לטיני/הכרזה/מספר ב-bdi כדי שלא יתהפך בתוך עברית
function htmlBids(text) {
  if (text === null || text === undefined) return '';
  const s = String(text);
  return s.replace(/([0-9A-Za-z♣♦♥♠]+(?:[-–][0-9A-Za-z♣♦♥♠]+)*(?:NT)?\+?)/g,
    m => `<bdi class="bid">${m}</bdi>`);
}

// ── כפתור "נתקעתי" ──────────────────────────────────────────────────────────
function toast(msg) {
  const t = document.getElementById('toast') || (() => {
    const d = document.createElement('div'); d.id = 'toast'; document.body.appendChild(d); return d;
  })();
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2600);
}

function closeModal() {
  const m = document.getElementById('stuck-modal');
  if (m) m.remove();
}

function reportStuck() {
  if (!STATE || !STATE.session_id) { toast('התחל יד קודם'); return; }
  closeModal();
  const overlay = document.createElement('div');
  overlay.id = 'stuck-modal';
  overlay.innerHTML = `
    <div class="modal-box">
      <div class="modal-title">נתקעת? שלח דיווח למורה 🆘</div>
      <div class="modal-sub">היד והמכרז יישלחו אוטומטית. אפשר להוסיף מה לא היה ברור (לא חובה):</div>
      <textarea id="stuck-note" dir="auto" rows="3" placeholder="למשל: לא הבנתי למה לא להכריז 4NT"></textarea>
      <div class="modal-sub modal-reply">תרצה שאשיב לך? השאר מייל.</div>
      <div class="modal-btns">
        <button id="stuck-send" class="ctl ctl-new">שלח</button>
        <button id="stuck-cancel" class="ctl ctl-replay">ביטול</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);
  overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
  document.getElementById('stuck-cancel').onclick = closeModal;
  document.getElementById('stuck-send').onclick = async () => {
    const note = document.getElementById('stuck-note').value;
    const btn = document.getElementById('stuck-send');
    btn.disabled = true; btn.textContent = 'שולח...';
    try {
      const r = await api('report', { session_id: STATE.session_id, note });
      closeModal();
      toast(r.emailed ? 'נשלח למורה, תודה! ✅' : 'הדיווח נשמר, תודה! ✅');
    } catch (e) {
      btn.disabled = false; btn.textContent = 'שלח';
      toast('שגיאה בשליחה, נסה שוב');
    }
  };
}

// ── אתחול ───────────────────────────────────────────────────────────────────
_fbMobileMQ.addEventListener('change', placeFeedback);
placeFeedback();

document.getElementById('btn-new').onclick = () => newDeal(LESSON_IDX);
document.getElementById('btn-replay').onclick = () => replay();
document.getElementById('btn-stuck').onclick = () => reportStuck();

(async function init() {
  await loadLessons();
  await newDeal(0);
})();
