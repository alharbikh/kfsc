"""Cloud-only monitor for official Course 70 news. No secrets or AI API required."""
from __future__ import annotations

import html
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data" / "course70-monitor-state.json"
REPORT = ROOT / "reports" / "course-70-monitor.html"
QUERIES = [
    'site:moi.gov.sa "كلية الملك فهد الأمنية" "الدورة 70"',
    'site:spa.gov.sa "كلية الملك فهد الأمنية" "بكالوريوس العلوم الأمنية" "70"',
]

def fetch(query: str) -> list[dict[str, str]]:
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": query, "hl": "ar", "gl": "SA", "ceid": "SA:ar"})
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=25) as response:
        root = ET.fromstring(response.read())
    items = []
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        if title and link:
            items.append({"title": title, "link": link, "published": published})
    return items

def report(items: list[dict[str, str]], checked: str) -> str:
    cards = "".join(
        f'<li><a href="{html.escape(x["link"], quote=True)}" target="_blank" rel="noopener">{html.escape(x["title"])}</a><small>{html.escape(x["published"])}</small></li>'
        for x in items[:12]
    ) or "<li>لا توجد نتائج جديدة محفوظة حتى الآن.</li>"
    return f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>متابعة الدورة 70</title><link rel="stylesheet" href="../assets/site.css"></head><body>
<nav class="topnav"><div class="nav-inner"><div class="brand">تقارير القبول - كلية الملك فهد الأمنية</div><div class="links"><a href="../index.html">الرئيسية</a><a href="../report-01-personal-interview.html">المقابلة</a><a class="active" href="course-70-monitor.html">متابعة الدورة 70</a><a href="../comprehensive-tests.html">الاختبارات</a></div></div></nav>
<main class="wrap"><header class="hero"><span class="badge">تحديث تلقائي كل 6 ساعات</span><h1>متابعة تجارب وإجراءات الدورة 70</h1><p>يرصد هذا الملف نتائج منشورة مرتبطة بالكلية من نطاقي وزارة الداخلية ووكالة الأنباء السعودية. لا يُعد أي عنوان «تجربة طالب» أو معلومة مؤكدة قبل فتح المصدر والتحقق منه.</p></header>
<section class="section"><h2>حالة المعرفة الأساسية</h2><div class="callout official">المعلن رسميًا في إجراءات الدورة 70: التحقق من الهوية ثم المقابلة الشخصية، يليها تقييم المهارات والمعايير المطلوبة، ثم الفحص الطبي. ولا توجد - في هذه المتابعة - تجربة مباشرة موثقة تشرح محتوى تقييم المهارات بالتفصيل.</div></section>
<section class="section"><h2>آخر نتائج المصدر الرسمي</h2><p class="small">آخر فحص تلقائي: {checked} UTC. تُضاف نتائج جديدة فقط؛ لا يُنشأ تحديث عند عدم وجود روابط جديدة.</p><ul class="sources">{cards}</ul></section>
<section class="section"><h2>منهجية المتابعة</h2><div class="callout warn"><ul><li>المصادر الآلية محصورة في نطاقي <b>moi.gov.sa</b> و<b>spa.gov.sa</b>.</li><li>المهمة لا تخترع أسئلة ولا تفسر النتائج؛ تحفظ العنوان والرابط وتاريخ النشر الظاهر.</li><li>التحديثات ذات القيمة تحتاج مراجعة بشرية قبل اعتبارها تجربة مؤكدة أو تغييرًا في إجراءات القبول.</li></ul></div></section></main><footer class="footer">هذه المهمة تعمل على خوادم GitHub Actions ولا تتطلب فتح جهازك.</footer></body></html>'''

def main() -> None:
    STATE.parent.mkdir(exist_ok=True)
    REPORT.parent.mkdir(exist_ok=True)
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"seen": [], "items": []}
    seen = set(state.get("seen", []))
    found = [item for query in QUERIES for item in fetch(query)]
    fresh = [item for item in found if item["link"] not in seen]
    state["items"] = fresh + state.get("items", [])
    state["items"] = state["items"][:30]
    state["seen"] = [x["link"] for x in state["items"]]
    checked = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT.write_text(report(state["items"], checked), encoding="utf-8")

if __name__ == "__main__":
    main()
