#!/usr/bin/env python3
"""官方最新消息：抓 RSI Comm-Link 的新文章，用 Gemini 翻成繁體中文摘要。

用法：
  python scripts/news_update.py            # 檢查新文章、翻譯、寫回 data/news.json 與 data/news.js
  python scripts/news_update.py --test     # 只抓清單並翻譯最新 3 篇印出來，不寫檔

環境變數：
  GEMINI_API_KEY   必填（GitHub Secrets，跟 PTU 追蹤台共用）
  GEMINI_MODEL     選填
"""
import json, os, re, sys, time, html, datetime, email.utils, urllib.request, urllib.error
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JSON = os.path.join(ROOT, 'data', 'news.json')
DATA_JS = os.path.join(ROOT, 'data', 'news.js')
GLOSSARY = os.path.join(ROOT, 'data', 'glossary.json')
FEED = 'https://robertsspaceindustries.com/comm-link/rss'
BASE = 'https://robertsspaceindustries.com'
MAX_ITEMS = 20
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


PROMPT = """你是 Star Citizen 繁體中文攻略網站的編輯。下面是 RSI 官方 Comm-Link 的新文章清單（英文標題與簡介）。
請把每一篇翻成「台灣用語的繁體中文」，輸出 JSON 陣列，順序與輸入相同。

每一篇輸出：
- "id"：照抄輸入的 id
- "title_zh"：中文標題（自然、精簡；飛船名稱寫成「英文（中文）」，名稱對照表有的一定照用）
- "summary"：一到兩句中文摘要（60 字以內），說明這篇對玩家有什麼用；簡介太短就依標題合理描述，不要編造細節
- "tag"：從這些選一個：活動、改版、影片、開發進度、新船、促銷、週報、故事、其他

只輸出 JSON 陣列，例如：[{"id": "123", "title_zh": "...", "summary": "...", "tag": "活動"}]

【名稱對照表】
__GLOSSARY__

【文章】
__ITEMS__
"""


def load_glossary():
    try:
        with open(GLOSSARY, encoding='utf-8') as f:
            g = json.load(f)
        return '\n'.join(f'{k} = {v}' for k, v in g.items() if not k.startswith('_'))
    except FileNotFoundError:
        return '（無）'


def gemini_translate(items):
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        raise RuntimeError('GEMINI_API_KEY is not set')
    models = [m for m in [os.environ.get('GEMINI_MODEL'), 'gemini-3.8-flash', 'gemini-3.6-flash', 'gemini-3.5-flash-lite'] if m]
    src = json.dumps([{'id': i['id'], 'title': i['title'], 'type': i['kind'], 'desc': i['desc']} for i in items], ensure_ascii=False, indent=1)
    prompt = PROMPT.replace('__GLOSSARY__', load_glossary()).replace('__ITEMS__', src)
    payload = {'contents': [{'parts': [{'text': prompt}]}],
               'generationConfig': {'temperature': 0.2, 'responseMimeType': 'application/json'}}
    last = None
    for model in models:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
        for attempt in range(3):
            try:
                r = post_json(url, payload, headers={'x-goog-api-key': key}, timeout=90)
                data = json.loads(r['candidates'][0]['content']['parts'][0]['text'])
                assert isinstance(data, list) and data
                print(f'  translated with {model}')
                return {str(d.get('id')): d for d in data}
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


def save(data):
    with open(DATA_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    with open(DATA_JS, 'w', encoding='utf-8') as f:
        f.write('// 由 scripts/news_update.py 自動產生，請勿手動修改\nwindow.SC_NEWS = ')
        json.dump(data, f, ensure_ascii=False)
        f.write(';\n')


def main():
    test = '--test' in sys.argv
    items = fetch_items()
    print(f'Found {len(items)} items; newest: {items[0]["title"] if items else "-"}')
    if test:
        for i in items[:5]:
            print(json.dumps(i, ensure_ascii=False)[:300])
        print(json.dumps(gemini_translate(items[:3]), ensure_ascii=False, indent=1))
        return
    try:
        with open(DATA_JSON, encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {'source': BASE + '/comm-link', 'updated': '', 'items': []}
    have = {i['id'] for i in data['items']}
    todo = [i for i in items[:MAX_ITEMS] if i['id'] not in have]
    if not todo:
        print('No new items.')
        return
    for i in todo:
        if not i['image'] or not i['desc']:
            img, desc = page_meta(i['link'])
            i['image'] = i['image'] or img
            if desc and len(desc) > len(i['desc']):
                i['desc'] = desc
            time.sleep(1)
    tr = gemini_translate(todo)
    for i in todo:
        t = tr.get(i['id'], {})
        data['items'].append({'id': i['id'], 'title': i['title'], 'title_zh': t.get('title_zh') or i['title'],
                              'summary': t.get('summary', ''), 'tag': t.get('tag', '其他'), 'link': i['link'],
                              'date': i['date'], 'time': i['time'], 'image': i['image']})
    data['items'].sort(key=lambda x: x.get('time', 0), reverse=True)
    data['items'] = data['items'][:MAX_ITEMS]
    data['updated'] = datetime.datetime.now(TZ8).strftime('%Y-%m-%d %H:%M')
    save(data)
    print(f'Added {len(todo)} item(s).')


if __name__ == '__main__':
    main()
