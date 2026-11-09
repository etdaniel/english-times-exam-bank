"""Collect candidate English exam resource links from Google News RSS.

Discovery only: never download or republish exam PDFs.
"""
import datetime
import hashlib
import json
import pathlib
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "candidates.json"

# Focus on Gimpo school exams, plus nationwide English mock exams and CSAT.
SCHOOL_QUERIES = [
    '"김포" "중학교" "영어" "기말고사" 기출',
    '"김포" "중학교" "영어" "중간고사" 기출',
    '"김포" "고등학교" "영어" "기말고사" 기출',
    '"김포" "고등학교" "영어" "중간고사" 기출',
    '"나래중" "영어" 시험',
    '"은여울중" "영어" 시험',
    '"김포한가람중" "영어" 시험',
    '"솔터고" "영어" 시험',
    '"김포제일고" "영어" 시험',
]
NATIONAL_QUERIES = [
    'site:ebsi.co.kr "영어" "전국연합학력평가" "문제"',
    'site:ebsi.co.kr "영어" "모의고사" "정답"',
    'site:kice.re.kr "영어" "대학수학능력시험" "문제"',
    'site:kice.re.kr "영어" "수능" "모의평가"',
]

EXCLUDED = re.compile(
    r'검정고시|임용|교원.?시험|공무원|경찰.?채용|소방.?채용|'
    r'토익|TOEIC|토플|TOEFL|텝스|TEPS|아이엘츠|IELTS|'
    r'한국사능력|자격증|자격시험|편입|대학원|공인중개사|'
    r'학원.?강사.?채용|채용.?시험',
    re.IGNORECASE,
)
ENGLISH = re.compile(r'영어|영문|English', re.IGNORECASE)
SCHOOL_EXAM = re.compile(
    r'중간고사|기말고사|중간시험|기말시험|내신|시험지|기출문제|'
    r'중[123]|고[123]|중학교|고등학교',
    re.IGNORECASE,
)
GIMPO = re.compile(
    r'김포|나래중|은여울중|김포한가람중|솔터고|김포제일고',
    re.IGNORECASE,
)
NATIONAL = re.compile(
    r'전국연합|학력평가|모의고사|모의평가|수능|대학수학능력시험',
    re.IGNORECASE,
)


def classify(title, query):
    if EXCLUDED.search(title):
        return None
    if not ENGLISH.search(title):
        return None
    if query in SCHOOL_QUERIES:
        if not GIMPO.search(title) or not SCHOOL_EXAM.search(title):
            return None
        return "gimpo_school_exam"
    if not NATIONAL.search(title):
        return None
    return "national_exam"


def fetch_items(query):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({
        "q": query, "hl": "ko", "gl": "KR", "ceid": "KR:ko"
    })
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "EnglishTimesExamBank/1.0 (RSS discovery only)"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        xml = response.read(2_000_000)
    root = ET.fromstring(xml)
    return root.findall(".//item")[:25]


def main():
    existing = json.loads(PATH.read_text(encoding="utf-8")) if PATH.exists() else []
    if not isinstance(existing, list):
        raise ValueError("candidates.json must contain a JSON array")
    known = {str(item.get("id")) for item in existing if isinstance(item, dict)}
    added = 0
    skipped = 0
    for query in SCHOOL_QUERIES + NATIONAL_QUERIES:
        try:
            items = fetch_items(query)
            for item in items:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if not title or not link:
                    skipped += 1
                    continue
                category = classify(title, query)
                if category is None:
                    skipped += 1
                    continue
                parsed = urllib.parse.urlparse(link)
                if parsed.scheme not in ("https", "http"):
                    skipped += 1
                    continue
                uid = hashlib.sha256(link.encode()).hexdigest()[:16]
                if uid in known:
                    continue
                existing.append({
                    "id": uid,
                    "title": title,
                    "url": link,
                    "source_query": query,
                    "found_on": datetime.date.today().isoformat(),
                    "status": "pending",
                    "rights": "unverified",
                    "category": category,
                })
                known.add(uid)
                added += 1
        except Exception as exc:
            print("검색 실패:", query, type(exc).__name__, str(exc)[:160])
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("새 후보:", added, "필터 제외:", skipped, "전체:", len(existing))


if __name__ == "__main__":
    main()
