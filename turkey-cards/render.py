#!/usr/bin/env python3
"""Карточки постов «Пространство Аланья» — единый стиль: тёмно-синий + золото.

    python3 render.py card.json out_dir/  [--name имя]

Рисует два файла из одного описания:
    <имя>-tall.png  1080×1350 (4:5) — Instagram, Threads
    <имя>-wide.png  1280×720  (16:9) — Telegram

Иллюстрация выбирается по полю "topic" (см. TOPICS ниже и README.md).
Код выхода 2 — текст не влез, сократите заголовок/подзаголовок.
"""
import base64, html, json, math, mimetypes, pathlib, sys

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
FONTS = HERE / "fonts"
LOGO = HERE / "assets" / "logo-gold.png"

NAVY, PANEL, LINE, GOLD, CREAM, MUTED = "#0E1A2B", "#13233A", "#2C4058", "#D9A441", "#EDE6D6", "#8FA0B3"
CHANNEL = "@prostranstvo_alanya"

TOPICS = {
    "districts": "районы, кварталы, открыты/закрыты для ВНЖ",
    "rate": "курс лиры, решения ЦБ, пороги 200/400 тыс. $",
    "law": "законы, правила ВНЖ/гражданства, проверки, аннулирования",
    "calendar": "90/180, зимовка, сроки, афиша, каникулы",
    "stats": "статистика продаж, цены, число ВНЖ, турпоток",
    "payments": "платежи и переводы, карты, банки",
    "tariffs": "тарифы, коммуналка, стоимость жизни",
    "property": "обзор/показ квартиры, разбор объекта",
}


def esc(s):
    return html.escape(str(s or ""))


def data_uri(path):
    p = pathlib.Path(path)
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def css():
    f = FONTS.as_uri()
    return f"""
@font-face{{font-family:'PT Serif';src:url('{f}/PT_Serif-Web-Regular.ttf');font-weight:400}}
@font-face{{font-family:'PT Serif';src:url('{f}/PT_Serif-Web-Bold.ttf');font-weight:700}}
@font-face{{font-family:'Mono';src:url('{f}/IBMPlexMono-Regular.ttf');font-weight:400}}
@font-face{{font-family:'Mono';src:url('{f}/IBMPlexMono-Medium.ttf');font-weight:500}}
@font-face{{font-family:'Playfair';src:url('{f}/PlayfairDisplay-VF.ttf');font-weight:400 900}}
@font-face{{font-family:'Manrope';src:url('{f}/Manrope-VF.ttf');font-weight:200 800}}
*{{box-sizing:border-box}} body{{margin:0;background:{NAVY}}}
.k{{font-family:Mono;letter-spacing:4px;text-transform:uppercase}}
"""


# ───────────────────────── иллюстрации (SVG, квадрат 560×560) ─────────────────────────
S = 560


def frame(inner, label):
    grid = "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="{S}" stroke="{LINE}" stroke-width="1" opacity=".45"/>'
                   for x in range(40, S, 40))
    grid += "".join(f'<line x1="0" y1="{y}" x2="{S}" y2="{y}" stroke="{LINE}" stroke-width="1" opacity=".45"/>'
                    for y in range(40, S, 40))
    return f"""<svg width="100%" height="100%" viewBox="0 0 {S} {S}" xmlns="http://www.w3.org/2000/svg" style="display:block">
<rect width="{S}" height="{S}" fill="{PANEL}"/>{grid}
<rect x="1" y="1" width="{S-2}" height="{S-2}" fill="none" stroke="{LINE}" stroke-width="2"/>
<text x="{S-24}" y="34" text-anchor="end" font-family="Mono" font-size="15" letter-spacing="3" fill="{GOLD}">{esc(label)}</text>
{inner}</svg>"""


def ill_districts(items):
    # сетка кварталов 6×6, «открытые» — золотой крест в центре, как на карточке «Снова открыты»
    open_cells = {(1, 1), (2, 1), (0, 2), (1, 2), (2, 2), (3, 2), (1, 3), (2, 3), (3, 3), (4, 3), (2, 4)}
    cells, x0, y0, c, g = "", 70, 80, 64, 8
    for r in range(6):
        for col in range(6):
            x, y = x0 + col * (c + g), y0 + r * (c + g)
            if (col, r) in open_cells:
                cells += f'<rect x="{x}" y="{y}" width="{c}" height="{c}" fill="{GOLD}"/>'
            else:
                cells += f'<rect x="{x}" y="{y}" width="{c}" height="{c}" fill="none" stroke="{LINE}" stroke-width="2"/>'
                if (r + col) % 3 == 0:
                    cells += f'<line x1="{x+14}" y1="{y+c/2}" x2="{x+c-14}" y2="{y+c/2}" stroke="{MUTED}" stroke-width="2" opacity=".6"/>'
    legend = (f'<rect x="70" y="520" width="16" height="16" fill="{GOLD}"/><text x="94" y="533" font-family="Mono" font-size="14" fill="{MUTED}">открыт</text>'
              f'<rect x="200" y="520" width="16" height="16" fill="none" stroke="{MUTED}" stroke-width="2"/><text x="224" y="533" font-family="Mono" font-size="14" fill="{MUTED}">закрыт</text>')
    return cells + legend


def ill_rate(items):
    vals = [float(v) for v in items][:12] if items and all(_isnum(v) for v in items) else [30, 31, 31.5, 33, 34, 34.2, 36, 37.5, 38, 39.4, 40.1, 41.3]
    lo, hi = min(vals), max(vals)
    pts = []
    for i, v in enumerate(vals):
        x = 70 + i * (420 / (len(vals) - 1))
        y = 440 - (v - lo) / ((hi - lo) or 1) * 300
        pts.append((x, y))
    poly = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    area = f"70,460 {poly} 490,460"
    dots = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="5" fill="{NAVY}" stroke="{GOLD}" stroke-width="3"/>' for x, y in pts)
    thr = f'<line x1="70" y1="200" x2="490" y2="200" stroke="{CREAM}" stroke-width="2" stroke-dasharray="8 8" opacity=".6"/>' \
          f'<text x="70" y="188" font-family="Mono" font-size="14" fill="{MUTED}">порог в $ по курсу ЦБ</text>'
    axis = f'<line x1="70" y1="460" x2="490" y2="460" stroke="{MUTED}" stroke-width="2"/>'
    return f'<polygon points="{area}" fill="{GOLD}" opacity=".12"/>{thr}{axis}<polyline points="{poly}" fill="none" stroke="{GOLD}" stroke-width="4"/>{dots}'


def ill_law(items):
    lines = "".join(f'<rect x="150" y="{y}" width="{w}" height="10" fill="{MUTED}" opacity=".55"/>'
                    for y, w in [(170, 200), (200, 240), (230, 180), (260, 230), (290, 150), (340, 220), (370, 190)])
    doc = f'<rect x="120" y="110" width="300" height="380" fill="none" stroke="{CREAM}" stroke-width="3"/>' \
          f'<rect x="150" y="135" width="120" height="14" fill="{GOLD}"/>{lines}'
    stamp = f'<g transform="translate(390,400) rotate(-14)"><circle r="78" fill="none" stroke="{GOLD}" stroke-width="5"/>' \
            f'<circle r="62" fill="none" stroke="{GOLD}" stroke-width="2"/>' \
            f'<path d="M-26 2 L-6 22 L30 -20" fill="none" stroke="{GOLD}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/></g>'
    return doc + stamp


def ill_calendar(items):
    # 6 месяцев × 30 дней, золотом — диапазон (по умолчанию 90 дней из 180)
    out, x0, y0 = "", 70, 110
    months = items[:6] if items and len(items) >= 6 else ["НОЯ", "ДЕК", "ЯНВ", "ФЕВ", "МАР", "АПР"]
    for m in range(6):
        x = x0 + m * 72
        out += f'<text x="{x+26}" y="{y0-16}" text-anchor="middle" font-family="Mono" font-size="14" fill="{MUTED}">{esc(months[m])}</text>'
        for d in range(15):
            for h in range(2):
                day = m * 30 + d * 2 + h
                cx, cy = x + 12 + h * 28, y0 + 10 + d * 24
                on = day < 90
                out += f'<rect x="{cx-9}" y="{cy-9}" width="18" height="18" fill="{GOLD if on else "none"}" stroke="{GOLD if on else LINE}" stroke-width="2"/>'
    out += f'<text x="70" y="520" font-family="Mono" font-size="15" fill="{GOLD}">90 из 180 дней</text>'
    return out


def ill_stats(items):
    vals = [float(v) for v in items][:7] if items and all(_isnum(v) for v in items) else [42, 55, 48, 63, 58, 71, 86]
    hi = max(vals) or 1
    bw, gap, out = 44, 14, ""
    for i, v in enumerate(vals):
        h = v / hi * 330
        x = 70 + i * (bw + gap)
        last = i == len(vals) - 1
        out += f'<rect x="{x}" y="{460-h:.0f}" width="{bw}" height="{h:.0f}" fill="{GOLD if last else "none"}" stroke="{GOLD if last else MUTED}" stroke-width="2"/>'
    return out + f'<line x1="60" y1="460" x2="500" y2="460" stroke="{MUTED}" stroke-width="2"/>'


def ill_payments(items):
    card = lambda x, y, fill: (f'<rect x="{x}" y="{y}" width="230" height="146" rx="14" fill="{fill}" stroke="{GOLD}" stroke-width="3"/>'
                               f'<rect x="{x+22}" y="{y+30}" width="40" height="30" rx="4" fill="{NAVY if fill == GOLD else GOLD}"/>'
                               f'<rect x="{x+22}" y="{y+100}" width="150" height="10" fill="{NAVY if fill == GOLD else MUTED}" opacity=".7"/>')
    arrow = f'<path d="M190 330 C 250 330, 300 300, 330 260" fill="none" stroke="{CREAM}" stroke-width="3" stroke-dasharray="10 8"/>' \
            f'<path d="M318 262 L334 256 L336 274" fill="none" stroke="{CREAM}" stroke-width="3"/>'
    return card(60, 330, "none") + card(270, 110, GOLD) + arrow + \
        f'<text x="60" y="510" font-family="Mono" font-size="15" fill="{MUTED}">RUB</text><text x="500" y="90" text-anchor="end" font-family="Mono" font-size="15" fill="{GOLD}">TRY</text>'


def ill_tariffs(items):
    # счётчик-«лампа» + ступени тарифа
    steps = "".join(f'<rect x="{80+i*80}" y="{460-(i+1)*60}" width="70" height="{(i+1)*60}" fill="{GOLD if i == 4 else "none"}" stroke="{GOLD if i == 4 else MUTED}" stroke-width="2"/>'
                    for i in range(5))
    bulb = f'<circle cx="420" cy="150" r="56" fill="none" stroke="{GOLD}" stroke-width="4"/>' \
           f'<rect x="398" y="206" width="44" height="30" fill="none" stroke="{GOLD}" stroke-width="4"/>' \
           f'<path d="M405 160 L420 130 L420 158 L435 140" fill="none" stroke="{GOLD}" stroke-width="4" stroke-linejoin="round"/>'
    return steps + bulb


def ill_property(items, photo=None):
    if photo:
        return (f'<defs><clipPath id="arch"><path d="M110 500 V250 A170 170 0 0 1 450 250 V500 Z"/></clipPath></defs>'
                f'<image href="{esc(photo)}" x="110" y="80" width="340" height="420" preserveAspectRatio="xMidYMid slice" clip-path="url(#arch)"/>'
                f'<path d="M110 500 V250 A170 170 0 0 1 450 250 V500" fill="none" stroke="{GOLD}" stroke-width="6"/>')
    win = "".join(f'<rect x="{x}" y="{y}" width="36" height="36" fill="{GOLD if (x + y) % 3 == 0 else "none"}" stroke="{GOLD}" stroke-width="2"/>'
                  for x in range(180, 380, 56) for y in range(200, 440, 56))
    return (f'<path d="M110 500 V250 A170 170 0 0 1 450 250 V500" fill="none" stroke="{GOLD}" stroke-width="6"/>{win}'
            f'<path d="M60 500 C 150 480, 200 520, 280 500 S 420 480, 500 500" fill="none" stroke="{MUTED}" stroke-width="3"/>')


ILL = {"districts": ill_districts, "rate": ill_rate, "law": ill_law, "calendar": ill_calendar,
       "stats": ill_stats, "payments": ill_payments, "tariffs": ill_tariffs, "property": ill_property}


def _isnum(v):
    try:
        float(v); return True
    except (TypeError, ValueError):
        return False


def illustration(d):
    topic = d.get("topic") if d.get("topic") in ILL else "law"
    items = d.get("items") or []
    label = d.get("fig") or f"{topic.upper()[:3]}. {d.get('date', '')[:5]}"
    if topic == "property":
        photo = d.get("photo")
        if photo and not str(photo).startswith(("http", "data:")):
            photo = data_uri(photo)
        inner = ill_property(items, photo)
    else:
        inner = ILL[topic](items)
    return frame(inner, label)


# ───────────────────────── раскладки ─────────────────────────
def fit(text, sizes, width):
    """Кегль по длине заголовка, но так, чтобы самое длинное слово влезло в ширину."""
    n = len(text or "")
    px = sizes[-1][1]
    for limit, size in sizes:
        if n <= limit:
            px = size
            break
    longest = max((len(w) for w in (text or "").split()), default=1)
    return int(min(px, width / (longest * 0.78 + 0.3)))


def subtitle_html(d, px):
    sub = d.get("subtitle") or []
    if isinstance(sub, str):
        sub = [sub]
    return "".join(f'<div style="font-family:Manrope;font-size:{px}px;line-height:1.35;color:{CREAM}">{esc(s)}</div>' for s in sub[:3])


def takeaway_html(d, px):
    t = d.get("takeaway")
    if not t:
        return ""
    return (f'<div style="border-left:4px solid {GOLD};padding:6px 0 6px 22px;display:flex;flex-direction:column;gap:8px">'
            f'<div class="k" style="font-size:{int(px*.55)}px;color:{GOLD}">Что это меняет</div>'
            f'<div style="font-family:Manrope;font-size:{px}px;line-height:1.35;color:{CREAM}">{esc(t)}</div></div>')


def logo_html(h):
    return f'<img src="{data_uri(LOGO)}" style="height:{h}px;display:block">'


def tall(d):
    W, H = 1080, 1350
    t = (d.get("title") or "").upper()
    ts = fit(t, [(14, 104), (24, 88), (40, 72), (60, 60), (999, 50)], 952)
    return W, H, f"""
<div style="width:{W}px;height:{H}px;background:{NAVY};color:{CREAM};padding:64px 64px 56px;display:flex;flex-direction:column;gap:36px">
 <div style="display:flex;justify-content:space-between;align-items:center">
  <div class="k" style="font-size:22px;color:{MUTED}">{esc(d.get('kicker') or 'Аланья · Турция')} <span style="color:{GOLD}">·</span> {esc(d.get('date'))}</div>
  {logo_html(56)}
 </div>
 <div style="height:560px;flex-shrink:0">{illustration(d)}</div>
 <div style="display:flex;flex-direction:column;gap:22px">
  <h1 style="margin:0;font-family:Playfair;font-weight:600;font-size:{ts}px;line-height:1.02;letter-spacing:3px;color:{CREAM}">{esc(t)}</h1>
  <div style="width:260px;height:4px;background:{GOLD}"></div>
  {subtitle_html(d, 30)}
  {takeaway_html(d, 28)}
 </div>
 <div style="margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;gap:24px">
  <div class="k" style="font-size:16px;line-height:1.5;color:{MUTED};letter-spacing:2px">{esc(d.get('footnote'))}</div>
  <div class="k" style="font-size:20px;color:{GOLD};white-space:nowrap;letter-spacing:2px">{CHANNEL}</div>
 </div>
</div>"""


def wide(d):
    W, H = 1280, 720
    t = (d.get("title") or "").upper()
    ts = fit(t, [(14, 84), (24, 70), (40, 56), (60, 46), (999, 40)], 530)
    return W, H, f"""
<div style="width:{W}px;height:{H}px;background:{NAVY};color:{CREAM};padding:56px 64px;display:flex;gap:56px">
 <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:22px">
  <div style="display:flex;align-items:center;gap:18px">{logo_html(40)}
   <div class="k" style="font-size:17px;color:{MUTED}">{esc(d.get('kicker') or 'Аланья · Турция')} <span style="color:{GOLD}">·</span> {esc(d.get('date'))}</div></div>
  <h1 style="margin:28px 0 0;font-family:Playfair;font-weight:600;font-size:{ts}px;line-height:1.04;letter-spacing:3px">{esc(t)}</h1>
  <div style="width:220px;height:4px;background:{GOLD}"></div>
  {subtitle_html(d, 24)}
  {takeaway_html(d, 22)}
  <div style="margin-top:auto;display:flex;flex-direction:column;gap:8px">
   <div class="k" style="font-size:13px;line-height:1.5;color:{MUTED};letter-spacing:2px">{esc(d.get('footnote'))}</div>
   <div class="k" style="font-size:16px;color:{GOLD};letter-spacing:2px">{CHANNEL}</div>
  </div>
 </div>
 <div style="width:560px;height:608px;flex-shrink:0;display:flex;align-items:center"><div style="width:560px;height:560px">{illustration(d)}</div></div>
</div>"""


def shoot(page, html_body, W, H, out):
    doc = f"<!doctype html><html lang='ru'><head><meta charset='utf-8'><style>{css()}</style></head><body>{html_body}</body></html>"
    tmp = pathlib.Path(out).with_suffix(".html")
    tmp.write_text(doc, encoding="utf-8")
    page.set_viewport_size({"width": W, "height": H})
    page.goto(tmp.resolve().as_uri())
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(250)
    over = page.evaluate("""[document.documentElement.scrollHeight, document.documentElement.scrollWidth,
        [...document.querySelectorAll('h1')].some(e => e.scrollWidth > e.clientWidth + 8)]""")
    page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": W, "height": H})
    tmp.unlink()
    return over[0] > H + 2 or over[1] > W + 2 or over[2]


def render(d, out_dir, name):
    out_dir = pathlib.Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    bad = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        for fmt, fn in (("tall", tall), ("wide", wide)):
            W, H, body = fn(d)
            out = out_dir / f"{name}-{fmt}.png"
            if shoot(pg, body, W, H, out):
                bad.append(fmt)
            print(out)
        b.close()
    if bad:
        print(f"ВНИМАНИЕ: текст не влез в {bad} — сократите заголовок или подзаголовок", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2:
        raise SystemExit(__doc__)
    name = pathlib.Path(args[0]).stem
    if "--name" in args:
        name = args[args.index("--name") + 1]
    sys.exit(render(json.loads(pathlib.Path(args[0]).read_text(encoding="utf-8")), args[1], name))
