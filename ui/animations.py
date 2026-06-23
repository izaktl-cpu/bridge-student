# -*- coding: utf-8 -*-
import tkinter as tk
import random, math

_BG   = '#1e5c1e'
_SYMS = ['♠', '♥', '♦', '♣']
_CLRS = {'♠': '#ffffff', '♥': '#ff2222', '♦': '#ff9900', '♣': '#44ff88'}
_PROB = 0.60


def maybe_animate(table):
    if random.random() > _PROB:
        return
    random.choice([_big_burst, _purple_dust, _fireworks, _big_flash])(table)


def _make(table):
    table.update_idletasks()
    x = table.winfo_rootx()
    y = table.winfo_rooty()
    w = table.winfo_width()
    h = table.winfo_height()
    top = tk.Toplevel()
    top.overrideredirect(True)
    top.geometry(f'{w}x{h}+{x}+{y}')
    top.attributes('-topmost', True)
    c = tk.Canvas(top, width=w, height=h, bg=_BG, highlightthickness=0)
    c.pack(fill='both', expand=True)
    return top, c, w, h


# ── 1. פיצוץ ענק ─────────────────────────────────────────────────────────────

def _big_burst(table):
    top, c, w, h = _make(table)
    cx, cy = w / 2, h / 2
    particles = []
    for i in range(10):
        angle = i * 36 + random.uniform(-8, 8)
        rad   = math.radians(angle)
        sym   = random.choice(_SYMS)
        size  = random.randint(40, 72)
        spd   = random.uniform(8, 16)
        tid   = c.create_text(cx, cy, text=sym,
                              font=('Arial', size, 'bold'), fill=_CLRS[sym])
        particles.append({'id': tid, 'x': cx, 'y': cy,
                          'dx': math.cos(rad)*spd, 'dy': math.sin(rad)*spd})

    FRAMES = 80
    def step(f=0):
        if f >= FRAMES:
            top.destroy()
            return
        for p in particles:
            p['x'] += p['dx']
            p['y'] += p['dy']
            p['dx'] *= 0.93
            p['dy'] *= 0.93
            c.coords(p['id'], p['x'], p['y'])
            if f > FRAMES * 0.75:
                c.itemconfig(p['id'], fill=_BG)
        c.after(30, lambda: step(f + 1))

    step()


# ── 2. אבק סגול ──────────────────────────────────────────────────────────────

def _purple_dust(table):
    top, c, w, h = _make(table)
    palette = ['#cc44ff', '#aa22ee', '#ff44ff', '#dd88ff', '#ffffff', '#ee00cc']
    particles = []
    for _ in range(55):
        x     = random.uniform(w * 0.1, w * 0.9)
        y     = random.uniform(h * 0.2, h * 0.9)
        size  = random.randint(10, 30)
        col   = random.choice(palette)
        sym   = random.choice(['✦', '✧', '★', '•', '✩', '❋', '✿'])
        vx    = random.uniform(-1.5, 1.5)
        vy    = random.uniform(-2.5, -0.5)
        delay = random.randint(0, 18)
        tid   = c.create_text(x, y, text=sym,
                              font=('Arial', size, 'bold'), fill=_BG)
        particles.append({'id': tid, 'x': x, 'y': y,
                          'vx': vx, 'vy': vy, 'col': col,
                          'delay': delay, 'born': False})

    FRAMES = 85
    def step(f=0):
        if f >= FRAMES:
            top.destroy()
            return
        for p in particles:
            if f < p['delay']:
                continue
            if not p['born']:
                c.itemconfig(p['id'], fill=p['col'])
                p['born'] = True
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] -= 0.04
            c.coords(p['id'], p['x'], p['y'])
            if f - p['delay'] > 52:
                c.itemconfig(p['id'], fill=_BG)
        c.after(30, lambda: step(f + 1))

    step()


# ── 3. זיקוקים ───────────────────────────────────────────────────────────────

def _fireworks(table):
    top, c, w, h = _make(table)

    def boom(cx, cy, col, sym, delay):
        particles = []
        for i in range(12):
            angle = i * 30 + random.uniform(-10, 10)
            rad   = math.radians(angle)
            spd   = random.uniform(7, 14)
            size  = random.randint(22, 40)
            tid   = c.create_text(cx, cy, text=sym,
                                  font=('Arial', size, 'bold'), fill=_BG)
            particles.append({'id': tid, 'x': float(cx), 'y': float(cy),
                              'dx': math.cos(rad)*spd, 'dy': math.sin(rad)*spd})

        def step(f=0):
            if f == 0:
                for p in particles:
                    c.itemconfig(p['id'], fill=col)
            if f > 36:
                for p in particles:
                    c.itemconfig(p['id'], fill=_BG)
                return
            for p in particles:
                p['x'] += p['dx']
                p['y'] += p['dy']
                p['dx'] *= 0.88
                p['dy'] *= 0.88
                c.coords(p['id'], p['x'], p['y'])
            c.after(30, lambda: step(f + 1))

        c.after(delay, step)

    blasts = [
        (w * 0.25, h * 0.3,  '#ff2222', '♥', 0),
        (w * 0.75, h * 0.3,  '#ffffff', '♠', 350),
        (w * 0.5,  h * 0.65, '#ff9900', '♦', 700),
        (w * 0.3,  h * 0.6,  '#44ff88', '♣', 1050),
    ]
    for bx, by, col, sym, d in blasts:
        boom(bx, by, col, sym, d)

    c.after(2500, top.destroy)


# ── 4. הבזק + סימן ענק ───────────────────────────────────────────────────────

def _big_flash(table):
    top, c, w, h = _make(table)
    sym = random.choice(_SYMS)
    col = _CLRS[sym]

    bg_rect = c.create_rectangle(0, 0, w, h, fill='#ffee00', outline='')
    glow    = c.create_text(w/2, h/2, text=sym,
                            font=('Arial', 130, 'bold'), fill='#ffff88')
    big_sym = c.create_text(w/2, h/2, text=sym,
                            font=('Arial', 20, 'bold'), fill=col)

    FRAMES = 83
    def step(f=0):
        if f >= FRAMES:
            top.destroy()
            return
        if f < 5:
            alpha = f / 5
        else:
            alpha = max(0.0, 1.0 - (f - 5) / (FRAMES - 5))
        v  = int(alpha * 238)
        v2 = int(alpha * 80)
        bg_col = f'#{v:02x}{v:02x}{v2:02x}' if alpha > 0.03 else _BG
        c.itemconfig(bg_rect, fill=bg_col)
        size = min(110, 20 + f * 7) if f < 15 else 110
        c.itemconfig(big_sym, font=('Arial', int(size), 'bold'))
        if f > 58:
            c.itemconfig(big_sym, fill=_BG)
            c.itemconfig(glow, fill=_BG)
        c.after(30, lambda: step(f + 1))

    step()


# ── Owl animations ───────────────────────────────────────────────────────────

_owl_count     = 0
_owl_threshold = random.randint(3, 4)


def owl_correct(table):
    global _owl_count, _owl_threshold
    _owl_count += 1
    if _owl_count >= _owl_threshold:
        _owl_count     = 0
        _owl_threshold = random.randint(3, 4)
        _show_owl(table, correct=True)


def owl_wrong(table, correct_answer=''):
    global _owl_count, _owl_threshold
    _owl_count += 1
    if _owl_count >= _owl_threshold:
        _owl_count     = 0
        _owl_threshold = random.randint(3, 4)
        _show_owl(table, correct=False, correct_answer=str(correct_answer))


def _show_owl(table, correct=True, correct_answer=''):
    top, c, w, h = _make(table)

    BROWN    = '#8B5E3C'
    DARK     = '#4A2C0A'
    CREAM    = '#F5DEB3'
    YELLOW   = '#FFD700'
    flag_col = '#00CC44' if correct else '#DD2222'

    # Owl center — left of window so flag has room on the right
    cx = int(w * 0.38)
    cy = int(h * 0.60)

    # Body
    c.create_oval(cx-55, cy-20, cx+55, cy+90, fill=BROWN, outline=DARK, width=2)
    # Belly
    c.create_oval(cx-28, cy+15, cx+28, cy+82, fill=CREAM, outline='')
    for i in range(3):
        yy = cy + 32 + i * 16
        c.create_arc(cx-20, yy-6, cx+20, yy+6, start=0, extent=180,
                     style='arc', outline=DARK, width=1)

    # Head
    hx, hy = cx, cy - 68
    c.create_oval(hx-45, hy-38, hx+45, hy+38, fill=BROWN, outline=DARK, width=2)
    # Ear tufts
    c.create_polygon(hx-35, hy-22, hx-22, hy-62, hx-10, hy-22,
                     fill=BROWN, outline=DARK, width=1)
    c.create_polygon(hx+10, hy-22, hx+22, hy-62, hx+35, hy-22,
                     fill=BROWN, outline=DARK, width=1)

    # Eyes (large!)
    c.create_oval(hx-34, hy-18, hx-6,  hy+14, fill=YELLOW, outline=DARK, width=2)
    c.create_oval(hx+6,  hy-18, hx+34, hy+14, fill=YELLOW, outline=DARK, width=2)
    c.create_oval(hx-28, hy-10, hx-12, hy+8,  fill='#111111')
    c.create_oval(hx+12, hy-10, hx+28, hy+8,  fill='#111111')
    # Eye shine
    c.create_oval(hx-25, hy-8,  hx-20, hy-3,  fill='white')
    c.create_oval(hx+15, hy-8,  hx+20, hy-3,  fill='white')

    # Beak
    c.create_polygon(hx-7, hy+8, hx, hy+22, hx+7, hy+8,
                     fill='#FF8C00', outline=DARK, width=1)

    # Wings
    c.create_oval(cx-88, cy+5,  cx-20, cy+65, fill=BROWN, outline=DARK, width=2)
    c.create_oval(cx+18, cy-58, cx+92, cy+8,  fill=BROWN, outline=DARK, width=2)

    # Legs
    c.create_line(cx-20, cy+88, cx-25, cy+108, fill=DARK, width=3)
    c.create_line(cx-25, cy+108, cx-38, cy+108, fill=DARK, width=3)
    c.create_line(cx-25, cy+108, cx-20, cy+116, fill=DARK, width=3)
    c.create_line(cx+20, cy+88, cx+25, cy+108, fill=DARK, width=3)
    c.create_line(cx+25, cy+108, cx+38, cy+108, fill=DARK, width=3)
    c.create_line(cx+25, cy+108, cx+20, cy+116, fill=DARK, width=3)

    # Flag pole
    px     = cx + 85
    py_top = cy - 95
    py_bot = cy + 5
    c.create_line(px, py_top, px, py_bot, fill='#AAAAAA', width=4)

    # Flag (animated)
    fw, fh = 72, 42
    flag = c.create_polygon(
        px,    py_top,
        px+fw, py_top + 6,
        px+fw, py_top + fh + 6,
        px,    py_top + fh,
        fill=flag_col, outline='white', width=1
    )

    # Header text
    msg     = 'כל הכבוד! ✓' if correct else '✗ לא נכון'
    msg_col = '#44FF88'           if correct else '#FF5555'
    c.create_text(w // 2, int(h * 0.10), text=msg,
                  font=('Arial', 28, 'bold'), fill=msg_col)

    # Sign with correct answer (wrong only)
    if not correct and correct_answer:
        sx = min(int(w * 0.72), w - 75)
        sy = int(h * 0.52)
        c.create_line(sx, sy + 55, sx, sy + 12, fill='#AA8855', width=4)
        c.create_rectangle(sx-62, sy-32, sx+62, sy+15,
                           fill='#FFFDE0', outline='#AA8855', width=3)
        c.create_text(sx, sy - 18, text='התשובה הנכונה:',
                      font=('Arial', 11), fill='#555500')
        c.create_text(sx, sy + 2,  text=correct_answer,
                      font=('Arial', 20, 'bold'), fill='#003300')

    # כיוון כניסה אקראי: שמאל / ימין / מלמעלה
    entry = random.choice(['left', 'right', 'top'])
    if entry == 'left':
        off_x, off_y = -(w + 60), 0
    elif entry == 'right':
        off_x, off_y =  (w + 60), 0
    else:
        off_x, off_y = 0, -(h + 60)

    c.move('all', off_x, off_y)  # מתחיל מחוץ למסך

    # Animation phases (40 ms per frame):
    #   IN:   כניסה          30f = 1.2s
    #   WAVE: מנפנף במקום    50f = 2.0s
    #   OUT:  יורד למטה      40f = 1.6s
    #   STAY: עצירה למטה     20f = 0.8s
    IN   = 30
    WAVE = 50
    OUT  = 40
    STAY = 20

    in_dx  = -off_x / IN
    in_dy  = -off_y / IN
    out_dy = (h + 50) / OUT

    def step(f=0):
        if f >= IN + WAVE + OUT + STAY:
            top.destroy()
            return

        if f < IN:
            # כניסה מהצד
            c.move('all', in_dx, in_dy)
        elif f < IN + WAVE:
            # ניפנוף דגל
            wf   = f - IN
            wave = math.sin(wf * 0.28) * 14
            c.coords(flag,
                     px,    py_top,
                     px+fw, py_top + 6  + wave,
                     px+fw, py_top + fh + 6 + wave,
                     px,    py_top + fh)
        elif f < IN + WAVE + OUT:
            # יציאה למטה
            c.move('all', 0, out_dy)

        c.after(40, lambda: step(f + 1))

    step()
