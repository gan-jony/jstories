#!/usr/bin/env python3
"""Builds the static Jachnun Stories archive into ./site from src/data.json.

Run from the repo root:  python3 src/build.py
Commerce controls (cart, log in, rewards, add to cart, ...) are rendered but disabled.
"""
import json, re, html, shutil
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
D = json.load(open(ROOT / "src" / "data.json"))

SITE_URL = "https://jstories.uk"
CLOSED_MSG = "The store is closed. This is a demo website, kept online as an archive."
TIP = "The shop is closed"

# ---------------------------------------------------------------- helpers
def esc(s): return html.escape(s or "", quote=True)
def money(p): return "£{:,.2f}".format(p / 100)

def norm(u):
    u = u.split("?")[0]
    return "https:" + u if u.startswith("//") else u

def img_for(u):
    name = D["imgMap"].get(norm(u))
    return f"/img/{name}" if name else None

def clean_html(raw):
    """Sanitise Shopify rich text: drop scripts, contact/cart links, editor attrs; remap images."""
    soup = BeautifulSoup(raw or "", "lxml")
    for t in soup(["script", "style", "noscript", "iframe", "form"]):
        t.decompose()
    for a in soup.find_all("a"):
        href = a.get("href", "")
        if re.search(r"wa\.me|mailto:|/cart|/pages/contact|/account|/checkout|/apps/", href):
            a.unwrap()
    for img in soup.find_all("img"):
        src = img.get("src", "")
        new = img_for(src)
        if new:
            img["src"] = new
            for k in ("srcset", "width", "height"):
                img.attrs.pop(k, None)
            img["loading"] = "lazy"
            img.attrs.setdefault("alt", "")
        else:
            img.decompose()
    for tag in soup.find_all(True):
        for k in list(tag.attrs):
            if k.startswith("data-") or k in ("style", "class", "id") or k.startswith("on"):
                del tag.attrs[k]
    body = soup.body.decode_contents() if soup.body else str(soup)
    return body.strip()

def text_of(raw):
    return re.sub(r"\s+", " ", BeautifulSoup(raw or "", "lxml").get_text(" ")).strip()

# ---------------------------------------------------------------- layout
CSS = """
@font-face{font-family:"Fraunces";src:url(/fonts/fraunces-latin-wght-normal.woff2) format("woff2");font-weight:100 900;font-style:normal;font-display:swap}
@font-face{font-family:"Inter";src:url(/fonts/inter-latin-wght-normal.woff2) format("woff2");font-weight:100 900;font-style:normal;font-display:swap}
@font-face{font-family:"Heebo";src:url(/fonts/heebo-hebrew-wght-normal.woff2) format("woff2");font-weight:100 900;font-style:normal;font-display:swap;unicode-range:U+0590-05FF,U+200C-2010,U+20AA,U+25CC,U+FB1D-FB4F}
:root{--serif:"Fraunces",Georgia,"Times New Roman","Heebo",serif;--sans:"Inter",system-ui,-apple-system,"Segoe UI",Roboto,"Heebo",sans-serif;--peach:#f69679;--peach-deep:#e2795a;--peach-soft:#fde8e1;--ink:#2b2220;--muted:#6e5f5a;--bg:#fffaf7;--card:#fff;--line:#f1ddd5;--pink:#e8588a}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.7 var(--sans);font-optical-sizing:auto}
h1,h2,h3{font-family:var(--serif);font-weight:600;letter-spacing:-.01em}
.rte,.desc,.narrow>p,.hero+p{font-family:var(--sans)}
a{color:inherit}img{max-width:100%;height:auto;display:block}
.sans,nav,.btn,.badge,.price,footer,.bar,.crumbs,.tag{font-family:var(--sans)}
.bar{background:var(--ink);color:#fff;text-align:center;font-size:.85rem;padding:9px 16px;line-height:1.4}
header.top{background:var(--peach);padding:16px}
.top-in{max-width:1100px;margin:0 auto;display:flex;align-items:center;gap:20px;flex-wrap:wrap}
.top-in .logo img{width:150px}
nav.main{display:flex;gap:22px;flex-wrap:wrap;flex:1}
nav.main a{text-decoration:none;font-weight:600;font-size:.95rem;color:#2b2220;padding:4px 0;border-bottom:2px solid transparent}
nav.main a:hover,nav.main a[aria-current]{border-color:#2b2220}
.tools{display:flex;gap:10px;align-items:center}
.pill{display:inline-flex;align-items:center;gap:7px;background:rgba(255,255,255,.55);border:0;border-radius:999px;padding:7px 14px;font:600 .85rem var(--sans);color:#2b2220}
.pill[disabled]{cursor:not-allowed;opacity:.8}
main{max-width:1100px;margin:0 auto;padding:0 16px 56px}
.narrow{max-width:720px;margin:0 auto}
h1{font-size:2.4rem;line-height:1.15;margin:28px 0 12px}h2{font-size:1.6rem;line-height:1.25;margin:40px 0 12px}h3{font-size:1.1rem;margin:0 0 6px}
.tag{text-transform:uppercase;letter-spacing:.12em;font-size:.75rem;color:var(--muted);margin:28px 0 4px}
.notice{background:var(--peach-soft);border-left:4px solid var(--peach);padding:14px 18px;border-radius:6px;margin:22px 0;font-family:var(--sans);font-size:.95rem}
.notice p{margin:0}
.hero img{width:100%;max-height:440px;object-fit:cover;object-position:center 62%;border-radius:14px;margin-top:24px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:18px;margin:16px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;text-decoration:none;display:flex;flex-direction:column}
.card img{aspect-ratio:1/1;object-fit:cover;width:100%;background:#fff}
.card .cb{padding:12px 14px 14px}.card h3{font-size:1rem;margin:0 0 4px}
.price{font-weight:600;font-size:.95rem}.price s{color:var(--muted);font-weight:400;margin-left:6px}
.badge{display:inline-block;font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;background:var(--peach-soft);color:var(--peach-deep);border-radius:999px;padding:2px 10px;margin-top:6px}
.sec-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px}
.sec-head a{font:600 .85rem var(--sans);color:var(--muted)}
.btn{display:inline-block;border:0;border-radius:8px;padding:12px 22px;font-weight:700;font-size:.95rem;background:var(--peach-deep);color:#fff;text-decoration:none;cursor:pointer}
.btn[disabled],.btn.is-off{background:#d8c7c0;color:#fff;cursor:not-allowed}
.btn.block{width:100%}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px;margin:20px 0}
.promo{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px;text-align:center}
.promo img{max-width:240px;margin:0 auto 12px;border-radius:8px}
.icons{display:flex;gap:28px;justify-content:center;flex-wrap:wrap;margin:36px 0}
.icons img{width:72px;height:72px;object-fit:contain;margin:0 auto 6px}.icons span{display:block;text-align:center;font:.8rem var(--sans);color:var(--muted)}
.sub{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin:24px 0}
.sub input{padding:11px 14px;border:1px solid var(--line);border-radius:8px;min-width:240px;font-size:.95rem;background:#fff}
.crumbs{font-size:.82rem;color:var(--muted);margin:22px 0 4px}.crumbs a{text-decoration:none}.crumbs a:hover{text-decoration:underline}
.product{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:32px;margin-top:12px}
.gallery .main{border-radius:12px;width:100%;background:#fff;border:1px solid var(--line)}
.thumbs{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}.thumbs img{width:64px;height:64px;object-fit:cover;border-radius:8px;border:1px solid var(--line);cursor:pointer}
.buy label{display:block;font:600 .8rem var(--sans);margin:16px 0 4px;color:var(--muted)}
.buy select,.buy input[type=number]{padding:10px 12px;border:1px solid var(--line);border-radius:8px;font-size:.95rem;background:#f4ece8;min-width:200px}
.buy .btn{margin-top:18px}
.desc{margin-top:24px}.desc ul,.rte ul,.rte ol{padding-left:22px}
.rte img{border-radius:10px;margin:16px auto}
.post{border-bottom:1px solid var(--line);padding:22px 0}.post h2{margin:0 0 6px}.post a{text-decoration:none}.post .meta{font:.85rem var(--sans);color:var(--muted)}
.more{font:600 .9rem var(--sans);color:var(--peach-deep)}
.deliv div{margin:2px 0}.deliv [dir]{unicode-bidi:plaintext}
footer{border-top:1px solid var(--line);padding:26px 16px 44px;text-align:center;font-size:.9rem;color:var(--muted)}
footer a{margin:0 10px}
.rewards{position:fixed;right:16px;bottom:16px;z-index:10}
.rewards button{background:var(--pink);color:#fff;border:0;border-radius:999px;padding:12px 20px;font:700 .85rem var(--sans);box-shadow:0 4px 14px rgba(0,0,0,.18);cursor:not-allowed;opacity:.85}
@media(max-width:560px){h1{font-size:1.9rem}.top-in .logo img{width:120px}.top-in{gap:12px}nav.main{gap:14px}.tools{width:100%}}
"""

def page(path, title, body, desc="", og_img="/img/hero.jpg", canonical=None, nav=None):
    canon = canonical or path
    nav_items = [("/", "Home"), ("/blogs/news", "Blog"), ("/pages/jachnun-stories-delivery-out-of-london", "Deliveries out of London")]
    nav_html = "".join(
        f'<a href="{u}"{" aria-current=\"page\"" if nav == u else ""}>{t}</a>' for u, t in nav_items)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE_URL}{canon}">
<meta name="theme-color" content="#f69679">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website"><meta property="og:url" content="{SITE_URL}{canon}">
<meta property="og:image" content="{SITE_URL}{og_img}">
<link rel="icon" href="/img/logo.png">
<style>{CSS}</style></head>
<body>
<div class="bar">{esc(CLOSED_MSG)}</div>
<header class="top"><div class="top-in">
<a class="logo" href="/"><img src="/img/logo.png" alt="Jachnun Stories"></a>
<nav class="main">{nav_html}</nav>
<div class="tools">
<button class="pill" disabled title="{TIP}" aria-label="Log in (unavailable)">&#128100; Log in</button>
<button class="pill" disabled title="{TIP}" aria-label="Cart (unavailable)">&#128722; Cart <span>0</span></button>
</div></div></header>
<main>
{body}
</main>
<div class="rewards"><button disabled title="{TIP}">&#9733; REWARDS</button></div>
<footer>
<div><a href="https://www.facebook.com/JachnunStories/" rel="noopener">Facebook</a><a href="https://www.instagram.com/jachnunstories/" rel="noopener">Instagram</a></div>
<p>&copy; 2026 Jachnun Stories</p>
</footer>
</body></html>"""

def write(rel, content):
    p = SITE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# ---------------------------------------------------------------- data views
P = D["products"]; C = D["collections"]
product_cols = {}
for c, v in C.items():
    for h in v["handles"]:
        product_cols.setdefault(h, []).append(c)

def first_img(h):
    return f"/img/p-{h}-1.jpg"

def card(h, col=None):
    p = P[h]
    href = f"/collections/{col}/products/{h}" if col else f"/products/{h}"
    price = f'<span class="price">{money(p["price"])}'
    if p.get("compare") and p["compare"] > p["price"]:
        price += f' <s>{money(p["compare"])}</s>'
    price += "</span>"
    return (f'<a class="card" href="{href}"><img src="{first_img(h)}" alt="{esc(p["title"])}" loading="lazy">'
            f'<div class="cb"><h3>{esc(p["title"])}</h3>{price}<br><span class="badge">No longer available</span></div></a>')

def disabled_btn(label, extra=""):
    return f'<button class="btn {extra}" disabled title="{TIP}">{label}</button>'

# ---------------------------------------------------------------- home
HOME_ORDER = ["homemade-original-jachnun", "homemade-vegan-jachnun", "extras", "something-sweet", "the-frozen-collection", "jachnun-pots"]

def build_home():
    secs = ""
    for c in HOME_ORDER:
        v = C[c]
        cards = "".join(card(h, c) for h in v["handles"])
        secs += (f'<div class="sec-head"><h2>{esc(v["title"].title() if v["title"].isupper() else v["title"])}</h2>'
                 f'<a href="/collections/{c}">View all</a></div><div class="grid">{cards}</div>')
    body = f"""
<div class="hero"><img src="/img/hero.jpg" alt="Homemade Jachnun with baked egg, grated tomato and schug" fetchpriority="high"></div>
<p class="tag">A small project, 2020 to 2021</p>
<h1>Jachnun Stories</h1>
<p class="sans" style="margin-top:-4px"><strong>Original Jachnun homemade by order</strong></p>
<div class="notice"><p><strong>The store is closed; this is a demo website.</strong> The shop below is preserved as it was, as a keepsake of a very tasty chapter. Buttons are shown for memory only and do not work.</p></div>

<div class="narrow">
<h2>The story of rolling</h2>
<p>It started as an underground tradition: Jachnun brunch for friends. Then it became a weekly one, thanks to the feedback of the people who came back for more. The rolling and the baking were mine. The support and demand were what let Jachnun Stories grow.</p>
<p>My story: I'm Jonathan, a hi-tech entrepreneur. For six years I had been leading a tech startup, with an amazing team and partners. On weekends, in rare moments of free time, I baked Jachnuns and invited friends over for brunch to enjoy this traditional weekend meal with me. Then the coronavirus slowed the business rhythm, and I suddenly discovered more and more free slots in my calendar.</p>
<p>So I skipped another Netflix binge and dedicated my weekends to Jachnun rolls. I pulled out my Yemenite grandma's original Jachnun recipe and my grandpa's secret pepper Schug recipe (amazing!) and started to roll. After years of friendly, sarcastic "what about my Jachnun?" from my local community, I finally made the time for a whole weekend of Jachnun bakes, then the following weekend, and then another.</p>
<p>Delicious, authentic, handmade with love. Simply enjoy it.</p>
<h2>How the deliveries worked</h2>
<p>We delivered the Jachnun brunch to most areas of London (zones 1 to 5), on Saturdays and Sundays only, arriving between 8:30 and 11:30. Orders for the weekend stayed open all week until 6PM the evening before.</p>
</div>

<h2 style="margin-top:48px">Homemade Original Jachnun, Kubaneh and more</h2>
{secs}

<div class="two">
<div class="promo"><img src="/img/h-club.png" alt="The Jachnun Club"><h3>Let's be friends</h3><p class="sans" style="font-size:.9rem">Join The Jachnun Club and earn points for every order and referral.</p>{disabled_btn("Join the club")}</div>
<div class="promo"><img src="/img/h-gift.png" alt="Gift voucher"><h3>Gift voucher</h3><p class="sans" style="font-size:.9rem">Treat someone special with a digital gift voucher and invite them to a traditional Israeli Jachnun brunch.</p>{disabled_btn("Explore gift vouchers")}</div>
</div>

<div class="icons">
<div><img src="/img/i-handmade.png" alt="Handmade"><span>Handmade</span></div>
<div><img src="/img/i-vegan.png" alt="Vegan options"><span>Vegan options</span></div>
<div><img src="/img/i-recycable.png" alt="Recyclable packaging"><span>Recyclable</span></div>
<div><img src="/img/i-quality.png" alt="Quality"><span>Quality</span></div>
</div>
"""
    write("index.html", page("/", "Jachnun Stories", body,
          "Jachnun Stories: homemade Yemenite Jachnun, rolled and baked overnight. A small project, now closed and kept online as an archive.", nav="/"))

# ---------------------------------------------------------------- collections & products
def build_collections():
    for c, v in C.items():
        if not v["handles"]:
            continue
        title = v["title"].title() if v["title"].isupper() else v["title"]
        cards = "".join(card(h, c) for h in v["handles"])
        body = (f'<div class="crumbs"><a href="/">Home</a> / {esc(title)}</div><h1>{esc(title)}</h1>'
                f'<div class="notice"><p>{esc(CLOSED_MSG)}</p></div><div class="grid">{cards}</div>')
        write(f"collections/{c}.html", page(f"/collections/{c}", f"{title} | Jachnun Stories", body,
              f"{title} from Jachnun Stories (archive)."))

def build_product(h, col=None):
    p = P[h]
    imgs = [f"/img/p-{h}-{i+1}.jpg" for i in range(len(p["images"]))]
    thumbs = ""
    if len(imgs) > 1:
        thumbs = '<div class="thumbs">' + "".join(
            f'<img src="{u}" alt="{esc(p["title"])} photo {i+1}" onclick="document.getElementById(\'mainimg\').src=this.src">'
            for i, u in enumerate(imgs)) + "</div>"
    price = money(p["price"])
    cmp_ = f' <s>{money(p["compare"])}</s>' if p.get("compare") and p["compare"] > p["price"] else ""
    variants = ""
    if len(p["variants"]) > 1:
        opts = "".join(f'<option>{esc(v["t"])} - {money(v["price"])}</option>' for v in p["variants"])
        variants = f'<label>Option</label><select disabled title="{TIP}">{opts}</select>'
    crumb_col = ""
    if col:
        ct = C[col]["title"]; ct = ct.title() if ct.isupper() else ct
        crumb_col = f' / <a href="/collections/{col}">{esc(ct)}</a>'
    elif product_cols.get(h):
        col0 = product_cols[h][0]; ct = C[col0]["title"]; ct = ct.title() if ct.isupper() else ct
        crumb_col = f' / <a href="/collections/{col0}">{esc(ct)}</a>'
    desc = clean_html(p["desc"])
    body = f"""
<div class="crumbs"><a href="/">Home</a>{crumb_col} / {esc(p["title"])}</div>
<div class="product">
<div class="gallery"><img id="mainimg" class="main" src="{imgs[0]}" alt="{esc(p["title"])}">{thumbs}</div>
<div class="buy">
<h1 style="margin-top:0">{esc(p["title"])}</h1>
<p class="price" style="font-size:1.25rem">{price}{cmp_}</p>
<span class="badge">No longer available</span>
{variants}
<label>Quantity</label><input type="number" value="1" min="1" disabled title="{TIP}">
<div>{disabled_btn("Add to cart", "block")}</div>
<div class="notice" style="margin-top:20px"><p>{esc(CLOSED_MSG)}</p></div>
<div class="desc rte">{desc}</div>
</div></div>"""
    path = f"/collections/{col}/products/{h}" if col else f"/products/{h}"
    dtxt = text_of(p["desc"])[:155]
    write(path.lstrip("/") + ".html", page(path, f'{p["title"]} | Jachnun Stories', body, dtxt,
          og_img=imgs[0], canonical=f"/products/{h}"))

# ---------------------------------------------------------------- blog
def build_blog():
    posts = ""
    for a in D["articles"]:
        date = a["metaLine"].split("|")[1].strip() if "|" in a["metaLine"] else ""
        by = a["metaLine"].split("|")[0].strip()
        ex = a["meta"] or text_of(a["html"])[:200]
        posts += (f'<article class="post"><h2><a href="/blogs/news/{a["slug"]}">{esc(a["title"])}</a></h2>'
                  f'<p class="meta">{esc(by)} &middot; {esc(date)}</p><p>{esc(ex)}</p>'
                  f'<a class="more" href="/blogs/news/{a["slug"]}">Read more</a></article>')
    body = f'<div class="narrow"><h1>News</h1>{posts}</div>'
    write("blogs/news.html", page("/blogs/news", "News | Jachnun Stories", body, "Jachnun recipe and instructions from Jachnun Stories.", nav="/blogs/news"))
    for a in D["articles"]:
        date = a["metaLine"].split("|")[1].strip() if "|" in a["metaLine"] else ""
        by = a["metaLine"].split("|")[0].strip()
        body = (f'<div class="narrow"><div class="crumbs"><a href="/">Home</a> / <a href="/blogs/news">News</a> / {esc(a["title"])}</div>'
                f'<h1>{esc(a["title"])}</h1><p class="meta sans" style="color:var(--muted);font-size:.9rem">{esc(by)} &middot; {esc(date)}</p>'
                f'<div class="rte">{clean_html(a["html"])}</div><p><a class="more" href="/blogs/news">&larr; Back to News</a></p></div>')
        og = f'/img/a-{a["slug"]}-1.jpg'
        write(f'blogs/news/{a["slug"]}.html', page(f'/blogs/news/{a["slug"]}', f'{a["title"]} | Jachnun Stories', body,
              (a["meta"] or text_of(a["html"]))[:155], og_img=og, nav="/blogs/news"))

# ---------------------------------------------------------------- delivery page
def build_delivery():
    soup = BeautifulSoup(D["pages"]["delivery"]["html"], "lxml")
    # remove the contact call-to-action ("צרו קשר להזמנה", WhatsApp, e-mail)
    for t in soup.find_all(string=re.compile("צרו קשר|יוצרים קשר")):
        node = t.find_parent("div")
        if node: node.decompose()
    for a in soup.find_all("a"):
        if re.search(r"wa\.me|mailto:", a.get("href", "")):
            parent = a.find_parent("span") or a
            parent.decompose()
    for br in soup.find_all("br"):
        pass
    cleaned = clean_html(str(soup.body.decode_contents() if soup.body else soup))
    soup2 = BeautifulSoup(cleaned, "lxml")
    for d in soup2.find_all("div"):
        d["dir"] = "auto"
        d["style"] = "text-align:center"
    for e in soup2.find_all(True):
        if e.name == "div" and not e.get_text(strip=True) and not e.find("img"):
            e.decompose()
    inner = soup2.body.decode_contents() if soup2.body else cleaned
    body = (f'<div class="narrow deliv"><h1>Special delivery to your city</h1>'
            f'<div class="notice"><p>{esc(CLOSED_MSG)} This page shows how deliveries outside London used to work.</p></div>'
            f'<div class="rte">{inner}</div></div>')
    write("pages/jachnun-stories-delivery-out-of-london.html",
          page("/pages/jachnun-stories-delivery-out-of-london", "Special Delivery to Your City | Jachnun Stories", body,
               "How Jachnun Stories deliveries outside London worked (archive).", nav="/pages/jachnun-stories-delivery-out-of-london"))

# ---------------------------------------------------------------- misc
def build_misc():
    write("404.html", page("/404", "Page not found | Jachnun Stories",
          '<div class="narrow"><h1>Page not found</h1><p>This page is not part of the archive. <a href="/">Back to the home page</a>.</p></div>'))
    write("_redirects", "\n".join([
        "/cart / 302", "/cart/* / 302", "/pages/contact-us / 302", "/apps/help-center / 302", "/apps/* / 302",
        "/account / 302", "/account/* / 302", "/checkout / 302", "/search / 302", "/policies/* / 302",
        "/collections / 302", "/products / 302", "/blogs / /blogs/news 302", "/collections/speicals / 302", ""]))
    write("robots.txt", "User-agent: *\nAllow: /\nSitemap: https://jstories.uk/sitemap.xml\n")
    urls = ["/", "/blogs/news", "/pages/jachnun-stories-delivery-out-of-london"]
    urls += [f"/blogs/news/{a['slug']}" for a in D["articles"]]
    urls += [f"/collections/{c}" for c, v in C.items() if v["handles"]]
    urls += [f"/products/{h}" for h in P]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "\n".join(f"<url><loc>{SITE_URL}{u}</loc></url>" for u in urls) + "\n</urlset>\n")

def main():
    # keep images, wipe generated html
    for p in SITE.iterdir():
        if p.name in ("img", "fonts"): continue
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    build_home(); build_collections(); build_blog(); build_delivery(); build_misc()
    n = 0
    for h in P:
        build_product(h); n += 1
        for c in product_cols.get(h, []):
            build_product(h, c); n += 1
    print("product pages:", n, "| total html files:", len(list(SITE.rglob("*.html"))))

if __name__ == "__main__":
    main()
