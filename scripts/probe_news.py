import urllib.request, re, json, html
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36'
def get(u):
    r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=40); return r.read().decode('utf-8','ignore')
def props(u):
    t=get(u); m=re.search(r'data-platform-client-props="([^"]*)"',t); return json.loads(html.unescape(m.group(1)))['routerParams']['props']
for u in ['https://robertsspaceindustries.com/comm-link/transmission/21345-Drake-Marauder','https://robertsspaceindustries.com/comm-link/transmission/20943-Monthly-Store-Bundle-2026','https://robertsspaceindustries.com/comm-link/transmission/21454-This-Week-In-Star-Citizen']:
    c=props(u)['content']; print('=====',u, 'htmlUrl', c.get('htmlUrl'), 'js', (c.get('js') or '')[:200])
    if c.get('htmlUrl'):
        h=get(c['htmlUrl']); print('HTMLLEN',len(h))
        print('LINKS', sorted(set(re.findall(r'href="([^"#]+)"',h)))[:60])
        print('IMGS', re.findall(r'(?:src|data-src)="([^"]+\.(?:jpg|png|webp)[^"]*)"',h)[:5])
        txt=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',re.sub(r'<script.*?</script>|<style.*?</style>','',h,flags=re.S)))
        print('TEXT',len(txt), html.unescape(txt)[:2500])
for u in ['https://robertsspaceindustries.com/iae2956','https://iae2956.com']:
    try:
        t=get(u); print('=====',u,len(t)); m=re.search(r'data-platform-client-props="([^"]*)"',t)
        if m: print(json.dumps(json.loads(html.unescape(m.group(1)))['routerParams'],ensure_ascii=False)[:1500])
        else: print(t[:1500])
    except Exception as e: print(u,e)
