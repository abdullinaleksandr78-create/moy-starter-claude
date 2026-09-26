# Карточки постов «Лилия Спика · Турция»

Автоматическая картинка 1080×1350 (4:5) под пост в Instagram и Threads.
Стиль выбирается по типу поста:

| type | Стиль | Когда |
|---|---|---|
| `news` | Досье | новости: ВНЖ, гражданство, закрытые кварталы, проверки, курс, налоги |
| `life` | Море | сезон и быт: зимовка, 90/180, тарифы, афиша, стоимость жизни |
| `object` | Арка | обзор или показ квартиры, разбор объекта |

## Запуск

```bash
pip install playwright --break-system-packages   # если нет
python3 render.py card.json out.png
```

Код выхода 2 = текст не влез, сократите заголовок.

## Поля

Общие: `type`, `title`, `date` (ДД.ММ.ГГГГ), `channel` (@канал), `tag` (необязательно, своя плашка).

- `news`: `takeaway` — «что это меняет для клиента», одна фраза; `source` — «Кто · дата».
- `life`: `label` (напр. «Пятница»), `stats` — 0–2 шт. `{value, label}`, `body`, `note` (дата проверки).
- `object`: `location`, `price`, `photo` (URL или путь к файлу; нет — в арке будет название района),
  `facts` — до 4 шт. `{label, value, good}`, `body`.

Примеры — в `examples/`.

## Публикация

Готовые PNG лежат в ветке `cards`, папка `turkey-cards/posts/`, и доступны по ссылке
`https://raw.githubusercontent.com/abdullinaleksandr78-create/moy-starter-claude/cards/turkey-cards/posts/<файл>.png` —
эту ссылку принимает Metricool.

Шрифты — Google Fonts, лицензия OFL.
