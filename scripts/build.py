#!/usr/bin/env python3
"""Build the static AI 법률 지형도 site.

Reads data/posts/*.json and data/regions.json, writes the site into docs/
(served by GitHub Pages from the main branch's /docs folder).

Post JSON fields: id, region, type, status, date, title, forum, summary,
body (one sentence per line, blank line between paragraphs), sources
[{label, url}], updatedAt.
"""
import html, json, os, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "docs"

SITE_NAME = "AI 법률 지형도"
TAGLINE = "인공지능을 둘러싼 소송, 입법, 규제를 나라별로 읽는 노트"
REGIONS = [("us", "미국"), ("eu", "유럽"), ("cn", "중국"), ("jp", "일본"), ("kr", "한국"), ("other", "그 외")]
RNAME = dict(REGIONS)
TYPES = ["소송·판결", "입법·규제", "집행·조사", "정책·지침"]
STATUS_CLASS = {"진행 중": "st-open", "결정·판결": "st-done", "제정·시행": "st-law", "발표": "st-ann", "계류": "st-pend"}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,80}$")

e = lambda s: html.escape(s or "", quote=True)
fmt_date = lambda d: (d or "").replace("-", ".")


def load_posts():
    posts = []
    for f in sorted((DATA / "posts").glob("*.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        p.setdefault("id", f.stem)
        if p["id"] != f.stem:
            sys.exit(f"{f.name}: id '{p['id']}' must match the file name")
        if not ID_RE.match(p["id"]):
            sys.exit(f"{f.name}: id must be lowercase letters, digits and hyphens")
        if p.get("region") not in RNAME:
            sys.exit(f"{f.name}: unknown region {p.get('region')!r}")
        if p.get("date") and not re.match(r"^\d{4}(-\d{2}(-\d{2})?)?$", p["date"]):
            sys.exit(f"{f.name}: date must be YYYY, YYYY-MM or YYYY-MM-DD")
        posts.append(p)
    posts.sort(key=lambda p: (p.get("date") or "", p.get("title") or ""), reverse=True)
    # keep same-date ordering stable by title ascending
    posts.sort(key=lambda p: p.get("date") or "", reverse=True)
    return posts


def page(title, body, depth, desc="", current=""):
    pre = "../" * depth
    cur = lambda key: ' aria-current="page"' if current == key else ""
    nav = [f'<a href="{pre}index.html"{cur("home")}>Home</a>']
    for k, n in REGIONS:
        nav.append(f'<a href="{pre}{k}/index.html"{cur(k)}>{n}<span class="ct" data-region="{k}"></span></a>')
    nav.append(f'<a href="{pre}about/index.html"{cur("about")}>About</a>')
    full_title = SITE_NAME if title == SITE_NAME else f"{title} | {SITE_NAME}"
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc or TAGLINE)}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc or TAGLINE)}">
<meta property="og:type" content="{'article' if depth == 2 else 'website'}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+KR:wght@400;500;600&family=Noto+Serif+KR:wght@600;700&display=swap">
<link rel="stylesheet" href="{pre}assets/style.css">
</head>
<body>
<div class="wrap">
  <header class="site">
    <a class="site-title" href="{pre}index.html">{e(SITE_NAME)}</a>
    <p class="site-tag">{e(TAGLINE)}</p>
    <nav class="menu" aria-label="메뉴">{''.join(nav)}</nav>
  </header>
  <main>
{body}
  </main>
  <footer class="foot">
    <p>실무에서 마주치는 AI 법률 이슈를 판결문과 보도를 바탕으로 정리합니다.</p>
    <p>각 글의 출처를 함께 적었습니다. 업무에 인용할 때는 원문으로 다시 확인하세요.</p>
  </footer>
</div>
</body>
</html>
"""


def meta_row(p, pre, with_region):
    parts = []
    if with_region:
        parts.append(f'<a href="{pre}{p["region"]}/index.html">{e(RNAME[p["region"]])}</a>')
    parts.append(f"<span>{e(fmt_date(p.get('date')) or '날짜 미상')}</span>")
    if p.get("type"):
        parts.append(f"<span>{e(p['type'])}</span>")
    return '<div class="pmeta">' + '<span class="sep">·</span>'.join(parts) + "</div>"


def tag_row(p):
    st = p.get("status")
    if not st:
        return ""
    return f'<div class="tags"><span class="tag {STATUS_CLASS.get(st, "st-ann")}">{e(st)}</span></div>'


def post_card(p, pre):
    hay = " ".join([p.get("title", ""), p.get("forum", ""), p.get("summary", ""), p.get("body", ""), p.get("type", "")]).lower()
    return f"""<article class="post" data-type="{e(p.get('type'))}" data-hay="{e(hay)}">
  {meta_row(p, pre, True)}
  <h2><a href="{pre}posts/{p['id']}/index.html">{e(p.get('title'))}</a></h2>
  {f'<p class="excerpt">{e(p["summary"])}</p>' if p.get('summary') else ''}
  {tag_row(p)}
</article>"""


TOOLBAR = """<div class="toolbar">
  <label class="search"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.6"/><path d="M11 11l3.5 3.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
  <input id="q" type="search" placeholder="사건명, 기관, 법리로 검색" aria-label="검색"></label>
  <select id="tfilter" class="tfilter" aria-label="유형"><option value="">모든 유형</option>""" + "".join(f'<option value="{t}">{t}</option>' for t in TYPES) + """</select>
</div>"""

FILTER_JS = """<script>
(function(){var q=document.getElementById('q'),t=document.getElementById('tfilter'),posts=[].slice.call(document.querySelectorAll('.post')),none=document.getElementById('none');
function run(){var s=q.value.trim().toLowerCase(),ty=t.value,n=0;posts.forEach(function(p){var ok=(!ty||p.dataset.type===ty)&&(!s||p.dataset.hay.indexOf(s)>=0);p.hidden=!ok;if(ok)n++;});none.hidden=n>0;}
q.addEventListener('input',run);t.addEventListener('change',run);})();
</script>"""


def list_body(posts, pre, head=""):
    cards = "\n".join(post_card(p, pre) for p in posts) or '<div class="empty"><strong>아직 글이 없습니다</strong>글이 올라오면 여기에 표시됩니다.</div>'
    return f"""{head}
{TOOLBAR}
<div class="posts">
{cards}
</div>
<div class="empty" id="none" hidden><strong>조건에 맞는 글이 없습니다</strong>검색어나 유형을 바꿔 보세요.</div>
{FILTER_JS}"""


def body_lines(text):
    out, n = [], 0
    for par in re.split(r"\n\s*\n", (text or "").strip()):
        lines = [l.strip() for l in par.split("\n") if l.strip()]
        if not lines:
            continue
        rows = []
        for l in lines:
            n += 1
            rows.append(f'<div class="ln"><span class="no">{n}.</span><span class="tx">{e(l)}</span></div>')
        out.append('<div class="blk">' + "".join(rows) + "</div>")
    return '<div class="lines">' + "".join(out) + "</div>" if out else ""


def post_body(p, siblings, pre):
    srcs = [s for s in p.get("sources") or [] if str(s.get("url", "")).startswith(("http://", "https://"))]
    src_html = ""
    if srcs:
        lis = "".join(f'<li><a href="{e(s["url"])}" target="_blank" rel="noopener noreferrer">{e(s.get("label") or s["url"])}</a></li>' for s in srcs)
        src_html = f'<section class="srcbox"><h3>출처</h3><ul>{lis}</ul></section>'
    idx = next(i for i, s in enumerate(siblings) if s["id"] == p["id"])
    newer = siblings[idx - 1] if idx > 0 else None
    older = siblings[idx + 1] if idx < len(siblings) - 1 else None
    pager = ""
    if newer or older:
        a = []
        if older:
            a.append(f'<a class="prev" href="{pre}posts/{older["id"]}/index.html"><span class="dir">← 이전 글</span><span class="tt">{e(older["title"])}</span></a>')
        if newer:
            a.append(f'<a class="next" href="{pre}posts/{newer["id"]}/index.html"><span class="dir">다음 글 →</span><span class="tt">{e(newer["title"])}</span></a>')
        pager = '<nav class="pager" aria-label="이전 글, 다음 글">' + "".join(a) + "</nav>"
    body = body_lines(p.get("body")) or (f'<p class="nobody">{e(p.get("summary"))}</p>' if p.get("summary") else "")
    return f"""<div class="crumbs"><a href="{pre}index.html">Home</a><span>›</span><a href="{pre}{p['region']}/index.html">{e(RNAME[p['region']])}</a></div>
<article class="full">
  <h1>{e(p.get('title'))}</h1>
  {meta_row(p, pre, False)}
  {f'<p class="forum">{e(p["forum"])}</p>' if p.get('forum') else ''}
  {tag_row(p)}
  {body}
  {src_html}
  {pager}
</article>"""


COUNT_JS = """<script>
(function(){var c=%s;[].forEach.call(document.querySelectorAll('.ct[data-region]'),function(s){s.textContent=c[s.dataset.region]||'0';});})();
</script>"""


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    posts = load_posts()
    regions = json.loads((DATA / "regions.json").read_text(encoding="utf-8"))
    counts = {k: sum(1 for p in posts if p["region"] == k) for k, _ in REGIONS}
    cjs = COUNT_JS % json.dumps(counts)

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    shutil.copy(ROOT / "assets" / "style.css", OUT / "assets" / "style.css")
    write(OUT / ".nojekyll", "")

    write(OUT / "index.html", page(SITE_NAME, list_body(posts, "") + cjs, 0, current="home"))

    for k, n in REGIONS:
        rp = [p for p in posts if p["region"] == k]
        ov = regions.get(k, "")
        ov_html = f'<p class="ov">{e(ov)}</p>' if ov else ""
        head = f'<section class="cathead"><div class="eyebrow">나라별</div><h1>{e(n)}</h1>{ov_html}</section>'
        write(OUT / k / "index.html", page(n, list_body(rp, "../", head) + cjs, 1, desc=ov.split("\n")[0] if ov else "", current=k))
        for p in rp:
            write(OUT / "posts" / p["id"] / "index.html",
                  page(p["title"], post_body(p, rp, "../../") + cjs, 2, desc=p.get("summary", ""), current=k))

    about = """<section class="about"><h1>About</h1>
<p>인공지능을 둘러싼 소송·판결, 입법·규제, 집행·조사, 정책·지침을 미국, 유럽, 중국, 일본, 한국, 그 밖의 나라로 나누어 정리하는 노트입니다.</p>
<p>글은 짧은 문장에 번호를 붙여 사건의 배경, 쟁점, 판단, 의미를 차례로 따라가도록 썼습니다. 각 글 아래에 근거가 된 판결문과 보도를 적었습니다.</p>
<p>매주 월요일 지난 한 주의 소식을 더합니다. 판결문 원문을 직접 확인한 글과 보도만을 근거로 한 글이 섞여 있으니, 업무에 쓸 때는 출처의 원문으로 다시 확인하세요.</p>
</section>"""
    write(OUT / "about" / "index.html", page("About", about + cjs, 1, current="about"))
    write(OUT / "404.html", page("페이지를 찾을 수 없습니다", '<div class="empty"><strong>페이지를 찾을 수 없습니다</strong>주소가 바뀌었거나 삭제된 글일 수 있습니다.</div>', 0))
    print(f"built {len(posts)} posts into {OUT}")


if __name__ == "__main__":
    main()
