import urllib.request, re, json, html, collections
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36'
def get(u):
    r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=40); return r.read().decode('utf-8','ignore')
def props(u):
    t=get(u); m=re.search(r'data-platform-client-props="([^"]*)"',t); return json.loads(html.unescape(m.group(1)))['routerParams']['props']
for u in ['https://robertsspaceindustries.com/comm-link/transmission/21345-Drake-Marauder','https://robertsspaceindustries.com/comm-link/transmission/21415-IAE-2956-Merchandise']:
    c=props(u)['content']; print('=====',u, c.get('htmlUrl'), (c.get('js') or '')[:150])
    if not c.get('htmlUrl'): continue
    h=get(c['htmlUrl'])
    print('WIDGETS', collections.Counter(re.findall(r'name="([A-Za-z]+Widget)"',h)).most_common())
    print('ATTRS', collections.Counter(re.findall(r'\s(data-[a-z-]+)=',h)).most_common(40))
    for k in ['pledge','/store/','"url"','"price"','"slug"','"name"','"title"','"body"','"text"','"description"']:
        hs=[m.start() for m in re.finditer(re.escape(k),html.unescape(h))]
        print('KEY',k,len(hs))
    U=html.unescape(h)
    for m in list(re.finditer(r'pledge[^"\s]{0,120}',U))[:15]: print('PL',m.group(0))
    for m in list(re.finditer(r'"(?:title|text|body|description|excerpt|content)":"((?:[^"\\]|\\.){20,300})',U))[:25]: print('TX',m.group(0)[:300])
    print('RAW', U[:3000])
