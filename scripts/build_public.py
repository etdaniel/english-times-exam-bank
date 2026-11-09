"""Publish only reviewed, explicitly approved official links."""
import json,pathlib,urllib.parse
root=pathlib.Path(__file__).resolve().parents[1]
candidates=json.loads((root/'data'/'candidates.json').read_text(encoding='utf-8'))
approved=[]
for c in candidates:
    url=c.get('approved_url') or c.get('url','')
    parsed=urllib.parse.urlparse(url)
    if c.get('status')!='approved' or c.get('rights')!='link_only' or parsed.scheme!='https' or not parsed.netloc:continue
    approved.append({'title':c.get('title','자료'),'url':url,'found_on':c.get('found_on',''),'source':c.get('source_query','')})
(root/'docs'/'approved.json').write_text(json.dumps(approved,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('공개 링크:',len(approved))
