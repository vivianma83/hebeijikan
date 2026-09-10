#!/usr/bin/env python3
"""河北冀勘官网静态构建脚本。

零依赖，只用 Python 标准库。把 src/ 下的模板与 content/site.json 合成为
dist/ 下的纯静态 HTML，可直接部署到 Netlify、阿里云 OSS 或任何静态托管。

用法：
    python3 build.py            # 构建到 dist/
    python3 build.py --serve    # 构建后起本地服务 http://127.0.0.1:8000
"""
import html
import json
import os
import re
import shutil
import sys
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
DIST = os.path.join(ROOT, "dist")
SITE_URL = "https://hebeijikan.com"

PAGE_INDEX = [
    ("index", ("首页", "一站式服务概览、权威评审认可、代表项目数据")),
    ("services", ("技术服务", "四段服务链条，采矿证 / 项目立项 / 安全许可证的完整办理流程")),
    ("municipal", ("市政与城市安全", "水文地质灾害治理、市政管线探测、CCTV 管道检测、地下空间隐蔽致灾探测")),
    ("projects", ("工程业绩", "获奖成果、部级评审文号、代表项目清单")),
    ("equipment", ("技术装备", "六类物探与检测装备参数，溶洞探测实证对照")),
    ("credentials", ("资质荣誉", "ISO9001 认证、工程设计资质、获奖证书")),
    ("about", ("关于我们", "公司概况、组织架构、三地机构、关联公司")),
    ("contact", ("联系我们", "联系方式、三地地址、在线咨询表单")),
    ("join", ("人才招聘", "招聘岗位、待遇与福利")),
]

D = json.load(open(os.path.join(ROOT, "content", "site.json"), encoding="utf-8"))


def img(name, alt, w, h, cls="", eager=False):
    """普通 <img>；构建末尾的后处理会统一包成 <picture> 并挂 WebP。"""
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<img src="/assets/img/{name}" alt="{esc(alt)}" width="{w}" height="{h}" '
            f'{load} decoding="async" class="{cls}">')


WEBP_AVAILABLE = set()


def to_picture(html_text):
    """把所有指向 assets/img 的 <img> 包成 <picture>，WebP 优先、原图兜底。"""
    def wrap(m):
        tag, path = m.group(0), m.group(1)
        stem, ext = path.rsplit(".", 1)
        if stem not in WEBP_AVAILABLE:
            return tag
        return (f'<picture><source type="image/webp" srcset="/assets/img/{stem}.webp">'
                f'{tag}</picture>')
    return re.sub(r'<img\b[^>]*?src="/assets/img/([^"]+)"[^>]*>', wrap, html_text)


# ── 取值 ────────────────────────────────────────────────────────────────
def get(path):
    """按点分路径从 site.json 取值，如 company.name。"""
    cur = D
    for part in path.split("."):
        cur = cur[part]
    return cur


def esc(s):
    return html.escape(str(s), quote=True)


# ── 区块渲染 ────────────────────────────────────────────────────────────
def blk_stats():
    out = []
    for s in get("stats"):
        cls = " stat--hl" if s.get("highlight") else ""
        unit = f'<span class="stat__unit">{esc(s["unit"])}</span>' if s.get("unit") else ""
        out.append(
            f'<div class="stat{cls}">'
            f'<div class="stat__v">{esc(s["value"])}{unit}</div>'
            f'<div class="stat__l">{esc(s["label"])}</div></div>')
    return f'<div class="stats">{"".join(out)}</div>'


def blk_service_chain():
    out = []
    for i, s in enumerate(get("serviceChain")):
        tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in s["tags"])
        dl = "<br>".join(esc(d) for d in s["deliverables"])
        out.append(
            f'<article class="svc" style="--i:{i}">'
            f'<div class="svc__no">{esc(s["step"])}</div>'
            f'<h3 class="svc__name">{esc(s["name"])}</h3>'
            f'<p class="svc__sum">{esc(s["summary"])}</p>'
            f'<div class="svc__tags">{tags}</div>'
            f'<div class="svc__dl"><span class="lbl">交付物</span>{dl}</div>'
            f'</article>')
    return f'<div class="svcs">{"".join(out)}</div>'


def blk_recognition():
    out = []
    for r in get("recognition"):
        docs = "<br>".join(esc(d) for d in r["docs"])
        out.append(
            f'<article class="rec">'
            f'<div class="rec__auth">{esc(r["authority"])}</div>'
            f'<div class="rec__kind">{esc(r["kind"])}</div>'
            f'<h3 class="rec__title">{esc(r["title"])}</h3>'
            f'<p class="rec__detail">{esc(r["detail"])}</p>'
            f'<div class="rec__docs">{docs}</div>'
            f'</article>')
    return f'<div class="recs">{"".join(out)}</div>'


def blk_figures():
    out = []
    for f in get("projectFigures"):
        rows = "".join(
            f'<div class="fig__row"><span class="fig__v">{esc(r["value"])}</span>'
            f'<span class="fig__l">{esc(r["unit"])} {esc(r["label"])}</span></div>'
            for r in f["rows"])
        out.append(
            f'<article class="fig"><h3 class="fig__name">{esc(f["name"])}</h3>'
            f'<div class="fig__rows">{rows}</div>'
            f'<p class="fig__note">{esc(f["note"])}</p></article>')
    return f'<div class="figs">{"".join(out)}</div>'


def _eq_card(e, detailed=False):
    img_el = (img(e["image"], e["name"], 560, 380, "eq__img")
              if e["image"] else '<div class="eq__img eq__img--none">暂无实拍</div>')
    detail = f'<p class="eq__detail">{esc(e["detail"])}</p>' if detailed else ""
    return (f'<article class="eq">{img_el}<div class="eq__body">'
            f'<h3 class="eq__name">{esc(e["name"])}</h3>'
            f'<p class="eq__spec">{esc(e["spec"])}</p>{detail}</div></article>')


def blk_equipment_preview():
    items = [e for e in get("equipment") if e["image"]][:4]
    return f'<div class="eqs">{"".join(_eq_card(e) for e in items)}</div>'


def blk_equipment_all():
    return f'<div class="eqs eqs--all">{"".join(_eq_card(e, True) for e in get("equipment"))}</div>'


def blk_evidence():
    out = []
    for e in get("evidence.items"):
        out.append(
            f'<article class="ev">'
            + img(e["image"], e["station"] + " 溶洞探测与开挖对照", 560, 300, "ev__img") +
            f'<div class="ev__body"><div class="ev__st">桩号 {esc(e["station"])}</div>'
            f'<div class="ev__cmp"><span class="ev__pred">推断 {esc(e["predicted"])}</span>'
            f'<span class="ev__arrow" aria-hidden="true">→</span>'
            f'<strong class="ev__act">实际揭露 {esc(e["actual"])}</strong></div>'
            f'<p class="ev__meta">{esc(e["date"])} · {esc(e["kind"])}，开挖验证</p></div></article>')
    return f'<div class="evs">{"".join(out)}</div>'


def blk_credentials():
    out = []
    for c in get("credentials"):
        rows = "".join(
            f'<div class="cred__row"><span class="cred__k">{esc(k)}</span>'
            f'<span class="cred__v{" cred__v--warn" if k == "有效期至" and c.get("expiryWarning") else ""}">{esc(v)}</span></div>'
            for k, v in c["fields"].items())
        img = (f'<img src="/assets/img/{c["image"]}" alt="{esc(c["title"])}" '
               f'width="420" height="594" loading="lazy" class="cred__img">'
               if c.get("image") else "")
        out.append(
            f'<article class="cred">{img}<div class="cred__body">'
            f'<span class="chip">{esc(c["holder"])}</span>'
            f'<h3 class="cred__title">{esc(c["title"])}</h3>'
            f'<div class="cred__std">{esc(c["standard"])}</div>'
            f'<div class="cred__rows">{rows}</div></div></article>')
    return f'<div class="creds">{"".join(out)}</div>'


def blk_permit_flows():
    out = []
    for fl in get("permitFlows"):
        nodes = []
        for i, n in enumerate(fl["nodes"]):
            cls = "flow__node"
            if i in fl.get("soft", []):
                cls += " flow__node--soft"
            if i == len(fl["nodes"]) - 1:
                cls += " flow__node--key"
            nodes.append(f'<li class="{cls}">{esc(n)}</li>')
        note = f'<p class="flow__note">{esc(fl["note"])}</p>' if fl["note"] else ""
        out.append(
            f'<section class="flow"><h3 class="flow__name">{esc(fl["name"])}</h3>'
            f'<ol class="flow__nodes">{"".join(nodes)}</ol>{note}</section>')
    return "".join(out)


def blk_project_table():
    rows = "".join(
        f'<tr><td>{esc(p["name"])}</td><td>{esc(p["service"])}</td>'
        f'<td class="pt__st">{esc(p["status"])}</td></tr>'
        for p in get("projectList"))
    return ('<div class="tablewrap"><table class="pt">'
            '<thead><tr><th>代表项目</th><th>服务内容</th><th>状态</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')


def _maps(address, name):
    """地图导航链接。用地址搜索而非坐标，避免编造经纬度。"""
    from urllib.parse import quote
    q = quote(address)
    return (f'<div class="maps">'
            f'<a class="maps__b" href="https://www.amap.com/search?query={q}" '
            f'target="_blank" rel="noopener">高德地图</a>'
            f'<a class="maps__b" href="https://map.baidu.com/search/{q}" '
            f'target="_blank" rel="noopener">百度地图</a>'
            f'<button type="button" class="maps__b maps__copy" '
            f'data-copy="{esc(address)}">复制地址</button>'
            f'</div>')


def blk_offices():
    out = []
    for o in get("offices"):
        out.append(
            f'<article class="office"><h3 class="office__name">{esc(o["name"])}</h3>'
            f'<p class="office__addr">{esc(o["address"])}</p>'
            f'<p class="office__c">{esc(o["contact"])}　'
            f'<a href="tel:{esc(o["phone"])}">{esc(o["phone"])}</a></p>'
            + _maps(o["address"], o["name"]) + '</article>')
    return f'<div class="offices">{"".join(out)}</div>'


def blk_shareholders():
    out = []
    for s in get("shareholders"):
        phone = (f'<a href="tel:{esc(s["phone"])}">{esc(s["phone"])}</a>') if s["phone"] else ""
        who = f'{esc(s["contact"])}　{phone}' if s["contact"] else phone
        addr = (f'<p class="office__addr">{esc(s["address"])}</p>'
                + _maps(s["address"], s["name"])) if s["address"] else ""
        out.append(
            f'<article class="office"><span class="chip">{esc(s["role"])}</span>'
            f'<h3 class="office__name">{esc(s["name"])}</h3>'
            f'<p class="office__focus">{esc(s["focus"])}</p>{addr}'
            f'<p class="office__c">{who}</p></article>')
    return f'<div class="offices">{"".join(out)}</div>'


def blk_benefits():
    return ('<ul class="benefits">'
            + "".join(f'<li>{esc(b)}</li>' for b in get("job.benefits"))
            + "</ul>")


def _gallery(items, cls=""):
    out = []
    for g in items:
        out.append(
            f'<figure class="ga"><img src="/assets/img/{g["image"]}" alt="{esc(g["caption"])}" '
            f'width="640" height="480" loading="lazy" class="ga__img">'
            f'<figcaption class="ga__cap">{esc(g["caption"])}</figcaption></figure>')
    return f'<div class="gas {cls}">{"".join(out)}</div>'


def blk_gallery_field():
    return _gallery(get("gallery.field"))


def blk_gallery_office():
    return _gallery(get("gallery.office"))


def blk_org_chart():
    o = get("orgChart")
    return (f'<figure class="org"><img src="/assets/img/{o["image"]}" alt="公司组织结构图" '
            f'width="860" height="412" loading="lazy" class="org__img">'
            f'<figcaption class="org__cap">{esc(o["caption"])}</figcaption></figure>')


def blk_review_docs():
    out = []
    for r in get("reviewDocs"):
        out.append(
            f'<figure class="rdoc"><h3 class="rdoc__title">{esc(r["title"])}</h3>'
            f'<img src="/assets/img/{r["image"]}" alt="{esc(r["title"])}评审意见书" '
            f'width="860" height="890" loading="lazy" class="rdoc__img">'
            f'<figcaption class="rdoc__note">{esc(r["note"])}</figcaption></figure>')
    return f'<div class="rdocs">{"".join(out)}</div>'


def blk_municipal():
    out = []
    for m in get("municipal"):
        out.append(
            f'<article class="mun">'
            f'<img src="/assets/img/{m["image"]}" alt="{esc(m["name"])}" '
            f'width="620" height="420" loading="lazy" class="mun__img">'
            f'<div class="mun__body"><h3 class="mun__name">{esc(m["name"])}</h3>'
            f'<p class="mun__desc">{esc(m["desc"])}</p>'
            f'<p class="mun__eq"><span class="lbl">主要装备</span>{esc(m["equip"])}</p>'
            f'</div></article>')
    return f'<div class="muns">{"".join(out)}</div>'


BLOCKS = {
    "stats": blk_stats, "serviceChain": blk_service_chain, "recognition": blk_recognition,
    "figures": blk_figures, "equipmentPreview": blk_equipment_preview,
    "equipmentAll": blk_equipment_all, "evidence": blk_evidence,
    "credentials": blk_credentials, "permitFlows": blk_permit_flows,
    "projectTable": blk_project_table, "offices": blk_offices,
    "shareholders": blk_shareholders, "benefits": blk_benefits, "galleryField": blk_gallery_field,
    "galleryOffice": blk_gallery_office, "orgChart": blk_org_chart,
    "reviewDocs": blk_review_docs, "municipal": blk_municipal,
}


# ── 模板渲染 ────────────────────────────────────────────────────────────
def render(text, ctx):
    def sub_partial(m):
        p = os.path.join(SRC, "partials", m.group(1).strip() + ".html")
        return render(open(p, encoding="utf-8").read(), ctx)

    def sub_block(m):
        return BLOCKS[m.group(1).strip()]()

    def sub_var(m):
        key = m.group(1).strip()
        if key in ctx:
            return str(ctx[key])
        return esc(get(key))

    for _ in range(5):                       # partial 可嵌套，迭代到稳定
        new = re.sub(r"\{\{>\s*([\w/-]+)\s*\}\}", sub_partial, text)
        if new == text:
            break
        text = new
    text = re.sub(r"\{\{%\s*(\w+)\s*%\}\}", sub_block, text)
    text = re.sub(r"\{\{\s*([\w.]+)\s*\}\}", sub_var, text)
    return text


FRONT = re.compile(r"^\s*<!--\s*(\{.*?\})\s*-->", re.S)


def build():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)

    shutil.copytree(os.path.join(SRC, "assets"), os.path.join(DIST, "assets"))
    shutil.copy(os.path.join(SRC, "favicon.ico"), os.path.join(DIST, "favicon.ico"))

    # 为每张位图生成 WebP（体积更小，浏览器优先取用；原图作为兜底保留）
    webp_saved = 0
    try:
        from PIL import Image
        imgdir = os.path.join(DIST, "assets", "img")
        for fn in os.listdir(imgdir):
            if not fn.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            src_p = os.path.join(imgdir, fn)
            dst_p = os.path.join(imgdir, fn.rsplit(".", 1)[0] + ".webp")
            im = Image.open(src_p)
            im.save(dst_p, "WEBP", quality=76, method=6)
            if os.path.getsize(dst_p) < os.path.getsize(src_p):
                webp_saved += os.path.getsize(src_p) - os.path.getsize(dst_p)
                WEBP_AVAILABLE.add(fn.rsplit('.', 1)[0])
            else:
                os.remove(dst_p)          # WebP 反而更大就不用
    except ImportError:
        print("  （未安装 Pillow，跳过 WebP 生成）")

    pages, built = [], []
    for fn in sorted(os.listdir(os.path.join(SRC, "pages"))):
        if not fn.endswith(".html"):
            continue
        raw = open(os.path.join(SRC, "pages", fn), encoding="utf-8").read()
        m = FRONT.match(raw)
        if not m:
            raise SystemExit(f"{fn} 缺少开头的 JSON front-matter 注释")
        meta = json.loads(m.group(1))
        body = raw[m.end():]

        slug = fn[:-5]
        extra = ""
        if meta.get("faq"):
            faq = {"@context": "https://schema.org", "@type": "FAQPage",
                   "mainEntity": [{"@type": "Question", "name": q,
                                   "acceptedAnswer": {"@type": "Answer", "text": a}}
                                  for q, a in meta["faq"]]}
            extra += ('<script type="application/ld+json">'
                      + json.dumps(faq, ensure_ascii=False) + "</script>")
        if meta.get("jsonld"):
            extra += ('<script type="application/ld+json">'
                      + json.dumps(meta["jsonld"], ensure_ascii=False) + "</script>")

        ctx = {
            "title": esc(meta["title"]), "description": esc(meta["description"]),
            "extrajsonld": extra, "keywords": esc(meta.get("keywords", "")),
            "slug": slug, "body": render(body, {"slug": slug}),
            "canonical": SITE_URL + ("/" if slug == "index" else f"/{slug}.html"),
            "year": str(date.today().year),
        }
        for nav in ("services", "municipal", "projects", "equipment", "credentials", "about", "contact"):
            ctx[f"nav_{nav}"] = ' aria-current="page"' if slug == nav else ""
        ctx["nav_index"] = ' aria-current="page"' if slug == "index" else ""

        out = render(open(os.path.join(SRC, "layout.html"), encoding="utf-8").read(), ctx)
        out = to_picture(out)
        open(os.path.join(DIST, fn), "w", encoding="utf-8").write(out)
        pages.append(slug)
        built.append((fn, len(out.encode("utf-8"))))

    # sitemap + robots
    urls = "".join(
        f"<url><loc>{SITE_URL}{'/' if s == 'index' else '/' + s + '.html'}</loc>"
        f"<lastmod>{date.today()}</lastmod></url>" for s in pages)
    open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    ai_bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User",
               "anthropic-ai", "PerplexityBot", "Perplexity-User", "Google-Extended",
               "Bytespider", "Baiduspider", "Applebot-Extended", "cohere-ai",
               "meta-externalagent", "YisouSpider", "Sogou web spider"]
    robots = ["User-agent: *", "Allow: /", ""]
    robots += ["# 显式放行 AI 检索爬虫：希望被大模型检索与引用"]
    for b in ai_bots:
        robots += [f"User-agent: {b}", "Allow: /", ""]
    robots += [f"Sitemap: {SITE_URL}/sitemap.xml", ""]
    open(os.path.join(DIST, "robots.txt"), "w", encoding="utf-8").write("\n".join(robots))

    # llms.txt —— 给大模型的站点索引（llmstxt.org 提议规范）
    c, ct = get("company"), get("contact")
    llms = [f"# {c['name']}", "",
            f"> {c['positioning']}。成立于 {c['founded']} 年，总部河北省秦皇岛市，"
            f"专业技术人员 {c['staff']}，下设{('、'.join(c['departments']))}。"
            f"提供物探勘查、工程设计、报告编制、证照办理、治理监测的一站式服务。", "",
            "## 核心事实", ""]
    for r in get("recognition"):
        llms.append(f"- {r['authority']}｜{r['kind']}｜{r['title']}｜{'；'.join(r['docs'])}")
    for cr in get("credentials"):
        f2 = "，".join(f"{k}：{v}" for k, v in cr["fields"].items())
        llms.append(f"- 资质｜{cr['holder']}｜{cr['title']}（{cr['standard']}）｜{f2}")
    llms += ["", "## 页面", ""]
    for slug, desc in PAGE_INDEX:
        loc = "/" if slug == "index" else f"/{slug}.html"
        llms.append(f"- [{desc[0]}]({SITE_URL}{loc})：{desc[1]}")
    llms += ["", "## 联系方式", "",
             f"- {ct['primaryTitle']} {ct['primaryName']}：{ct['phone']}（{ct['phoneNote']}）",
             f"- 邮箱：{ct['email']}"]
    for o in get("offices"):
        llms.append(f"- {o['name']}：{o['address']}，{o['contact']} {o['phone']}")
    llms += ["", f"备案号：{c['icp']}", ""]
    open(os.path.join(DIST, "llms.txt"), "w", encoding="utf-8").write("\n".join(llms))

    total_img = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, _, fs in os.walk(os.path.join(DIST, "assets", "img")) for f in fs)
    print(f"构建完成 → dist/  （{len(built)} 个页面）")
    for fn, size in built:
        print(f"  {fn:22} {size/1024:6.1f} KB")
    print(f"  图片合计 {total_img/1024:.0f} KB（其中 WebP 相比原图省下 {webp_saved/1024:.0f} KB）")


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        import http.server, socketserver, functools
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DIST)
        with socketserver.TCPServer(("127.0.0.1", 8000), h) as srv:
            print("\n本地预览 http://127.0.0.1:8000　（Ctrl+C 停止）")
            srv.serve_forever()
