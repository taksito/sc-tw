#!/usr/bin/env python3
"""官方消息追蹤台：抓 RSI Comm-Link 的新文章與全文，用 Gemini 翻成繁體中文重點，並整理販售內容與相關連結。

用法：
  python scripts/news_update.py            # 檢查新文章、翻譯、寫回 data/news.json 與 data/news.js
  python scripts/news_update.py --test     # 只抓清單並翻譯最新 2 篇全文印出來，不寫檔

環境變數：
  GEMINI_API_KEY   必填（GitHub Secrets，跟 PTU 追蹤台共用）
  GEMINI_MODEL     選填
"""
import json, os, re, sys, time, html, datetime, email.utils, urllib.request, urllib.error, urllib.parse
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JSON = os.path.join(ROOT, 'data', 'news.json')
DATA_JS = os.path.join(ROOT, 'data', 'news.js')
GLOSSARY = os.path.join(ROOT, 'data', 'glossary.json')
FEED = 'https://robertsspaceindustries.com/comm-link/rss'
BASE = 'https://robertsspaceindustries.com'
MAX_ITEMS = 30
BACKFILL_PER_RUN = 8   # 每次最多補翻幾篇舊文章的全文
MAX_TEXT = 12000       # 送去翻譯的全文長度上限
SITE_SHIPS = os.path.join(ROOT, 'ships')
UA = 'Mozilla/5.0 (compatible; sc-tw-news-tracker/1.0; +https://taksito.github.io/sc-tw/)'
TZ8 = datetime.timezone(datetime.timedelta(hours=8))


def http_get(url, timeout=60):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/rss+xml, application/xml, text/xml, text/html'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'ignore')


def post_json(url, payload, headers=None, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), method='POST',
                                 headers={'Content-Type': 'application/json', 'User-Agent': UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))


def clean(s):
    s = re.sub(r'<[^>]+>', ' ', html.unescape(s or ''))
    return re.sub(r'\s+', ' ', s).strip()


def item_id(link):
    m = re.search(r'/comm-link/[^/]+/(\d+)', link)
    return m.group(1) if m else link


def parse_feed(text):
    """回傳 [{id,title,link,date,desc,image,kind}]，新到舊。支援 RSS / Atom。"""
    items = []
    root = ET.fromstring(text.strip().encode('utf-8'))
    ns = {'atom': 'http://www.w3.org/2005/Atom', 'media': 'http://search.yahoo.com/mrss/'}
    nodes = root.findall('.//item') or root.findall('.//atom:entry', ns)
    for n in nodes:
        title = clean(n.findtext('title') or n.findtext('atom:title', namespaces=ns))
        link = (n.findtext('link') or '').strip()
        if not link:
            le = n.find('atom:link', ns)
            link = le.get('href') if le is not None else ''
        if link.startswith('/'):
            link = BASE + link
        raw_date = n.findtext('pubDate') or n.findtext('atom:updated', namespaces=ns) or n.findtext('atom:published', namespaces=ns) or ''
        try:
            dt = email.utils.parsedate_to_datetime(raw_date)
        except Exception:
            try:
                dt = datetime.datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
            except Exception:
                dt = datetime.datetime.now(datetime.timezone.utc)
        desc_raw = n.findtext('description') or n.findtext('atom:summary', namespaces=ns) or n.findtext('atom:content', namespaces=ns) or ''
        image = ''
        enc = n.find('enclosure')
        if enc is not None and (enc.get('type') or '').startswith('image'):
            image = enc.get('url', '')
        if not image:
            for tag in ('media:content', 'media:thumbnail'):
                mc = n.find(tag, ns)
                if mc is not None and mc.get('url'):
                    image = mc.get('url')
                    break
        if not image:
            m = re.search(r'<img[^>]+src="([^"]+)"', html.unescape(desc_raw))
            image = m.group(1) if m else ''
        if image.startswith('/'):
            image = BASE + image
        kind = (n.findtext('category') or '').strip()
        items.append({'id': item_id(link), 'title': title, 'link': link, 'time': int(dt.timestamp()),
                      'date': dt.astimezone(TZ8).strftime('%Y-%m-%d'), 'desc': clean(desc_raw)[:1200],
                      'image': image, 'kind': kind})
    items.sort(key=lambda x: x['time'], reverse=True)
    return items


REL = re.compile(r'^(?P<kind>[a-z-]+)\s+(?P<title>.*?)\s+\d+\s+Posted:\s*(?P<rel>.*?(?:ago|yesterday|today|just now))\s*(?P<desc>.*)$', re.I | re.S)


def rel_to_dt(rel):
    now = datetime.datetime.now(datetime.timezone.utc)
    rel = rel.lower().strip()
    if 'yesterday' in rel:
        return now - datetime.timedelta(days=1)
    m = re.search(r'(\d+|an?|one)\s+(second|minute|hour|day|week|month|year)', rel)
    if not m:
        return now
    n = 1 if m.group(1) in ('a', 'an', 'one') else int(m.group(1))
    unit = {'second': 1 / 86400, 'minute': 1 / 1440, 'hour': 1 / 24, 'day': 1, 'week': 7, 'month': 30, 'year': 365}[m.group(2)]
    return now - datetime.timedelta(days=n * unit)


def split_listing_text(text):
    """列表頁的連結文字長這樣：'post 標題 0 Posted: 4 hours ago 簡介…'"""
    m = REL.match(text)
    if not m:
        return {'kind': '', 'title': text, 'dt': datetime.datetime.now(datetime.timezone.utc), 'desc': ''}
    return {'kind': m.group('kind'), 'title': m.group('title').strip(), 'dt': rel_to_dt(m.group('rel')), 'desc': m.group('desc').strip()}


def parse_html_listing(text):
    """RSS 網址實際回傳的是 HTML 列表頁：從連結抓標題、類型、相對時間與簡介。"""
    items, seen = [], set()
    for m in re.finditer(r'href="((?:https://robertsspaceindustries\.com)?/comm-link/[a-z-]+/(\d+)-[^"]+)"[^>]*>(.*?)</a>', text, re.S | re.I):
        link, iid, inner = m.group(1), m.group(2), clean(m.group(3))
        if iid in seen or len(inner) < 4:
            continue
        seen.add(iid)
        if link.startswith('/'):
            link = BASE + link
        p = split_listing_text(inner)
        items.append({'id': iid, 'title': p['title'], 'link': link, 'time': int(p['dt'].timestamp()),
                      'date': p['dt'].astimezone(TZ8).strftime('%Y-%m-%d'), 'desc': p['desc'][:1200],
                      'image': '', 'kind': p['kind']})
    items.sort(key=lambda x: x['time'], reverse=True)
    return items


def page_meta(link):
    """抓文章頁的 og:image 與 og:description（文章內文是 JavaScript 產生的，抓不到全文）。"""
    try:
        t = http_get(link, timeout=30)
    except Exception as e:
        print('  meta fetch failed:', link, e)
        return '', ''
    def og(prop):
        m = re.search(r'<meta[^>]+(?:property|name)="' + prop + r'"[^>]+content="([^"]*)"', t) or \
            re.search(r'<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="' + prop + r'"', t)
        return html.unescape(m.group(1)) if m else ''
    img = og('og:image')
    if img.startswith('/'):
        img = BASE + img
    desc = og('og:description')
    if 'official go-to website' in desc:
        desc = ''
    return img, desc


def fetch_items():
    text = http_get(FEED)
    try:
        items = parse_feed(text)
        if items:
            return items
    except ET.ParseError as e:
        print('Feed is not XML:', e)
    print('Falling back to HTML listing')
    return parse_html_listing(text) or parse_html_listing(http_get(BASE + '/comm-link'))


# ---------- 文章全文 ----------
# Comm-Link 文章頁本身是空殼，內文放在 data-platform-client-props 裡 htmlUrl 指向的 Alexandria HTML。
# 那份 HTML 由很多小工具組成，文字在 JSON 的 "text"／"content" 欄位，連結在 "link"／"href"。
JUNK = re.compile(r'^(button|upgrade now|shop now|fly now|buy now|learn more|browse.*|view more|read more|play now|watch now)$', re.I)


def strip_html(s):
    s = re.sub(r'<(br|/p|/h\d|/li|/div|/tr)[^>]*>', '\n', s)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s)
    return [re.sub(r'[ \t\xa0]+', ' ', l).strip() for l in s.split('\n') if l.strip()]


def good_line(l):
    if len(l) < 2 or len(l) > 1500 or JUNK.match(l):
        return False
    return not re.search(r'":\s*[\[{"]|__typename|RSIStore|json://|function\s*\(|\{\s*"', l)


def article_content(link):
    """回傳 (全文文字, 封面圖, [官方連結])；抓不到就回傳空值。"""
    try:
        page = http_get(link, timeout=40)
    except Exception as e:
        print('  article fetch failed:', link, e)
        return '', '', []
    image = ''
    m = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', page)
    if m:
        image = html.unescape(m.group(1))
        image = BASE + image if image.startswith('/') else image
    m = re.search(r'data-platform-client-props="([^"]*)"', page)
    if not m:
        return '', image, []
    try:
        content = json.loads(html.unescape(m.group(1)))['routerParams']['props']['content']
    except Exception:
        return '', image, []
    url = content.get('htmlUrl')
    if not url:
        return '', image, []
    try:
        raw = http_get(url, timeout=60)
    except Exception as e:
        print('  alexandria fetch failed:', e)
        return '', image, []
    un = html.unescape(raw)
    lines = []
    for mm in re.finditer(r'"(?:text|content)":"((?:[^"\\]|\\.)*)"', un):
        try:
            lines += strip_html(json.loads('"' + mm.group(1) + '"'))
        except Exception:
            pass
    vis = re.sub(r'<script.*?</script>|<style.*?</style>', '', raw, flags=re.S)
    vis = re.sub(r'<([a-zA-Z][\w-]*)(?:\s[^<>]*)?>', r'<\1>', vis)
    lines += strip_html(vis)
    seen, out = set(), []
    for l in lines:
        if good_line(l) and l not in seen:
            seen.add(l)
            out.append(l)
    if not image:
        mm = re.search(r'"desktop":"(/i/[^"]+\.(?:jpg|png|webp))"', un)
        image = BASE + mm.group(1) if mm else ''
    links = []
    for mm in re.finditer(r'"(?:link|href|url)":"((?:[^"\\]|\\.)*)"|href="([^"]+)"', un):
        l = (mm.group(1) or mm.group(2) or '').replace('\\/', '/')
        l = BASE + l if l.startswith('/') else l
        if ' ' in l or len(l) > 200 or not re.match(r'https://(robertsspaceindustries\.com|iae2956\.com)', l):
            continue
        if re.search(r'/(pledge|store)/|iae2956', l) and l not in links:
            links.append(l)
    return '\n'.join(out)[:MAX_TEXT], image, links


def label_official(url):
    rules = [(r'paints', '🎨 官方商店：飛船塗裝'), (r'[Mm]erchandise', '👕 官方周邊商品'), (r'/pledge/ships|/store/pledge/browse/extras|browse/ships', '🛒 官方商店：飛船'),
             (r'subscri', '⭐ 訂閱會員'), (r'game-packages|packages', '🎮 遊戲包'), (r'iae2956', '🎪 IAE 2956 官方活動頁'), (r'/pledge|/store', '🛒 官方商店')]
    for pat, name in rules:
        if re.search(pat, url):
            return name
    return '🔗 官方連結'


def site_ships():
    """讀網站 ships/ 底下各飛船頁的標題，做成 {型號小寫: (顯示名稱, 路徑)}。"""
    out = {}
    if not os.path.isdir(SITE_SHIPS):
        return out
    for fn in sorted(os.listdir(SITE_SHIPS)):
        if not fn.endswith('.html'):
            continue
        with open(os.path.join(SITE_SHIPS, fn), encoding='utf-8') as f:
            m = re.search(r'<title>([^<]+?) - Star Citizen', f.read())
        if not m or re.search(r'[一-鿿]', m.group(1)):
            continue
        name = m.group(1).strip()
        model = name.split(' ', 1)[1] if ' ' in name else name
        out[model.lower()] = (name, 'ships/' + fn)
    return out


def ship_link(name, ships):
    n = name.lower()
    for model in sorted(ships, key=len, reverse=True):
        if re.search(r'(^|[\s(])' + re.escape(model) + r'($|[\s),])', n):
            return ships[model][1]
    return ''


def build_links(item, official, ships):
    links = []
    def add(label, url):
        if url and all(url != l['url'] for l in links):
            links.append({'label': label, 'url': url})
    t = (item.get('title') or '') + ' ' + (item.get('tag') or '')
    for p in item.get('promo') or []:
        if p.get('type') in ('船', '載具'):
            page = ship_link(p['name'], ships)
            if page:
                add('🚀 ' + p['name'] + '（本站介紹）', page)
            else:
                add('📖 ' + p['name'] + '（Star Citizen Wiki）', 'https://starcitizen.tools/index.php?search=' + urllib.parse.quote_plus(p['name']))
    for u in official:
        add(label_official(u), u)
    if re.search(r'IAE', t):
        add('📰 IAE 2956 站長整理（限量船開賣時間）', 'news.html#limited-ships')
    if item.get('tag') == '新船' or any(p.get('type') == '船' for p in item.get('promo') or []):
        add('🆕 2026 新船時間表', 'ships/new-ships.html')
    if re.search(r'Alpha 4\.10\.3|4\.10\.3', t):
        add('🟢 4.10.3 改版資訊', 'update410/4103.html')
    if re.search(r'PTU|Alpha [5-9]\.', t):
        add('📡 PTU 更新追蹤台', 'ptu-tracker.html')
    if item.get('tag') in ('促銷', '新船'):
        add('💰 CCU 現金購船指南', 'ship-ccu.html')
    return links


ARTICLE_PROMPT = """你是 Star Citizen 繁體中文攻略網站的編輯。下面是 RSI 官方 Comm-Link 的一篇文章（英文標題、類型與從網頁抓下來的全文）。
請翻成「台灣用語的繁體中文」，輸出一個 JSON 物件：

- "title_zh"：中文標題（自然、精簡）
- "summary"：一到兩句中文摘要（60 字以內），說明這篇對玩家有什麼用
- "tag"：從這些選一個：活動、改版、影片、開發進度、新船、促銷、週報、故事、其他
- "sections"：全文的中文翻譯，依原文段落分段，格式 [{"h": "段落標題", "items": ["重點1", "重點2"]}]。
  忠實翻譯內容，不要自己加料；最多 8 段、每段最多 10 點。
  網頁按鈕或導覽文字（Upgrade Now、Shop Now、Button、Browse…）、重複的句子、和文章無關的雜訊都略過。
  全文是空的或只有雜訊時，給空陣列 []。
- "promo"：文章中「販售或推廣」的商品清單，格式 [{"name": "英文原名", "type": "船|載具|塗裝|裝備|周邊|組合包|其他", "note": "中文說明"}]。
  note 只寫原文有提到的資訊（價格、戰爭債券、保險、限量、販售期間、限會員等），沒有就寫商品是什麼。沒有販售內容就給 []。

翻譯規則：
- 廠商名稱、星系、地名、人名保留英文（Drake Interplanetary、Nyx、New Babbage、Jax McCleary）
- 飛船名稱寫成「英文（中文）」，名稱對照表有的一定照用；對照表沒有的直接保留英文
- Warbond 翻成「戰爭債券」，LTI 翻成「終身保險」，aUEC、SCU、PTU、IAE 保留英文

只輸出 JSON。

【名稱對照表】
__GLOSSARY__

【文章】
標題：__TITLE__
類型：__KIND__
簡介：__DESC__
全文：
__TEXT__
"""


def gemini_call(prompt, check):
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        raise RuntimeError('GEMINI_API_KEY is not set')
    models = [m for m in [os.environ.get('GEMINI_MODEL'), 'gemini-3.8-flash', 'gemini-3.6-flash', 'gemini-3.5-flash-lite'] if m]
    payload = {'contents': [{'parts': [{'text': prompt}]}],
               'generationConfig': {'temperature': 0.2, 'responseMimeType': 'application/json'}}
    last = None
    for model in models:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
        for attempt in range(3):
            try:
                r = post_json(url, payload, headers={'x-goog-api-key': key}, timeout=180)
                data = json.loads(r['candidates'][0]['content']['parts'][0]['text'])
                assert check(data)
                print(f'  translated with {model}')
                return data
            except urllib.error.HTTPError as e:
                last = f'{model} HTTP {e.code}: {e.read().decode("utf-8", "ignore")[:300]}'
                if e.code in (400, 404):
                    break
                if e.code not in (429, 500, 503):
                    raise RuntimeError(f'Gemini failed: {last}')
            except Exception as e:
                last = f'{model} {e!r}'
            time.sleep(15 * (attempt + 1))
        print(f'  {last}')
    raise RuntimeError(f'Gemini failed: {last}')


def translate_article(item, text):
    prompt = (ARTICLE_PROMPT.replace('__GLOSSARY__', load_glossary()).replace('__TITLE__', item['title'])
              .replace('__KIND__', item.get('kind') or '').replace('__DESC__', item.get('desc') or '')
              .replace('__TEXT__', text or '（抓不到全文）'))
    d = gemini_call(prompt, lambda x: isinstance(x, dict) and x.get('title_zh'))
    secs = [{'h': str(s.get('h', '')).strip(), 'items': [str(i).strip() for i in (s.get('items') or []) if str(i).strip()]}
            for s in (d.get('sections') or []) if isinstance(s, dict)]
    promo = [{'name': str(p.get('name', '')).strip(), 'type': str(p.get('type', '其他')).strip(), 'note': str(p.get('note', '')).strip()}
             for p in (d.get('promo') or []) if isinstance(p, dict) and p.get('name')]
    return {'title_zh': d.get('title_zh'), 'summary': d.get('summary', ''), 'tag': d.get('tag', '其他'),
            'sections': [s for s in secs if s['items']], 'promo': promo}



def load_glossary():
    try:
        with open(GLOSSARY, encoding='utf-8') as f:
            g = json.load(f)
        return '\n'.join(f'{k} = {v}' for k, v in g.items() if not k.startswith('_'))
    except FileNotFoundError:
        return '（無）'



def save(data):
    with open(DATA_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    with open(DATA_JS, 'w', encoding='utf-8') as f:
        f.write('// 由 scripts/news_update.py 自動產生，請勿手動修改\nwindow.SC_NEWS = ')
        json.dump(data, f, ensure_ascii=False)
        f.write(';\n')


def enrich(entry, src, ships):
    """抓全文、翻譯、整理販售內容與連結，直接寫進 entry。"""
    text, image, official = article_content(entry['link'])
    if image and not entry.get('image'):
        entry['image'] = image
    print(f"  {entry['id']} {entry['title'][:60]} | {len(text)} chars, {len(official)} links")
    t = translate_article({**entry, 'kind': src.get('kind', entry.get('kind', '')), 'desc': src.get('desc', entry.get('summary', ''))}, text)
    entry.update({k: v for k, v in t.items() if v or k in ('sections', 'promo')})
    entry['official'] = official
    entry['links'] = build_links(entry, official, ships)
    entry['full'] = bool(text)
    entry['detailed'] = True


def main():
    test = '--test' in sys.argv
    items = fetch_items()
    print(f'Found {len(items)} items; newest: {items[0]["title"] if items else "-"}')
    ships = site_ships()
    if test:
        for i in items[:2]:
            e = {'id': i['id'], 'title': i['title'], 'link': i['link'], 'image': i['image']}
            enrich(e, i, ships)
            print(json.dumps(e, ensure_ascii=False, indent=1))
        return
    try:
        with open(DATA_JSON, encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {'source': BASE + '/comm-link', 'updated': '', 'items': []}
    have = {i['id'] for i in data['items']}
    src = {i['id']: i for i in items}
    new = [i for i in items[:MAX_ITEMS] if i['id'] not in have]
    changed = False
    for i in new:
        e = {'id': i['id'], 'title': i['title'], 'title_zh': i['title'], 'summary': '', 'tag': '其他', 'link': i['link'],
             'date': i['date'], 'time': i['time'], 'image': i['image'], 'image_checked': True}
        try:
            enrich(e, i, ships)
        except Exception as ex:
            print('  translate failed, keep for next run:', ex)
            continue
        data['items'].append(e)
        changed = True
        time.sleep(6)
    # 舊文章補翻全文
    old = [x for x in data['items'] if not x.get('detailed') and x.get('fail', 0) < 3]
    old.sort(key=lambda x: x.get('time', 0), reverse=True)
    for e in old[:BACKFILL_PER_RUN]:
        try:
            enrich(e, src.get(e['id'], {}), ships)
        except Exception as ex:
            e['fail'] = e.get('fail', 0) + 1
            print('  backfill failed:', ex)
        changed = True
        time.sleep(6)
    # 站內飛船頁有新增時，重算連結
    for e in data['items']:
        if e.get('detailed'):
            nl = build_links(e, e.get('official', []), ships)
            if nl != e.get('links'):
                e['links'] = nl
                changed = True
    if not changed:
        print('No new items.')
        return
    data['items'].sort(key=lambda x: x.get('time', 0), reverse=True)
    data['items'] = data['items'][:MAX_ITEMS]
    data['updated'] = datetime.datetime.now(TZ8).strftime('%Y-%m-%d %H:%M')
    save(data)
    print(f'Added {len(new)} new, backfilled {min(len(old), BACKFILL_PER_RUN)}.')


if __name__ == '__main__':
    main()
