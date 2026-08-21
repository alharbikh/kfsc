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
    '"تجربتي" "كلية الملك فهد الأمنية" "الدورة 70"',
    '"كلية الملك فهد الأمنية" "الدورة 70" "مقابلة"',
    '"كلية الملك فهد الأمنية" "تقييم المهارات"',
    'site:t.me "كلية الملك فهد الأمنية" "الدورة 70"',
    'site:x.com "كلية الملك فهد الأمنية" "الدورة 70"',
    'site:youtube.com "كلية الملك فهد الأمنية" "الدورة 70"',
]

def fetch(query: str) -> list[dict[str, str]]:
    url = "https://www.bing.com/search?" + urllib.parse.urlencode({"q": query, "format": "rss", "setlang": "ar-SA"})
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; kfsc-community-monitor/1.0)"})
    with urllib.request.urlopen(request, timeout=25) as response:
        root = ET.fromstring(response.read())
    return [{"title": (item.findtext("title") or "").strip(), "link": (item.findtext("link") or "").strip(), "published": "نتيجة بحث عامة - غير موثقة"} for item in root.findall("./channel/item") if item.findtext("title") and item.findtext("link")]

def report(items: list[dict[str, str]], checked: str) -> str:
    cards = "".join(
        f'<li><a href="{html.escape(x["link"], quote=True)}" target="_blank" rel="noopener">{html.escape(x["title"])}</a><small>{html.escape(x["published"])}</small></li>'
        for x in items[:12]
    ) or "<li>لا توجد نتائج جديدة محفوظة حتى الآن.</li>"
    return f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>متابعة الدورة 70</title><link rel="stylesheet" href="../assets/site.css"></head><body>
<nav class="topnav"><div class="nav-inner"><div class="brand">تقارير القبول - كلية الملك فهد الأمنية</div><div class="links"><a href="../index.html">الرئيسية</a><a href="../report-01-personal-interview.html">المقابلة</a><a class="active" href="course-70-monitor.html">متابعة الدورة 70</a><a href="../comprehensive-tests.html">الاختبارات</a></div></div></nav>
<main class="wrap"><header class="hero"><span class="badge">تحديث تلقائي كل 6 ساعات</span><h1>متابعة تجارب المتقدمين - الدورة 70</h1><p>يرصد هذا الملف ما يظهر علنًا في صفحات الويب ونتائج تيليجرام وX ويوتيوب المفهرسة. الغرض هو اكتشاف تجارب أو أسئلة متداولة، وليس اعتمادها كتعليمات قبول.</p></header>
<section class="section"><h2>تنبيه حول الثقة بالمحتوى</h2><div class="callout warn">كل نتيجة هنا <b>غير موثقة افتراضيًا</b>. قد تكون قديمة أو تخص دورة أخرى أو تنقل معلومة خاطئة. افتح المصدر، تحقق من التاريخ، ولا تُعامل أي محتوى كمعلومة رسمية أو تسريب مؤكد.</div></section>
<section class="section"><h2>آخر ما ظهر في المصادر العامة</h2><p class="small">آخر فحص تلقائي: {checked} UTC. تُضاف روابط جديدة فقط؛ لا يُنشأ تحديث عند عدم وجود نتائج جديدة.</p><ul class="sources">{cards}</ul></section>
<section class="section"><h2>منهجية المتابعة</h2><div class="callout official"><ul><li>تشمل عبارات البحث: تجربة المقابلة، أسئلة الدورة 70، تقييم المهارات، ومصادر مفهرسة من تيليجرام وX ويوتيوب.</li><li>لا تدخل المهمة إلى مجموعات مغلقة أو حسابات خاصة، ولا تستخدم بيانات دخول أو واجهات خاصة.</li><li>المهمة تحفظ العنوان والرابط فقط، ولا تلخص التجارب ولا تحكم بصحتها.</li><li>عند ظهور مادة مهمة، راجعها يدويًا ثم أضف استنتاجًا موثقًا إن لزم.</li></ul></div></section></main><footer class="footer">هذه المهمة تعمل على خوادم GitHub Actions ولا تتطلب فتح جهازك.</footer></body></html>'''

def main() -> None:
    STATE.parent.mkdir(exist_ok=True)
    REPORT.parent.mkdir(exist_ok=True)
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"seen": [], "items": []}
    seen = set(state.get("seen", []))
    found = []
    for query in QUERIES:
        try:
            found.extend(fetch(query))
        except Exception:
            continue
    fresh = [item for item in found if item["link"] not in seen]
    state["items"] = fresh + state.get("items", [])
    state["items"] = state["items"][:30]
    state["seen"] = [x["link"] for x in state["items"]]
    checked = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT.write_text(report(state["items"], checked), encoding="utf-8")

if __name__ == "__main__":
    main()
