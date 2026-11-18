import urllib.request, re, json
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36'
def get(u, data=None, ct=None):
    h={'User-Agent':UA}
    if ct: h['Content-Type']=ct
    r=urllib.request.urlopen(urllib.request.Request(u,data=data,headers=h),timeout=40)
    return r.status, r.read().decode('utf-8','ignore')
for u in ['https://robertsspaceindustries.com/comm-link/transmission/21345-Drake-Marauder',
          'https://robertsspaceindustries.com/comm-link/transmission/21407-IAE-2956-Drake-Interplanetary']:
    s,t=get(u); print('=====',u,s,len(t))
    print('scripts:', re.findall(r'<script[^>]+src="([^"]+)"',t)[:30])
    print('api:', sorted(set(re.findall(r'["\'](/api/[^"\'\s]{3,80})',t)))[:40])
    print('pledge links:', sorted(set(re.findall(r'href="([^"]*(?:pledge|store)[^"]*)"',t)))[:40])
    for k in ['__NEXT_DATA__','__NUXT__','window.__','application/json','segment','data-component']:
        print(k, t.count(k))
    body=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)
    txt=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',body))
    i=txt.find('Marauder') if 'Marauder' in u else txt.find('Drake')
    print('TEXTLEN',len(txt)); print(txt[:3000])
    for m in re.finditer(r'<script[^>]*>(.{0,400})',t,re.S):
        sn=m.group(1).strip()
        if sn and len(sn)>50: print('INLINE:',sn[:400].replace('\n',' '))
