"""Find candidate links via Google News RSS; do not download or republish PDFs."""
import json, pathlib, urllib.parse, urllib.request, xml.etree.ElementTree as ET, hashlib, datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
path=ROOT/'data'/'candidates.json'
existing=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
known={x['id'] for x in existing}
queries=[
 'site:kice.re.kr 영어 수능 기출문제',
 'site:ebsi.co.kr 영어 전국연합학력평가 문제 정답',
 'site:goe.go.kr 영어 전국연합학력평가 문제',
]
added=0
for q in queries:
    url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':q,'hl':'ko','gl':'KR','ceid':'KR:ko'})
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'EnglishTimesExamBank/1.0 (RSS discovery only)'})
        with urllib.request.urlopen(req,timeout=20) as r: xml=r.read(2_000_000)
        root=ET.fromstring(xml)
        for item in root.findall('.//item')[:25]:
            title=(item.findtext('title') or '').strip()
            link=(item.findtext('link') or '').strip()
            if not title or not link:continue
            uid=hashlib.sha256(link.encode()).hexdigest()[:16]
            if uid in known:continue
            existing.append({'id':uid,'title':title,'url':link,'source_query':q,'found_on':datetime.date.today().isoformat(),'status':'pending','rights':'unverified'})
            known.add(uid);added+=1
    except Exception as e:
        print('검색 실패:',q,type(e).__name__,str(e)[:160])
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('새 후보:',added,'전체:',len(existing))
