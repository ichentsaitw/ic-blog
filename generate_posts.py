import docx, os, json, shutil, re, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE_SRC = r"C:\Users\silly\新思惟國際 Dropbox\Tsai I-Chen\!!00IC_documents\ClaudeCowork\blog-test"
BASE_DST = r"C:\Users\silly\projects\ic-blog"

os.makedirs(os.path.join(BASE_DST, "posts", "images"), exist_ok=True)

ARTICLES_META = {
    "20220717_安倍晉三大戰略":         {"slug": "abe-grand-strategy",         "category": "閱讀筆記"},
    "20220721_統合心智":               {"slug": "synthesizing-mind",           "category": "閱讀筆記"},
    "20220901_不想念中國史中國地理":    {"slug": "history-geography-school",    "category": "教養思考"},
    "20220910_解決問題的能力":          {"slug": "problem-solving-skill",       "category": "教養思考"},
    "20220910_關於北歐教養的一些想法":  {"slug": "nordic-parenting",            "category": "教養思考"},
    "20220927_中華民國4.0":            {"slug": "roc-4",                       "category": "時事觀點"},
    "20221018_是的我去做老花雷射LBV了": {"slug": "lbv-laser-experience",        "category": "生活健康"},
    "20221023_敦煌壁畫中的太空船":      {"slug": "dunhuang-spaceship",          "category": "時事觀點"},
    "20221120_李紹榕主編的書":          {"slug": "li-shaorong-book",            "category": "閱讀筆記"},
    "20221209_那些散落的星星":          {"slug": "scattered-stars",             "category": "閱讀筆記"},
    "20221225_極限返航":               {"slug": "extreme-return",              "category": "閱讀筆記"},
    "20230214_關於應徵住院醫師的一些資訊": {"slug": "resident-application-info","category": "醫療教育"},
    "20230222_科部團隊問題":            {"slug": "department-team-issues",      "category": "醫療教育"},
    "20230310_翰林雲端學院":            {"slug": "hanlin-online-school",        "category": "教養思考"},
    "20230313_與成功有約最後一堂課":     {"slug": "7-habits-last-lesson",       "category": "閱讀筆記"},
    "20230705_AI時代的創意教養":        {"slug": "ai-era-creative-parenting",   "category": "教養思考"},
    "20230902_黑熊學院藍鵲行動":        {"slug": "black-bear-academy",          "category": "時事觀點"},
    "20250210_VEX家長":                {"slug": "vex-parent-questions",        "category": "教養思考"},
}

def read_docx_paragraphs(path):
    """Return list of (text, is_bold) tuples for non-empty paragraphs."""
    d = docx.Document(path)
    result = []
    for p in d.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        # Check if paragraph is bold: all non-empty runs are bold
        is_heading = 'Heading' in (p.style.name if p.style else '')
        runs_with_text = [r for r in p.runs if r.text.strip()]
        is_bold = all(r.bold for r in runs_with_text) if runs_with_text else False
        result.append((text, is_bold or is_heading))
    return result

def paras_to_html(paras):
    """paras is list of (text, is_bold) tuples."""
    parts = []
    for i, (p, is_bold) in enumerate(paras):
        # Skip title (first para) and author line
        if i == 0 or re.match(r'^(作者|讀者|Author)[:：]', p):
            continue
        if p.startswith('<iframe'):
            parts.append(p)
        elif p.startswith('問：') or p.startswith('問:'):
            parts.append(f'<p class="qa-q">{p}</p>')
        elif (p.startswith('答：') or p.startswith('答:')) and is_bold:
            parts.append(f'<p class="qa-a"><strong>{p}</strong></p>')
        elif is_bold and i > 0:
            # Bold paragraph = subheading (h3)
            parts.append(f'<h3>{p}</h3>')
        else:
            parts.append(f'<p>{p}</p>')
    return '\n'.join(parts)

def get_excerpt(paras):
    """paras is list of (text, is_bold) tuples."""
    skip = [r'^(作者|讀者)[:：]', r'^[（(]', r'^http', r'^<iframe']
    for p_text, is_bold in paras[1:]:
        if is_bold:
            continue
        if not any(re.match(pat, p_text) for pat in skip) and len(p_text) > 20:
            return p_text[:120] + ('…' if len(p_text) > 120 else '')
    return ''

def copy_images(src_folder, slug):
    img_dir = os.path.join(BASE_DST, "posts", "images", slug)
    os.makedirs(img_dir, exist_ok=True)
    imgs = []
    for f in sorted(os.listdir(src_folder)):
        if f.lower().endswith(('.jpg','.jpeg','.png','.gif','.webp')):
            shutil.copy2(os.path.join(src_folder, f), os.path.join(img_dir, f))
            imgs.append(f)
    return imgs

def make_post_html(title, date_str, category, slug, cover_img, content_html, excerpt, extra_imgs):
    og_desc = excerpt.replace('"', '&quot;').replace("'", "&#39;")
    cover_url = f"images/{slug}/{cover_img}" if cover_img else ""
    og_img_url = f"https://ichentsaitw.github.io/ic-blog/posts/images/{slug}/{cover_img}" if cover_img else ""

    extra_imgs_html = ""
    for img in extra_imgs:
        extra_imgs_html += f'<figure class="article-img"><img src="images/{slug}/{img}" alt="" loading="lazy"></figure>\n'

    hero_html = f'<img class="hero-img" src="{cover_url}" alt="{title}">' if cover_img else ''

    ld_json = ('{"@context":"https://schema.org","@type":"Article","headline":"' + title +
               '","description":"' + og_desc + '","datePublished":"' + date_str +
               '","author":{"@type":"Person","name":"蔡依橙"},"publisher":{"@type":"Organization","name":"IC 觀點","url":"https://ichentsaitw.github.io/ic-blog/"},"url":"https://ichentsaitw.github.io/ic-blog/posts/' + slug + '.html"}')

    STATIC_HEAD = '''<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="author" content="蔡依橙">
<meta name="robots" content="index, follow">
<meta property="og:type" content="article">
<meta property="og:locale" content="zh_TW">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='18' fill='%23C8602A'/%3E%3Ctext x='50' y='56' text-anchor='middle' dominant-baseline='central' font-family='serif' font-weight='bold' font-size='52' fill='white'%3EIC%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@600;700&display=swap" rel="stylesheet">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag("js",new Date());gtag("config","G-XXXXXXXXXX");</script>'''

    STATIC_CSS = '''<style>
:root{--accent:#C8602A;--text:#2C2825;--text-light:#6B6460;--bg:#F9F7F4;--border:#EAE4DC;}
*{margin:0;padding:0;box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{font-family:"Noto Sans TC",-apple-system,sans-serif;background:var(--bg);color:var(--text);-webkit-font-smoothing:antialiased;}
header{position:sticky;top:0;z-index:100;background:#1A1814;border-bottom:1px solid rgba(255,255,255,0.06);}
.hinner{max-width:1280px;margin:0 auto;padding:0 24px;height:60px;display:flex;align-items:center;gap:16px;}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none;}
.logo-icon{width:32px;height:32px;background:var(--accent);border-radius:8px;display:flex;align-items:center;justify-content:center;font-family:"Noto Serif TC",serif;font-weight:700;font-size:13px;color:white;}
.logo-text{font-family:"Noto Serif TC",serif;font-weight:700;font-size:16px;color:white;}
.back-link{margin-left:auto;color:rgba(255,255,255,0.6);text-decoration:none;font-size:13px;display:flex;align-items:center;gap:6px;transition:color 0.2s;}
.back-link:hover{color:white;}
.hero-img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;background:#EEE;max-height:520px;}
.article-wrap{max-width:720px;margin:0 auto;padding:40px 24px 80px;}
.article-meta{display:flex;align-items:center;gap:12px;margin-bottom:20px;flex-wrap:wrap;}
.cat-badge{background:var(--accent);color:white;font-size:11px;font-weight:700;letter-spacing:0.8px;padding:3px 10px;border-radius:12px;}
.meta-date{font-size:13px;color:var(--text-light);}
h1{font-family:"Noto Serif TC",serif;font-size:clamp(22px,4vw,32px);font-weight:700;line-height:1.4;letter-spacing:0.5px;margin-bottom:28px;}
.article-body{font-size:17px;line-height:2;color:var(--text);}
.article-body p{margin-bottom:1.4em;}
.article-body h3{font-family:"Noto Serif TC",serif;font-size:19px;font-weight:700;margin:2em 0 0.8em;border-left:4px solid var(--accent);padding-left:12px;}
.article-body .qa-q{background:#FDF0E8;border-left:4px solid var(--accent);padding:12px 16px;margin-bottom:0.6em;border-radius:0 8px 8px 0;font-weight:700;color:var(--accent);}
.article-body .qa-a{background:#FAFAF8;border-left:4px solid #CCC;padding:12px 16px;margin-bottom:1.4em;border-radius:0 8px 8px 0;}
.article-body iframe{width:100%;aspect-ratio:16/9;border:none;margin:1.5em 0;border-radius:8px;}
.article-img{margin:2em 0;}
.article-img img{width:100%;border-radius:12px;display:block;}
footer{background:#1A1814;color:rgba(255,255,255,0.5);text-align:center;padding:28px 24px;font-size:13px;line-height:2;}
footer a{color:var(--accent);text-decoration:none;}
@media(max-width:600px){.article-wrap{padding:28px 16px 60px;}}
</style>'''

    parts = [
        '<!DOCTYPE html>\n<html lang="zh-Hant">\n<head>',
        STATIC_HEAD,
        f'<title>{title} | IC 觀點</title>',
        f'<meta name="description" content="{og_desc}">',
        f'<link rel="canonical" href="https://ichentsaitw.github.io/ic-blog/posts/{slug}.html">',
        f'<meta property="og:title" content="{title}">',
        f'<meta property="og:description" content="{og_desc}">',
        f'<meta property="og:url" content="https://ichentsaitw.github.io/ic-blog/posts/{slug}.html">',
        f'<meta property="og:image" content="{og_img_url}">',
        f'<meta property="article:published_time" content="{date_str}">',
        f'<script type="application/ld+json">{ld_json}</script>',
        STATIC_CSS,
        '</head>\n<body>',
        '<header><div class="hinner">',
        '<a href="../index.html" class="logo"><div class="logo-icon">IC</div><span class="logo-text">IC 觀點</span></a>',
        '<a href="../index.html" class="back-link">← 所有文章</a>',
        '</div></header>',
        hero_html,
        '<article class="article-wrap">',
        f'<div class="article-meta"><span class="cat-badge">{category}</span><span class="meta-date">{date_str}</span></div>',
        f'<h1>{title}</h1>',
        '<div class="article-body">',
        content_html,
        extra_imgs_html,
        '</div></article>',
        '<footer><p>IC 觀點 · 蔡依橙的個人部落格</p>',
        '<p><a href="https://ichentsaitw.github.io/ic-lab/" target="_blank" rel="noopener">← 回到 IC-LAB</a></p></footer>',
        '</body>\n</html>'
    ]
    return '\n'.join(parts)

posts_index = []
generated = 0

for folder_name, meta in ARTICLES_META.items():
    slug = meta["slug"]
    category = meta["category"]
    src_folder = os.path.join(BASE_SRC, folder_name)
    date_raw = folder_name[:8]
    date_str = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:8]}"

    if not os.path.isdir(src_folder):
        print(f"SKIP (no folder): {folder_name}")
        continue

    # === Dunhuang: image-only post ===
    if slug == "dunhuang-spaceship":
        img_src = os.path.join(src_folder, "blog")
        img_dir = os.path.join(BASE_DST, "posts", "images", slug)
        os.makedirs(img_dir, exist_ok=True)
        imgs = sorted(f for f in os.listdir(img_src) if f.lower().endswith(('.jpg','.jpeg','.png')))
        for f in imgs:
            shutil.copy2(os.path.join(img_src, f), os.path.join(img_dir, f))
        cover = imgs[0] if imgs else ""
        img_html = "\n".join(
            f'<figure class="article-img"><img src="images/{slug}/{f}" alt="敦煌壁畫" loading="lazy"></figure>'
            for f in imgs
        )
        title = "敦煌壁畫中的太空船"
        excerpt = "敦煌壁畫中，有沒有太空船？這個問題引發了許多有趣的討論。透過一系列圖文，重新認識這個考古與想像力之間的話題。"
        reading_time = max(3, len(imgs))
        html = make_post_html(title, date_str, category, slug, cover, img_html, excerpt, [])
        with open(os.path.join(BASE_DST, "posts", f"{slug}.html"), "w", encoding="utf-8") as fout:
            fout.write(html)
        posts_index.append({"slug": slug, "title": title, "category": category, "date": date_str,
                            "excerpt": excerpt, "image": f"posts/images/{slug}/{cover}", "readingTime": reading_time})
        print(f"OK (image-post): {folder_name} ({len(imgs)} images)")
        generated += 1
        continue

    # === Empty folder ===
    if slug == "extreme-return":
        print(f"SKIP (empty): {folder_name}")
        continue

    # === Normal: find docx ===
    docx_path = None
    for f in os.listdir(src_folder):
        if f.endswith('.docx'):
            docx_path = os.path.join(src_folder, f)
            break
    if not docx_path:
        print(f"SKIP (no docx): {folder_name}")
        continue

    try:
        paras = read_docx_paragraphs(docx_path)
    except Exception as e:
        print(f"ERROR: {folder_name}: {e}")
        continue

    title = paras[0][0] if paras else folder_name
    excerpt = get_excerpt(paras)
    reading_time = max(3, len(''.join(p[0] for p in paras)) // 300)
    imgs = copy_images(src_folder, slug)
    cover_img = imgs[0] if imgs else ""
    extra_imgs = imgs[1:] if len(imgs) > 1 else []
    content_html = paras_to_html(paras)
    html = make_post_html(title, date_str, category, slug, cover_img, content_html, excerpt, extra_imgs)
    with open(os.path.join(BASE_DST, "posts", f"{slug}.html"), "w", encoding="utf-8") as fout:
        fout.write(html)
    posts_index.append({
        "slug": slug, "title": title, "category": category, "date": date_str,
        "excerpt": excerpt, "image": f"posts/images/{slug}/{cover_img}" if cover_img else "",
        "readingTime": reading_time
    })
    print(f"OK: {folder_name} ({len(paras)} paras, {len(imgs)} imgs)")
    generated += 1

posts_index.sort(key=lambda x: x["date"], reverse=True)
data_json = {
    "categories": ["全部", "閱讀筆記", "教養思考", "時事觀點", "醫療教育", "生活健康"],
    "posts": posts_index
}
with open(os.path.join(BASE_DST, "posts", "data.json"), "w", encoding="utf-8") as fout:
    json.dump(data_json, fout, ensure_ascii=False, indent=2)

print(f"\nDone: {generated} posts generated, data.json with {len(posts_index)} entries")
