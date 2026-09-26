#!/usr/bin/env python3
"""Карточки для постов канала «Лилия Спика · Турция».

Использование:
    python3 render.py card.json out.png

Три типа карточки, стиль выбирается по типу поста:
    news   -> «Досье»  (новости: статус, законы, проверки, курс)
    life   -> «Море»   (сезон и быт, зимовка, афиша, стоимость жизни)
    object -> «Арка»   (обзор / показ квартиры, разбор объекта)

Формат JSON — см. README.md и examples/.
"""
import base64, html, json, mimetypes, pathlib, sys

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
FONTS = HERE / "fonts"
W, H = 1080, 1350


def esc(s):
    return html.escape(str(s or ""))


def font_faces():
    f = FONTS.as_uri()
    return f"""
@font-face{{font-family:'PT Serif';src:url('{f}/PT_Serif-Web-Regular.ttf');font-weight:400}}
@font-face{{font-family:'PT Serif';src:url('{f}/PT_Serif-Web-Bold.ttf');font-weight:700}}
@font-face{{font-family:'Plex Mono';src:url('{f}/IBMPlexMono-Regular.ttf');font-weight:400}}
@font-face{{font-family:'Plex Mono';src:url('{f}/IBMPlexMono-Medium.ttf');font-weight:500}}
@font-face{{font-family:'Plex Mono';src:url('{f}/IBMPlexMono-SemiBold.ttf');font-weight:600}}
@font-face{{font-family:'Playfair';src:url('{f}/PlayfairDisplay-VF.ttf');font-weight:400 900}}
@font-face{{font-family:'Manrope';src:url('{f}/Manrope-VF.ttf');font-weight:200 800}}
@font-face{{font-family:'Unbounded';src:url('{f}/Unbounded-VF.ttf');font-weight:200 900}}
*{{box-sizing:border-box}} body{{margin:0}}
"""


def title_size(text, sizes):
    """sizes: [(max_chars, px), ...] по возрастанию длины."""
    n = len(text or "")
    for limit, px in sizes:
        if n <= limit:
            return px
    return sizes[-1][1]


def img_src(photo):
    if not photo:
        return ""
    if str(photo).startswith(("http://", "https://", "data:")):
        return photo
    p = pathlib.Path(photo)
    if not p.is_absolute():
        p = (pathlib.Path.cwd() / p).resolve()
    mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


# ---------------- НОВОСТЬ · «Досье» ----------------
def news(d):
    t = d.get("title", "")
    ts = title_size(t, [(40, 88), (60, 76), (85, 66), (999, 56)])
    tag = d.get("tag") or "СТАТУС · НОВОСТЬ"
    takeaway = d.get("takeaway", "")
    src = d.get("source", "")
    return f"""
<div style="width:{W}px;height:{H}px;background:#F7EFE4;color:#2B1D16;font-family:'Plex Mono';display:flex;flex-direction:column">
 <div style="height:20px;background:#E0A43A"></div>
 <div style="flex-grow:1;padding:40px 48px 48px;display:flex">
  <div style="flex-grow:1;border:3px solid #2B1D16;padding:64px 64px 48px;display:flex;flex-direction:column;gap:36px">
   <div style="display:flex;justify-content:space-between;align-items:center;font-size:24px;font-weight:500;letter-spacing:2px">
    <div style="padding:10px 20px;background:#B5532E;color:#fff">{esc(tag.upper())}</div>
    <div>{esc(d.get('date'))}</div>
   </div>
   <div style="height:3px;background:#2B1D16"></div>
   <h1 style="margin:0;font-family:'PT Serif';font-size:{ts}px;line-height:1.08;font-weight:700">{esc(t)}</h1>
   {f'''<div style="display:flex;flex-direction:column;gap:16px;padding:28px 32px;background:#fff;border:2px solid #2B1D16">
    <div style="font-size:22px;font-weight:600;letter-spacing:2px;color:#0E5E78">ЧТО ЭТО МЕНЯЕТ ДЛЯ КЛИЕНТА</div>
    <p style="margin:0;font-family:'PT Serif';font-size:{36 if len(takeaway) < 140 else 30}px;line-height:1.35">{esc(takeaway)}</p>
   </div>''' if takeaway else ''}
   <div style="margin-top:auto;font-size:22px;line-height:1.4;color:#6E5A4C">{('ИСТОЧНИК: ' + esc(src)) if src else ''}</div>
   <div style="height:3px;background:#2B1D16"></div>
   <div style="display:flex;justify-content:space-between;font-size:24px;font-weight:500;letter-spacing:2px">
    <div>ЛИЛИЯ СПИКА / ТУРЦИЯ</div><div>{esc(d.get('channel'))}</div>
   </div>
  </div>
 </div>
</div>"""


# ---------------- СЕЗОН И БЫТ · «Море» ----------------
def life(d):
    t = d.get("title", "")
    ts = title_size(t, [(35, 92), (55, 80), (80, 68), (999, 58)])
    stats = (d.get("stats") or [])[:2]
    cards = "".join(
        f"""<div style="padding:36px;border-radius:28px;background:#fff;display:flex;flex-direction:column;gap:8px">
        <div style="font-family:'Playfair';font-size:{96 if len(str(s.get('value',''))) <= 6 else 64}px;font-weight:700;color:#0E5E78;line-height:1.05">{esc(s.get('value'))}</div>
        <div style="font-size:30px;line-height:1.3">{esc(s.get('label'))}</div></div>"""
        for s in stats)
    grid = (f'<div style="display:grid;grid-template-columns:repeat({len(stats)},minmax(0,1fr));gap:24px">{cards}</div>'
            if stats else "")
    body = d.get("body", "")
    date_line = " · ".join(x for x in [d.get("label"), d.get("date")] if x)
    return f"""
<div style="width:{W}px;height:{H}px;background:#F4EFE6;color:#10233A;font-family:'Manrope';display:flex;flex-direction:column">
 <div style="height:22px;background:#E0A43A"></div>
 <svg width="1080" height="40" viewBox="0 0 1080 40" style="display:block"><path d="M0 0 H1080 V14 C990 34 900 34 810 14 C720 -6 630 -6 540 14 C450 34 360 34 270 14 C180 -6 90 -6 0 14 Z" fill="#E0A43A"/></svg>
 <div style="flex-grow:1;padding:56px 88px 0;display:flex;flex-direction:column;gap:40px">
  <div style="display:flex;justify-content:space-between;align-items:center">
   <div style="padding:14px 28px;border-radius:999px;background:#E0A43A;font-size:26px;font-weight:700;letter-spacing:3px">{esc((d.get('tag') or 'СЕЗОН И БЫТ').upper())}</div>
   <div style="font-size:26px;font-weight:500;color:#4A5A6B">{esc(date_line)}</div>
  </div>
  <h1 style="margin:0;font-family:'Playfair';font-size:{ts}px;line-height:1.05;font-weight:700">{esc(t)}</h1>
  {grid}
  {f'<p style="margin:0;font-size:{36 if len(body) < 120 else 30}px;line-height:1.4">{esc(body)}</p>' if body else ''}
  <div style="margin-top:auto;padding-bottom:40px;font-size:24px;color:#4A5A6B">{esc(d.get('note'))}</div>
 </div>
 <div style="height:132px;padding:0 88px;background:#10233A;color:#F4EFE6;display:flex;align-items:center;justify-content:space-between">
  <div style="display:flex;flex-direction:column;gap:4px">
   <div style="font-family:'Playfair';font-size:38px;font-weight:600">Лилия Спика</div>
   <div style="font-size:22px;letter-spacing:3px;color:#9FB6C8">НЕДВИЖИМОСТЬ · ВНЖ · ГРАЖДАНСТВО</div>
  </div>
  <div style="font-size:28px;font-weight:500">{esc(d.get('channel'))}</div>
 </div>
</div>"""


# ---------------- ОБЗОР ОБЪЕКТА · «Арка» ----------------
def obj(d):
    t = d.get("title", "")
    ts = title_size(t, [(22, 58), (40, 50), (60, 42), (999, 36)])
    src = img_src(d.get("photo"))
    arch_inner = (f'<img src="{esc(src)}" style="width:100%;height:100%;object-fit:cover;display:block">' if src else
                  f'<div style="width:100%;height:100%;background:repeating-linear-gradient(135deg,#E3CDB6 0 18px,#EEDDCB 18px 36px);display:flex;align-items:center;justify-content:center;font-family:Unbounded;font-size:34px;font-weight:700;color:#8C3B2A;text-align:center;padding:40px">{esc(d.get("location") or "")}</div>')
    facts = (d.get("facts") or [])[:4]
    fact_html = "".join(
        f"""<div style="padding:22px;border-radius:24px;background:#fff;display:flex;flex-direction:column;gap:6px">
        <div style="font-size:20px;color:#6E5A4C">{esc(f.get('label'))}</div>
        <div style="font-size:{30 if len(str(f.get('value',''))) <= 10 else 24}px;font-weight:700{';color:#5B6B3A' if f.get('good') else ''}">{esc(f.get('value'))}</div></div>"""
        for f in facts)
    cols = max(len(facts), 1)
    return f"""
<div style="width:{W}px;height:{H}px;background:#F7EFE4;color:#2B1D16;font-family:'Manrope';padding:56px 56px 0;display:flex;flex-direction:column;gap:32px">
 <div style="display:flex;gap:40px;align-items:flex-end">
  <div style="width:520px;height:700px;flex-shrink:0;border-radius:260px 260px 0 0;border:10px solid #B5532E;overflow:hidden">{arch_inner}</div>
  <div style="flex-grow:1;display:flex;flex-direction:column;gap:24px;padding-bottom:8px">
   <div style="align-self:flex-start;padding:12px 24px;border-radius:999px;background:#B5532E;color:#fff;font-size:22px;font-weight:700;letter-spacing:3px">{esc((d.get('tag') or 'ОБЗОР ОБЪЕКТА').upper())}</div>
   <div style="font-size:24px;font-weight:700;letter-spacing:2px;color:#6E5A4C">{esc((d.get('location') or '').upper())}</div>
   <h1 style="margin:0;font-family:'Unbounded';font-size:{ts}px;line-height:1.1;font-weight:700">{esc(t)}</h1>
   {f'<div style="font-family:Unbounded;font-size:44px;font-weight:500;color:#B5532E">{esc(d.get("price"))}</div>' if d.get('price') else ''}
  </div>
 </div>
 {f'<div style="display:grid;grid-template-columns:repeat({cols},minmax(0,1fr));gap:16px">{fact_html}</div>' if facts else ''}
 {f'<div style="font-size:30px;line-height:1.4">{esc(d.get("body"))}</div>' if d.get('body') else ''}
 <div style="margin-top:auto;margin-left:-56px;margin-right:-56px;height:120px;background:#2B1D16;color:#F7EFE4;padding:0 56px;display:flex;align-items:center;justify-content:space-between">
  <div style="font-family:Unbounded;font-size:30px;font-weight:500">Лилия Спика<span style="color:#E7A580"> · Турция</span></div>
  <div style="font-size:26px;font-weight:500">{esc(d.get('channel'))}</div>
 </div>
</div>"""


BUILDERS = {"news": news, "life": life, "object": obj}


def render(data, out):
    kind = data.get("type")
    if kind not in BUILDERS:
        raise SystemExit(f"type должен быть одним из {list(BUILDERS)}, получено: {kind!r}")
    page = f"<!doctype html><html lang='ru'><head><meta charset='utf-8'><style>{font_faces()}</style></head><body>{BUILDERS[kind](data)}</body></html>"
    tmp = pathlib.Path(out).with_suffix(".html")
    tmp.write_text(page, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto(tmp.resolve().as_uri())
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        # проверка, что ничего не вылезло за карточку
        overflow = pg.evaluate("document.body.scrollHeight")
        pg.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": W, "height": H})
        b.close()
    tmp.unlink()
    if overflow > H + 2:
        print(f"ВНИМАНИЕ: текст не влез ({overflow}px > {H}px) — сократите заголовок или текст", file=sys.stderr)
        return 2
    print(out)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    sys.exit(render(json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")), sys.argv[2]))
