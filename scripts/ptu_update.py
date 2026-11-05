#!/usr/bin/env python3
"""PTU 更新追蹤台：抓 RSI Spectrum Patch Notes 論壇的新公告，用 Gemini 翻譯成繁體中文。

用法：
  python scripts/ptu_update.py            # 檢查新公告、翻譯、寫回 data/ptu-notes.json 與 data/ptu-notes.js
  python scripts/ptu_update.py --test     # 只翻譯最新一篇印出來，不寫檔（測試 API 用）

環境變數：
  GEMINI_API_KEY   必填（GitHub Secrets）
  GEMINI_MODEL     選填，預設 gemini-2.5-flash
"""
import json, os, re, sys, time, datetime, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JSON = os.path.join(ROOT, 'data', 'ptu-notes.json')
DATA_JS = os.path.join(ROOT, 'data', 'ptu-notes.js')
GLOSSARY = os.path.join(ROOT, 'data', 'glossary.json')
CHANNEL_ID = '190048'
FORUM_URL = 'https://robertsspaceindustries.com/spectrum/community/SC/forum/190048'
API = 'https://robertsspaceindustries.com/api/spectrum'
MAX_POSTS = 10
UA = 'Mozilla/5.0 (compatible; sc-tw-ptu-tracker/1.0; +https://taksito.github.io/sc-tw/)'


def post_json(url, payload, headers=None, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), method='POST',
                                 headers={'Content-Type': 'application/json', 'User-Agent': UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))


def list_threads():
    r = post_json(f'{API}/forum/channel/threads', {'channel_id': CHANNEL_ID, 'page': 1, 'sort': 'newest', 'label_id': None})
    if not r.get('success'):
        raise RuntimeError(f'Spectrum threads API failed: {r.get("code")} {r.get("msg")}')
    return r['data']['threads']


def thread_text(slug):
    r = post_json(f'{API}/forum/thread/nested', {'slug': slug, 'sort': 'votes', 'target_reply_id': None})
    if not r.get('success'):
        raise RuntimeError(f'Spectrum thread API failed for {slug}: {r.get("code")}')
    out = []
    for b in r['data'].get('content_blocks') or []:
        if b.get('type') != 'text':
            continue
        for bl in (b.get('data') or {}).get('blocks') or []:
            t = (bl.get('text') or '').strip()
            if not t:
                continue
            typ = bl.get('type', '')
            if typ.startswith('header'):
                out.append('## ' + t)
            elif 'list-item' in typ:
                out.append('- ' + t)
            else:
                out.append(t)
    return '\n'.join(out)


PROMPT = """你是 Star Citizen 繁體中文攻略網站的翻譯。請把下面這篇官方 Patch Notes 翻譯成「台灣用語的繁體中文」，並整理成 JSON。

規則：
1. 飛船、載具、武器、組件名稱一律寫成「英文（中文）」，例如 Polaris（北極星）、LBCO Skarnov Rifle（LBCO Skarnov 步槍）。有出現在【名稱對照表】的一定要用表裡的中文；表裡沒有的，請自己取一個自然的中文名。
2. 地點、勢力、任務名、遊戲系統（mobiGlas、ASOP、Quantum Travel 等）保留英文，必要時在後面加括號中文說明。
3. "Potential Fix:" 翻成「可能修正：」。STARC-xxxxx 這類回報編號可以省略。
4. 依原文分段（例如 測試重點、遊戲性更新、飛船與載具、錯誤修正、已知問題），每段標題前加一個合適的 emoji。內容盡量完整，不要漏掉數值變化。
5. highlight：用一句話（40 字以內）寫出這版最重要的 2～3 個重點。
6. 只輸出 JSON，格式：
{"highlight": "...", "sections": [{"h": "🎯 測試重點", "items": ["...", "..."]}]}

【名稱對照表】
__GLOSSARY__

【原文】
__TEXT__
"""


def load_glossary():
    try:
        with open(GLOSSARY, encoding='utf-8') as f:
            g = json.load(f)
        return '\n'.join(f'{k} = {v}' for k, v in g.items() if not k.startswith('_'))
    except FileNotFoundError:
        return '（無）'


def gemini_translate(text):
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        raise RuntimeError('GEMINI_API_KEY is not set')
    model = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
    prompt = PROMPT.replace('__GLOSSARY__', load_glossary()).replace('__TEXT__', text)
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    payload = {'contents': [{'parts': [{'text': prompt}]}],
               'generationConfig': {'temperature': 0.2, 'responseMimeType': 'application/json'}}
    last = None
    for attempt in range(4):
        try:
            r = post_json(url, payload, headers={'x-goog-api-key': key}, timeout=180)
            raw = r['candidates'][0]['content']['parts'][0]['text']
            data = json.loads(raw)
            assert isinstance(data.get('sections'), list) and data['sections']
            return data
        except urllib.error.HTTPError as e:
            last = f'HTTP {e.code}: {e.read().decode("utf-8", "ignore")[:300]}'
            if e.code not in (429, 500, 503):
                break
        except Exception as e:  # malformed JSON etc.
            last = repr(e)
        time.sleep(20 * (attempt + 1))
    raise RuntimeError(f'Gemini translation failed: {last}')


def meta_from_title(title):
    m = re.search(r'Alpha\s+([\d.]+)\s*(PTU|LIVE|EPTU|Hotfix)?', title, re.I)
    version = m.group(1) if m else ''
    kind = 'LIVE' if re.search(r'LIVE', title) else ('PTU' if re.search(r'PTU', title, re.I) else 'NOTE')
    build = (re.search(r'(\d{7,9})\s*$', title.strip()) or [None, ''])[1]
    aud = ''
    a = re.match(r'\s*\[([^\]]+)\]', title)
    if a:
        tag = a.group(1)
        aud = {'All Backers': '所有支持者 (All Backers)', 'All Waves': '所有測試梯次 (All Waves)'}.get(tag)
        if not aud:
            w = re.match(r'Wave\s*(\d+)', tag, re.I)
            aud = f'第 {w.group(1)} 梯次 (Wave {w.group(1)})' if w else tag
    return version, kind, build, aud


def build_post(t, translated):
    version, kind, build, aud = meta_from_title(t['subject'])
    return {
        'id': str(t['id']),
        'title': t['subject'],
        'url': f'{FORUM_URL}/thread/{t["slug"]}',
        'date': datetime.datetime.fromtimestamp(t['time_created'], datetime.timezone.utc).strftime('%Y-%m-%d'),
        'time': t['time_created'],
        'version': version, 'kind': kind, 'build': build, 'audience': aud,
        'highlight': translated.get('highlight', ''),
        'sections': translated['sections'],
    }


def save(data):
    with open(DATA_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    with open(DATA_JS, 'w', encoding='utf-8') as f:
        f.write('// 由 scripts/ptu_update.py 自動產生，請勿手動修改\nwindow.PTU_NOTES = ')
        json.dump(data, f, ensure_ascii=False)
        f.write(';\n')


def main():
    test = '--test' in sys.argv
    threads = list_threads()
    threads.sort(key=lambda t: t['time_created'], reverse=True)
    if test:
        t = threads[0]
        print('Testing with:', t['subject'])
        print(json.dumps(gemini_translate(thread_text(t['slug'])), ensure_ascii=False, indent=1))
        return
    with open(DATA_JSON, encoding='utf-8') as f:
        data = json.load(f)
    have = {p['id'] for p in data['posts']}
    newest = threads[:MAX_POSTS]
    oldest_kept = min((p.get('time', 0) for p in data['posts']), default=0)
    todo = [t for t in newest if str(t['id']) not in have and t['time_created'] >= oldest_kept]
    if not todo:
        print('No new posts.')
        return
    for t in reversed(todo):
        print('Translating:', t['subject'])
        data['posts'].append(build_post(t, gemini_translate(thread_text(t['slug']))))
        time.sleep(5)
    data['posts'].sort(key=lambda p: p.get('time', 0), reverse=True)
    data['posts'] = data['posts'][:MAX_POSTS]
    data['updated'] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')
    save(data)
    print(f'Added {len(todo)} post(s).')


if __name__ == '__main__':
    main()
