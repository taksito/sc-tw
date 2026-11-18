import urllib.request, re, json, html
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36'
def get(u):
    r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=40); return r.read().decode('utf-8','ignore')
t=get('https://robertsspaceindustries.com/comm-link/transmission/21407-IAE-2956-Drake-Interplanetary')
m=re.search(r'data-platform-client-props="([^"]*)"',t)
p=json.loads(html.unescape(m.group(1)))
s=json.dumps(p,ensure_ascii=False)
print('PROPSLEN',len(s)); print(s[:6000])
js=get('https://static.robertsspaceindustries.com/plt-client/plt-client.es.js')
print('JSLEN',len(js))
for pat in [r'graphql[^"\'`]{0,80}', r'["\'`](/api/[^"\'`]{2,100})', r'alexandria[^"\'`]{0,100}', r'import\("([^"]+)"\)', r'from"([^"]+)"']:
    print(pat, sorted(set(re.findall(pat,js,re.I)))[:40])
