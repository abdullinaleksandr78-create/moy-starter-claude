"""Макеты карточек по рубрикам: cities, steps, qa, checklist, photo, portrait.

Подключаются из render.py по полю "layout". Классический макет (иллюстрация по topic)
остаётся в render.py и включается, если layout не указан или равен "classic".

Тема — поле "theme": "dark" (тёмно-синий, по умолчанию) или "light" (молочный).
Фото — поле "photo": путь к файлу, URL или имя города ("alanya", "antalya", "istanbul", "any"):
тогда снимок берётся из photos/<город>/ по очереди, чтобы не повторяться день в день.
"""
import hashlib, html, pathlib, base64, mimetypes

HERE = pathlib.Path(__file__).resolve().parent
PHOTOS = HERE / "photos"
LOGO = HERE / "assets" / "logo-gold.png"
CHANNEL = "@prostranstvo_alanya"

THEMES = {
    "dark": dict(bg="#0E1A2B", panel="#13233A", line="#2C4058", gold="#D9A441", ink="#EDE6D6", muted="#8FA0B3", soft="#1A2D47"),
    "light": dict(bg="#F3EEE3", panel="#E9E1D0", line="#D3C6AC", gold="#B07D24", ink="#0E1A2B", muted="#5E6B7B", soft="#E6DCC6"),
}
CITY_RU = {"alanya": "Алания", "antalya": "Анталья", "istanbul": "Стамбул"}


def esc(s):
    return html.escape(str(s or ""))


def data_uri(path):
    p = pathlib.Path(path)
    mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def pal(d):
    return THEMES.get(d.get("theme") or "dark", THEMES["dark"])


def pick_photo(spec, seed=""):
    """Путь/URL как есть; имя города — фото из photos/<город>/ по очереди (детерминированно по seed)."""
    if not spec:
        return None
    s = str(spec)
    if s.startswith(("http://", "https://", "data:")):
        return s
    key = s.lower()
    if key in CITY_RU or key == "any":
        dirs = [PHOTOS / key] if key != "any" else [PHOTOS / c for c in CITY_RU]
        files = sorted(f for dd in dirs if dd.is_dir() for f in dd.glob("*.jpg"))
        if not files:
            return None
        i = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(files)
        return data_uri(files[i])
    p = pathlib.Path(s)
    if not p.is_absolute():
        p = HERE / p
    return data_uri(p) if p.exists() else None


def logo(h):
    return f'<img src="{data_uri(LOGO)}" style="height:{h}px;display:block">'


def head(d, c, size=22, logo_h=56):
    return (f'<div style="display:flex;justify-content:space-between;align-items:center;gap:24px">'
            f'<div class="k" style="font-size:{size}px;color:{c["muted"]}">{esc(d.get("kicker"))} '
            f'<span style="color:{c["gold"]}">·</span> {esc(d.get("date"))}</div>{logo(logo_h)}</div>')


def foot(d, c, size=16):
    return (f'<div style="margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;gap:24px">'
            f'<div class="k" style="font-size:{size}px;line-height:1.5;color:{c["muted"]};letter-spacing:2px">{esc(d.get("footnote"))}</div>'
            f'<div class="k" style="font-size:{size+4}px;color:{c["gold"]};white-space:nowrap;letter-spacing:2px">{CHANNEL}</div></div>')


def title(d, c, px, upper=True, mt=0):
    t = d.get("title") or ""
    t = t.upper() if upper else t
    return (f'<h1 style="margin:{mt}px 0 0;font-family:Playfair;font-weight:600;font-size:{px}px;line-height:1.05;'
            f'letter-spacing:{3 if upper else 0}px;color:{c["ink"]}">{esc(t)}</h1>')


def rule(c, w=220):
    return f'<div style="width:{w}px;height:4px;background:{c["gold"]};flex-shrink:0"></div>'


def takeaway(d, c, px):
    t = d.get("takeaway")
    if not t:
        return ""
    return (f'<div style="border-left:4px solid {c["gold"]};padding:4px 0 4px 22px;display:flex;flex-direction:column;gap:8px">'
            f'<div class="k" style="font-size:{int(px*.55)}px;color:{c["gold"]}">Что это даёт</div>'
            f'<div style="font-family:Manrope;font-size:{px}px;line-height:1.35;color:{c["ink"]}">{esc(t)}</div></div>')


def tsize(text, big, width):
    n = len(text or "")
    px = big if n <= 18 else big * .86 if n <= 28 else big * .74 if n <= 40 else big * .62
    longest = max((len(w) for w in (text or "").split()), default=1)
    return int(min(px, width / (longest * 0.78 + 0.3)))


def page(W, H, c, body, pad="64px 64px 56px", gap=34, extra=""):
    return W, H, (f'<div style="width:{W}px;height:{H}px;background:{c["bg"]};color:{c["ink"]};padding:{pad};'
                  f'display:flex;flex-direction:column;gap:{gap}px;position:relative;overflow:hidden">{extra}{body}</div>')


# ───────────────────────── «Три города» ─────────────────────────
def _cities(d):
    rows = d.get("cities") or []
    out = []
    for i, r in enumerate(rows[:3]):
        key = (r.get("photo") or r.get("key") or "").lower()
        if not key:
            key = {v: k for k, v in CITY_RU.items()}.get(r.get("name", ""), "")
        out.append(dict(name=r.get("name") or CITY_RU.get(key, ""), value=r.get("value", ""), note=r.get("note", ""),
                        photo=pick_photo(key or r.get("photo"), d.get("date", "") + str(i) + (d.get("title") or ""))))
    return out


def _arch(photo, c, w, h):
    r = w / 2
    shape = f'border-radius:{r}px {r}px 0 0'
    if photo:
        return (f'<div style="width:{w}px;height:{h}px;{shape};overflow:hidden;border:3px solid {c["gold"]};flex-shrink:0">'
                f'<img src="{photo}" style="width:100%;height:100%;object-fit:cover;display:block"></div>')
    return f'<div style="width:{w}px;height:{h}px;{shape};border:3px solid {c["gold"]};background:{c["soft"]};flex-shrink:0"></div>'


def cities_tall(d):
    c, W, H = pal(d), 1080, 1350
    cols = "".join(
        f'<div style="flex:1;min-width:0;display:flex;flex-direction:column;align-items:center;gap:16px;text-align:center">'
        f'{_arch(x["photo"], c, 290, 470)}'
        f'<div class="k" style="font-size:20px;color:{c["gold"]}">{esc(x["name"])}</div>'
        f'<div style="font-family:Playfair;font-weight:600;font-size:{64 if len(str(x["value"])) <= 9 else 50}px;line-height:1;color:{c["ink"]}">{esc(x["value"])}</div>'
        f'<div style="font-family:Manrope;font-size:22px;line-height:1.3;color:{c["muted"]}">{esc(x["note"])}</div></div>'
        for x in _cities(d))
    t = (d.get("title") or "").upper()
    body = (head(d, c) + f'<div style="display:flex;flex-direction:column;gap:18px">{title(d, c, tsize(t, 76, 952))}{rule(c)}</div>'
            f'<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:40px"><div style="display:flex;gap:28px;align-items:flex-start">{cols}</div>{takeaway(d, c, 29)}</div>' + foot(d, c))
    return page(W, H, c, body)


def cities_wide(d):
    c, W, H = pal(d), 1280, 720
    cols = "".join(
        f'<div style="flex:1;min-width:0;display:flex;flex-direction:column;align-items:center;gap:10px;text-align:center">'
        f'{_arch(x["photo"], c, 200, 300)}'
        f'<div class="k" style="font-size:15px;color:{c["gold"]}">{esc(x["name"])}</div>'
        f'<div style="font-family:Playfair;font-weight:600;font-size:{40 if len(str(x["value"])) <= 9 else 32}px;line-height:1;color:{c["ink"]}">{esc(x["value"])}</div>'
        f'<div style="font-family:Manrope;font-size:16px;line-height:1.3;color:{c["muted"]}">{esc(x["note"])}</div></div>'
        for x in _cities(d))
    t = (d.get("title") or "").upper()
    left = (f'<div style="width:430px;flex-shrink:0;display:flex;flex-direction:column;gap:20px">'
            f'<div style="display:flex;align-items:center;gap:16px">{logo(40)}<div class="k" style="font-size:15px;color:{c["muted"]}">{esc(d.get("kicker"))} · {esc(d.get("date"))}</div></div>'
            f'{title(d, c, tsize(t, 56, 430), mt=18)}{rule(c, 180)}{takeaway(d, c, 20)}'
            f'<div style="margin-top:auto" class="k"><div style="font-size:12px;line-height:1.5;color:{c["muted"]};letter-spacing:2px">{esc(d.get("footnote"))}</div>'
            f'<div style="font-size:15px;color:{c["gold"]};letter-spacing:2px;margin-top:8px">{CHANNEL}</div></div></div>')
    return W, H, (f'<div style="width:{W}px;height:{H}px;background:{c["bg"]};color:{c["ink"]};padding:52px 56px;display:flex;gap:44px">'
                  f'{left}<div style="flex:1;display:flex;gap:20px;align-items:flex-start;padding-top:40px">{cols}</div></div>')


# ───────────────────────── «Как это устроено»: шаги ─────────────────────────
def _steps(d):
    out = []
    for s in (d.get("steps") or [])[:5]:
        out.append((s, "") if isinstance(s, str) else (s.get("t", ""), s.get("d", "")))
    return out


def steps_block(d, c, num, tp, dp, gap):
    st = _steps(d)
    rows = ""
    for i, (t, dd) in enumerate(st):
        last = i == len(st) - 1
        line = "" if last else f'<div style="position:absolute;left:{num/2-1.5}px;top:{num}px;bottom:-{gap}px;width:3px;background:{c["gold"]};opacity:.5"></div>'
        rows += (f'<div style="position:relative;display:flex;gap:26px;align-items:flex-start">{line}'
                 f'<div style="width:{num}px;height:{num}px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;'
                 f'font-family:Mono;font-weight:500;font-size:{int(num*.36)}px;'
                 f'{"background:" + c["gold"] + ";color:" + c["bg"] if last else "border:3px solid " + c["gold"] + ";color:" + c["gold"]}">{i+1:02d}</div>'
                 f'<div style="display:flex;flex-direction:column;gap:6px;padding-top:{int(num*.12)}px">'
                 f'<div style="font-family:Manrope;font-weight:700;font-size:{tp}px;line-height:1.2;color:{c["ink"]}">{esc(t)}</div>'
                 + (f'<div style="font-family:Manrope;font-size:{dp}px;line-height:1.35;color:{c["muted"]}">{esc(dd)}</div>' if dd else "")
                 + '</div></div>')
    return f'<div style="display:flex;flex-direction:column;gap:{gap}px">{rows}</div>'


def steps_tall(d):
    c, W, H = pal(d), 1080, 1350
    t = (d.get("title") or "").upper()
    body = (head(d, c) + f'<div style="display:flex;flex-direction:column;gap:18px">{title(d, c, tsize(t, 80, 952), mt=6)}{rule(c)}</div>'
            + f'<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:44px">{steps_block(d, c, 96, 42, 29, 46)}{takeaway(d, c, 30)}</div>' + foot(d, c))
    return page(W, H, c, body)


def steps_wide(d):
    c, W, H = pal(d), 1280, 720
    t = (d.get("title") or "").upper()
    left = (f'<div style="width:470px;flex-shrink:0;display:flex;flex-direction:column;gap:20px">'
            f'<div style="display:flex;align-items:center;gap:16px">{logo(40)}<div class="k" style="font-size:15px;color:{c["muted"]}">{esc(d.get("kicker"))} · {esc(d.get("date"))}</div></div>'
            f'{title(d, c, tsize(t, 58, 470), mt=18)}{rule(c, 180)}{takeaway(d, c, 20)}'
            f'<div style="margin-top:auto" class="k"><div style="font-size:12px;line-height:1.5;color:{c["muted"]};letter-spacing:2px">{esc(d.get("footnote"))}</div>'
            f'<div style="font-size:15px;color:{c["gold"]};letter-spacing:2px;margin-top:8px">{CHANNEL}</div></div></div>')
    return W, H, (f'<div style="width:{W}px;height:{H}px;background:{c["bg"]};color:{c["ink"]};padding:52px 56px;display:flex;gap:56px">'
                  f'{left}<div style="flex:1;display:flex;align-items:center">{steps_block(d, c, 56, 24, 17, 22)}</div></div>')


# ───────────────────────── «Чек-лист» ─────────────────────────
def check_block(d, c, box, px, gap):
    rows = ""
    tick = (f'<svg viewBox="0 0 24 24" width="{int(box*.66)}" height="{int(box*.66)}"><path d="M4 12.5 L10 18 L20 6" fill="none" '
            f'stroke="{c["bg"]}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    for it in (d.get("checklist") or [])[:6]:
        rows += (f'<div style="display:flex;gap:24px;align-items:flex-start">'
                 f'<div style="width:{box}px;height:{box}px;flex-shrink:0;background:{c["gold"]};border-radius:6px;display:flex;align-items:center;justify-content:center">{tick}</div>'
                 f'<div style="font-family:Manrope;font-weight:600;font-size:{px}px;line-height:1.3;color:{c["ink"]};padding-top:{max(0,(box-px*1.3)/2):.0f}px">{esc(it)}</div></div>'
                 f'<div style="height:1px;background:{c["line"]};margin-left:{box+24}px"></div>')
    return f'<div style="display:flex;flex-direction:column;gap:{gap}px">{rows}</div>'


def checklist_tall(d):
    c, W, H = pal(d), 1080, 1350
    t = (d.get("title") or "").upper()
    body = (head(d, c) + f'<div style="display:flex;flex-direction:column;gap:18px">{title(d, c, tsize(t, 80, 952), mt=6)}{rule(c)}</div>'
            + f'<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:44px">{check_block(d, c, 66, 38, 30)}{takeaway(d, c, 30)}</div>' + foot(d, c))
    return page(W, H, c, body)


def checklist_wide(d):
    c, W, H = pal(d), 1280, 720
    t = (d.get("title") or "").upper()
    left = (f'<div style="width:440px;flex-shrink:0;display:flex;flex-direction:column;gap:20px">'
            f'<div style="display:flex;align-items:center;gap:16px">{logo(40)}<div class="k" style="font-size:15px;color:{c["muted"]}">{esc(d.get("kicker"))} · {esc(d.get("date"))}</div></div>'
            f'{title(d, c, tsize(t, 58, 440), mt=18)}{rule(c, 180)}'
            f'<div style="margin-top:auto" class="k"><div style="font-size:12px;line-height:1.5;color:{c["muted"]};letter-spacing:2px">{esc(d.get("footnote"))}</div>'
            f'<div style="font-size:15px;color:{c["gold"]};letter-spacing:2px;margin-top:8px">{CHANNEL}</div></div></div>')
    return W, H, (f'<div style="width:{W}px;height:{H}px;background:{c["bg"]};color:{c["ink"]};padding:52px 56px;display:flex;gap:56px">'
                  f'{left}<div style="flex:1;display:flex;align-items:center">{check_block(d, c, 36, 21, 12)}</div></div>')


# ───────────────────────── «Вопрос — ответ» (+ фото Лилии) ─────────────────────────
def _expert(d, c, size, name_px):
    ph = pick_photo(d.get("portrait"), "") if d.get("portrait") else None
    if not ph:
        return ""
    return (f'<div style="display:flex;align-items:center;gap:20px">'
            f'<div style="width:{size}px;height:{size}px;border-radius:50%;overflow:hidden;border:3px solid {c["gold"]};flex-shrink:0">'
            f'<img src="{ph}" style="width:100%;height:100%;object-fit:cover;object-position:50% 25%;display:block"></div>'
            f'<div style="display:flex;flex-direction:column;gap:4px"><div class="k" style="font-size:{int(name_px*.7)}px;color:{c["gold"]}">Отвечает</div>'
            f'<div style="font-family:Manrope;font-weight:700;font-size:{name_px}px;color:{c["ink"]}">{esc(d.get("expert") or "Лилия Спика")}</div></div></div>')


def qa_tall(d):
    c, W, H = pal(d), 1080, 1350
    q = d.get("question") or d.get("title") or ""
    qpx = tsize(q, 88, 952) if len(q) < 70 else 62
    mark = (f'<div style="position:absolute;right:40px;top:120px;font-family:Playfair;font-weight:700;font-size:520px;line-height:1;'
            f'color:{c["gold"]};opacity:.13">?</div>')
    ex = _expert(d, c, 150, 34)
    body = (head(d, c) + ('' if ex else '<div style="flex:.6"></div>') + f'<div class="k" style="font-size:22px;color:{c["gold"]};margin-top:30px">Вопрос</div>'
            f'<div style="font-family:Playfair;font-weight:600;font-size:{qpx}px;line-height:1.12;color:{c["ink"]};max-width:930px;position:relative">{esc(q)}</div>'
            + rule(c) +
            f'<div style="display:flex;flex-direction:column;gap:14px;position:relative"><div class="k" style="font-size:22px;color:{c["gold"]}">Коротко</div>'
            f'<div style="font-family:Manrope;font-size:40px;line-height:1.4;color:{c["ink"]}">{esc(d.get("answer"))}</div></div>'
            + '<div style="flex:1"></div>' + ex + foot(d, c).replace('margin-top:auto', 'margin-top:0'))
    return page(W, H, c, body, extra=mark)


def qa_wide(d):
    c, W, H = pal(d), 1280, 720
    q = d.get("question") or d.get("title") or ""
    mark = (f'<div style="position:absolute;right:30px;top:-40px;font-family:Playfair;font-weight:700;font-size:420px;line-height:1;'
            f'color:{c["gold"]};opacity:.12">?</div>')
    body = (f'<div style="display:flex;align-items:center;gap:16px">{logo(40)}<div class="k" style="font-size:15px;color:{c["muted"]}">{esc(d.get("kicker"))} · {esc(d.get("date"))}</div></div>'
            f'<div style="font-family:Playfair;font-weight:600;font-size:{min(56, tsize(q, 56, 1050)) if len(q) < 70 else 42}px;line-height:1.12;color:{c["ink"]};max-width:1000px;position:relative;margin-top:10px">{esc(q)}</div>'
            + rule(c, 180) +
            f'<div style="font-family:Manrope;font-size:29px;line-height:1.4;color:{c["ink"]};max-width:1050px;position:relative">{esc(d.get("answer"))}</div>'
            + f'<div style="margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;gap:24px">{_expert(d, c, 76, 20) or "<div></div>"}'
            f'<div class="k" style="text-align:right"><div style="font-size:12px;line-height:1.5;color:{c["muted"]};letter-spacing:2px">{esc(d.get("footnote"))}</div>'
            f'<div style="font-size:15px;color:{c["gold"]};letter-spacing:2px;margin-top:6px">{CHANNEL}</div></div></div>')
    return page(W, H, c, body, pad="52px 60px", gap=22, extra=mark)


# ───────────────────────── «Фото»: снимок города на весь фон ─────────────────────────
def _photo_bg(d, W, H, c):
    ph = pick_photo(d.get("photo") or "any", d.get("date", "") + (d.get("title") or ""))
    img = f'<img src="{ph}" style="position:absolute;inset:0;width:{W}px;height:{H}px;object-fit:cover">' if ph else ""
    shade = (f'<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(14,26,43,.45) 0%,rgba(14,26,43,0) 22%,rgba(14,26,43,0) 40%,'
             f'rgba(14,26,43,.82) 62%,rgba(14,26,43,.97) 100%)"></div>')
    return img + shade


def photo_tall(d):
    c, W, H = THEMES["dark"], 1080, 1350
    t = (d.get("title") or "").upper()
    sub = d.get("subtitle") or []
    sub = [sub] if isinstance(sub, str) else sub
    subs = "".join(f'<div style="font-family:Manrope;font-size:30px;line-height:1.35;color:{c["ink"]}">{esc(s)}</div>' for s in sub[:3])
    body = (f'<div style="position:relative;display:flex;flex-direction:column;gap:22px;height:100%">' + head(d, c) +
            f'<div style="margin-top:auto"></div>{title(d, c, tsize(t, 96, 952))}{rule(c, 260)}{subs}{takeaway(d, c, 28)}'
            + foot(d, c).replace("margin-top:auto", "margin-top:18px") + '</div>')
    return page(W, H, c, body, extra=_photo_bg(d, W, H, c))


def photo_wide(d):
    c, W, H = THEMES["dark"], 1280, 720
    t = (d.get("title") or "").upper()
    shade = ('<div style="position:absolute;inset:0;background:linear-gradient(90deg,rgba(14,26,43,.97) 0%,rgba(14,26,43,.88) 42%,'
             'rgba(14,26,43,.25) 75%,rgba(14,26,43,.05) 100%)"></div>')
    ph = pick_photo(d.get("photo") or "any", d.get("date", "") + (d.get("title") or ""))
    img = f'<img src="{ph}" style="position:absolute;inset:0;width:{W}px;height:{H}px;object-fit:cover">' if ph else ""
    sub = d.get("subtitle") or []
    sub = [sub] if isinstance(sub, str) else sub
    subs = "".join(f'<div style="font-family:Manrope;font-size:23px;line-height:1.35;color:{c["ink"]}">{esc(s)}</div>' for s in sub[:2])
    body = (f'<div style="position:relative;width:620px;display:flex;flex-direction:column;gap:18px;height:100%">'
            f'<div style="display:flex;align-items:center;gap:16px">{logo(40)}<div class="k" style="font-size:15px;color:{c["muted"]}">{esc(d.get("kicker"))} · {esc(d.get("date"))}</div></div>'
            f'{title(d, c, tsize(t, 62, 620), mt=24)}{rule(c, 200)}{subs}{takeaway(d, c, 21)}'
            f'<div style="margin-top:auto" class="k"><div style="font-size:12px;line-height:1.5;color:{c["muted"]};letter-spacing:2px">{esc(d.get("footnote"))}</div>'
            f'<div style="font-size:15px;color:{c["gold"]};letter-spacing:2px;margin-top:8px">{CHANNEL}</div></div></div>')
    return page(W, H, c, body, pad="52px 60px", extra=img + shade)


# ───────────────────────── слайды карусели ─────────────────────────
def slide_tall(d, s, i, n):
    """Внутренний слайд карусели: крупный номер, заголовок слайда, текст."""
    c, W, H = pal(d), 1080, 1350
    ph = pick_photo(s.get("photo"), d.get("date", "") + str(i)) if s.get("photo") else None
    pic = (f'<div style="flex:1;min-height:300px;border-radius:240px 240px 0 0;overflow:hidden;border:3px solid {c["gold"]};flex-shrink:0">'
           f'<img src="{ph}" style="width:100%;height:100%;object-fit:cover;display:block"></div>') if ph else ""
    body = (head(d, c) +
            f'<div style="font-family:Playfair;font-weight:700;font-size:150px;line-height:.9;color:{c["gold"]};margin-top:10px">{i:02d}</div>'
            f'<div style="font-family:Playfair;font-weight:600;font-size:{tsize(s.get("t",""), 68, 952)}px;line-height:1.1;color:{c["ink"]}">{esc(s.get("t"))}</div>'
            + rule(c) +
            f'<div style="font-family:Manrope;font-size:38px;line-height:1.4;color:{c["ink"]}">{esc(s.get("d"))}</div>'
            + pic +
            f'<div style="margin-top:auto;display:flex;justify-content:space-between;align-items:center">'
            f'<div class="k" style="font-size:18px;color:{c["muted"]}">{i} / {n}</div>'
            f'<div class="k" style="font-size:20px;color:{c["gold"]};letter-spacing:2px">{"Листайте →" if i < n else CHANNEL}</div></div>')
    return page(W, H, c, body)


LAYOUTS = {
    "cities": (cities_tall, cities_wide),
    "steps": (steps_tall, steps_wide),
    "checklist": (checklist_tall, checklist_wide),
    "qa": (qa_tall, qa_wide),
    "photo": (photo_tall, photo_wide),
}
