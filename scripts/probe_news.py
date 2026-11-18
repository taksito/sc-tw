import urllib.request, re, json, html
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36'
BASE='https://robertsspaceindustries.com'
def get(u):
    r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=40); return r.read().decode('utf-8','ignore')
def strip(s):
    s=re.sub(r'<(br|/p|/h\d|/li|/div)[^>]*>','\n',s); s=re.sub(r'<[^>]+>',' ',s); s=html.unescape(s)
    return '\n'.join(re.sub(r'[ \t\xa0]+',' ',l).strip() for l in s.split('\n') if l.strip())
def article(u):
    t=get(u); m=re.search(r'data-platform-client-props="([^"]*)"',t)
    c=json.loads(html.unescape(m.group(1)))['routerParams']['props']['content']
    if not c.get('htmlUrl'): return '',[]
    h=get(c['htmlUrl']); U=html.unescape(h)
    parts=[]
    for m in re.finditer(r'"(?:text|content)":"((?:[^"\\]|\\.)*)"',U):
        try: s=json.loads('"'+m.group(1)+'"')
        except Exception: continue
        s=strip(s)
        if len(s)>3: parts.append(s)
    # visible html text (strip attributes first)
    vis=re.sub(r'<script.*?</script>|<style.*?</style>','',h,flags=re.S)
    vis=re.sub(r'<([a-zA-Z][\w-]*)(?:\s[^>]*)?>',r'<\1>',vis)
    vt=strip(vis)
    if len(vt)>200: parts.append(vt)
    seen=set(); out=[]
    for p in parts:
        for l in p.split('\n'):
            if l not in seen and not l.startswith('{') : seen.add(l); out.append(l)
    links=[]
    for m in re.finditer(r'"(?:link|href|url)":"((?:[^"\\]|\\.)*)"',U):
        l=m.group(1).replace('\\/','/')
        if l.startswith('/'): l=BASE+l
        if re.search(r'/(pledge|store|iae2956)',l) and l not in links: links.append(l)
    for m in re.finditer(r'href="([^"]+)"',U):
        l=m.group(1)
        if l.startswith('/'): l=BASE+l
        if re.search(r'/(pledge|store)',l) and l not in links: links.append(l)
    return '\n'.join(out), links
for u in ['https://robertsspaceindustries.com/comm-link/transmission/21345-Drake-Marauder',
 'https://robertsspaceindustries.com/comm-link/transmission/21407-IAE-2956-Drake-Interplanetary',
 'https://robertsspaceindustries.com/comm-link/transmission/20943-Monthly-Store-Bundle-2026',
 'https://robertsspaceindustries.com/comm-link/transmission/21408-IAE-2956-Tumbril-Land-Systems']:
    txt,links=article(u); print('=====',u,len(txt)); print('LINKS',links[:25]); print(txt[:2500].replace('\n',' ¶ '))
