import docx, os, json, shutil, re, sys
from docx.oxml.ns import qn
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

BUILD_DATE = datetime.now().strftime('%Y-%m-%d')

BASE_SRC = r"C:\Users\silly\新思惟國際 Dropbox\Tsai I-Chen\!!00IC_documents\ClaudeCowork\blog-test"
BASE_DST = r"C:\Users\silly\projects\ic-blog"

os.makedirs(os.path.join(BASE_DST, "posts", "images"), exist_ok=True)

ARTICLES_META = {
    "20220717_安倍晉三大戰略": {
        "slug": "abe-grand-strategy", "category": "閱讀筆記",
        "keywords": "安倍晉三,日本政治,大戰略,國際關係,台日關係,印太戰略,書評,閱讀筆記,蔡依橙"
    },
    "20220721_統合心智": {
        "slug": "synthesizing-mind", "category": "閱讀筆記",
        "keywords": "統合心智,多元智能,加德納,Howard Gardner,教育心理學,書評,孩子才華,閱讀筆記,蔡依橙"
    },
    "20220901_不想念中國史中國地理": {
        "slug": "history-geography-school", "category": "教養思考",
        "keywords": "中國歷史,中國地理,課綱,國中社會,教養,孩子教育,108課綱,蔡依橙"
    },
    "20220910_解決問題的能力": {
        "slug": "problem-solving-skill", "category": "教養思考",
        "keywords": "解決問題,Problem Solving,數位能力,孩子教育,教養思考,Word,PowerPoint,蔡依橙"
    },
    "20220910_關於北歐教養的一些想法": {
        "slug": "nordic-parenting", "category": "教養思考",
        "keywords": "北歐教養,丹麥教育,教養觀念,親子教育,教育比較,蔡依橙"
    },
    "20220927_中華民國4.0": {
        "slug": "roc-4", "category": "時事觀點",
        "keywords": "中華民國,台灣,國際新聞,忒修斯之船,國家認同,歷史觀,蔡依橙"
    },
    "20221018_是的我去做老花雷射LBV了": {
        "slug": "lbv-laser-experience", "category": "生活健康",
        "keywords": "老花雷射,Presbyond LBV,LASIK,近視雷射,遠見眼科,張聰麒,老花眼,醫療經驗,蔡依橙"
    },
    "20221023_敦煌壁畫中的太空船": {
        "slug": "dunhuang-spaceship", "category": "時事觀點",
        "keywords": "敦煌壁畫,太空船,考古,歷史,圖文分析,蔡依橙"
    },
    "20221120_李紹榕主編的書": {
        "slug": "li-shaorong-book", "category": "閱讀筆記",
        "keywords": "放射科醫師,新思惟國際,醫師職涯,創業,離開醫院,住院醫師,論文發表,蔡依橙"
    },
    "20221209_那些散落的星星": {
        "slug": "scattered-stars", "category": "閱讀筆記",
        "keywords": "那些散落的星星,讀後心得,難民,閱讀討論,親子共讀,蔡依橙"
    },
    "20221225_極限返航": {
        "slug": "extreme-return", "category": "閱讀筆記",
        "keywords": "極限返航,書評,閱讀筆記,蔡依橙"
    },
    "20230214_關於應徵住院醫師的一些資訊": {
        "slug": "resident-application-info", "category": "醫療教育",
        "keywords": "住院醫師,PGY,應徵,醫師求職,論文,醫學教育,熱門科別,蔡依橙"
    },
    "20230222_科部團隊問題": {
        "slug": "department-team-issues", "category": "醫療教育",
        "keywords": "醫院管理,科部經營,團隊合作,主治醫師,職場問題,醫療職場,蔡依橙"
    },
    "20230310_翰林雲端學院": {
        "slug": "hanlin-online-school", "category": "教養思考",
        "keywords": "翰林雲端學院,線上學習,國中課業,補習,自主學習,家長經驗,成績,蔡依橙"
    },
    "20230313_與成功有約最後一堂課": {
        "slug": "7-habits-last-lesson", "category": "閱讀筆記",
        "keywords": "與成功有約,七個習慣,史蒂芬柯維,中年危機,人生意義,書評,蔡依橙"
    },
    "20230705_AI時代的創意教養": {
        "slug": "ai-era-creative-parenting", "category": "教養思考",
        "keywords": "AI教育,創意教養,3C教養,人工智慧,孩子未來,推薦序,蔡依橙"
    },
    "20230902_黑熊學院藍鵲行動": {
        "slug": "black-bear-academy", "category": "時事觀點",
        "keywords": "黑熊學院,藍鵲行動,民防,防災演練,台灣安全,戰時準備,EDC,蔡依橙"
    },
    "20250210_VEX家長": {
        "slug": "vex-parent-questions", "category": "教養思考",
        "keywords": "VEX機器人,VEX IQ,VEX V5,機器人競賽,STEM教育,親子教育,家長經驗,蔡依橙"
    },
}

def read_docx_content(path):
    """Return list of content items: ('text', text, is_bold) or ('image', img_index).
    img_index is 0-based, matching the order images appear in the Word file,
    which corresponds to sorted folder images."""
    d = docx.Document(path)
    result = []
    img_counter = 0

    for p in d.paragraphs:
        text = p.text.strip()

        # Check for embedded images in this paragraph
        blips = p._element.findall('.//' + qn('a:blip'))
        if blips:
            for _ in blips:
                result.append(('image', img_counter))
                img_counter += 1

        if not text:
            continue

        # Check if paragraph is bold
        is_heading = 'Heading' in (p.style.name if p.style else '')
        runs_with_text = [r for r in p.runs if r.text.strip()]
        is_bold = all(r.bold for r in runs_with_text) if runs_with_text else False
        result.append(('text', text, is_bold or is_heading))

    return result

def content_to_html(content_items, slug, folder_imgs):
    """Convert content items to HTML, inserting images at their original positions.
    folder_imgs is the sorted list of image filenames in the folder.
    The first image is used as hero/cover, so inline images skip index 0."""
    parts = []
    text_idx = 0  # track which text paragraph we're on

    for item in content_items:
        if item[0] == 'image':
            img_idx = item[1]
            if img_idx < len(folder_imgs):
                img_file = folder_imgs[img_idx]
                # Skip the cover image (index 0) since it's shown as hero
                if img_idx > 0:
                    parts.append(f'<figure class="article-img"><img src="images/{slug}/{img_file}" alt="" loading="lazy"></figure>')
            continue

        # Text paragraph
        _, p, is_bold = item

        # Skip title (first text para) and author line
        if text_idx == 0:
            text_idx += 1
            continue
        if re.match(r'^(作者|讀者|Author)[:：]', p):
            text_idx += 1
            continue

        if p.startswith('<iframe'):
            parts.append(p)
        elif p.startswith('問：') or p.startswith('問:'):
            parts.append(f'<p class="qa-q">{p}</p>')
        elif (p.startswith('答：') or p.startswith('答:')) and is_bold:
            parts.append(f'<p class="qa-a"><strong>{p}</strong></p>')
        elif is_bold and text_idx > 0:
            parts.append(f'<h3>{p}</h3>')
        else:
            parts.append(f'<p>{p}</p>')

        text_idx += 1

    return '\n'.join(parts)

def get_excerpt(content_items):
    """Extract excerpt from content items, skipping title, author, bold headings, images."""
    skip = [r'^(作者|讀者)[:：]', r'^[（(]', r'^http', r'^<iframe']
    found_title = False
    for item in content_items:
        if item[0] != 'text':
            continue
        _, p_text, is_bold = item
        if not found_title:
            found_title = True
            continue  # skip title
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

def make_post_html(title, date_str, category, slug, cover_img, content_html, excerpt, extra_imgs, keywords=""):
    og_desc = excerpt.replace('"', '&quot;').replace("'", "&#39;")
    cover_url = f"images/{slug}/{cover_img}" if cover_img else ""
    og_img_url = f"https://ichentsaitw.github.io/ic-blog/posts/images/{slug}/{cover_img}" if cover_img else ""

    extra_imgs_html = ""
    for img in extra_imgs:
        extra_imgs_html += f'<figure class="article-img"><img src="images/{slug}/{img}" alt="" loading="lazy"></figure>\n'

    hero_html = f'<img class="hero-img" src="{cover_url}" alt="{title}">' if cover_img else ''

    # Article structured data with image
    ld_article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": excerpt,
        "datePublished": date_str,
        "dateModified": date_str,
        "author": {"@type": "Person", "name": "蔡依橙", "url": "https://ichentsaitw.github.io/ic-lab/"},
        "publisher": {"@type": "Organization", "name": "IC 觀點", "url": "https://ichentsaitw.github.io/ic-blog/"},
        "url": f"https://ichentsaitw.github.io/ic-blog/posts/{slug}.html",
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"https://ichentsaitw.github.io/ic-blog/posts/{slug}.html"},
        "articleSection": category,
        "inLanguage": "zh-TW"
    }
    if og_img_url:
        ld_article["image"] = {"@type": "ImageObject", "url": og_img_url}
    if keywords:
        ld_article["keywords"] = keywords

    # Breadcrumb structured data
    ld_breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "IC 觀點", "item": "https://ichentsaitw.github.io/ic-blog/"},
            {"@type": "ListItem", "position": 2, "name": category, "item": f"https://ichentsaitw.github.io/ic-blog/#cat-{category}"},
            {"@type": "ListItem", "position": 3, "name": title}
        ]
    }

    ld_json_str = json.dumps(ld_article, ensure_ascii=False)
    ld_bread_str = json.dumps(ld_breadcrumb, ensure_ascii=False)

    STATIC_HEAD = '''<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="author" content="蔡依橙">
<meta name="robots" content="index, follow">
<meta property="og:type" content="article">
<meta property="og:locale" content="zh_TW">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@ichentsai">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='18' fill='%23C8602A'/%3E%3Ctext x='50' y='56' text-anchor='middle' dominant-baseline='central' font-family='serif' font-weight='bold' font-size='52' fill='white'%3EIC%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@600;700&display=swap" rel="stylesheet">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4ZR4LYRZ7B"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag("js",new Date());gtag("config","G-4ZR4LYRZ7B");</script>'''

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
.related{margin-top:3em;padding-top:2em;border-top:2px solid var(--border);}
.related h2{font-family:"Noto Serif TC",serif;font-size:18px;font-weight:700;margin-bottom:16px;color:var(--text);}
.related-list{display:grid;gap:12px;}
.related-link{display:flex;gap:12px;text-decoration:none;color:inherit;padding:12px;border-radius:10px;border:1px solid var(--border);transition:all 0.2s;}
.related-link:hover{border-color:var(--accent);background:var(--accent-light,#FDF0E8);}
.related-link img{width:120px;height:68px;object-fit:cover;border-radius:6px;flex-shrink:0;}
.related-link .rl-text{display:flex;flex-direction:column;gap:4px;}
.related-link .rl-cat{font-size:11px;color:var(--accent);font-weight:700;}
.related-link .rl-title{font-size:15px;font-weight:500;line-height:1.4;}
@media(max-width:600px){.article-wrap{padding:28px 16px 60px;}.related-link img{width:80px;height:45px;}}
</style>'''

    keywords_meta = f'\n<meta name="keywords" content="{keywords}">' if keywords else ''

    parts = [
        '<!DOCTYPE html>\n<html lang="zh-Hant">\n<head>',
        STATIC_HEAD,
        f'<title>{title} | IC 觀點</title>',
        f'<meta name="description" content="{og_desc}">',
        keywords_meta,
        f'<link rel="canonical" href="https://ichentsaitw.github.io/ic-blog/posts/{slug}.html">',
        f'<link rel="alternate" type="application/rss+xml" title="IC 觀點" href="https://ichentsaitw.github.io/ic-blog/feed.xml">',
        f'<meta property="og:title" content="{title}">',
        f'<meta property="og:description" content="{og_desc}">',
        f'<meta property="og:url" content="https://ichentsaitw.github.io/ic-blog/posts/{slug}.html">',
        f'<meta property="og:image" content="{og_img_url}">',
        f'<meta property="og:image:width" content="1200">',
        f'<meta property="og:image:height" content="628">',
        f'<meta name="twitter:image" content="{og_img_url}">',
        f'<meta property="article:published_time" content="{date_str}">',
        f'<script type="application/ld+json">{ld_json_str}</script>',
        f'<script type="application/ld+json">{ld_bread_str}</script>',
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
        '</div>',
        '<!--RELATED_ARTICLES-->',
        '</article>',
        '<footer><p>IC 觀點 · 蔡依橙的個人部落格</p>',
        f'<p style="font-size:12px;color:rgba(255,255,255,0.35);">最後更新：{BUILD_DATE}</p>',
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
        html = make_post_html(title, date_str, category, slug, cover, img_html, excerpt, [], keywords=meta.get("keywords",""))
        with open(os.path.join(BASE_DST, "posts", f"{slug}.html"), "w", encoding="utf-8") as fout:
            fout.write(html)
        posts_index.append({"slug": slug, "title": title, "category": category, "date": date_str,
                            "excerpt": excerpt, "image": f"posts/images/{slug}/{cover}", "readingTime": reading_time})
        print(f"OK (image-post): {folder_name} ({len(imgs)} images)")
        generated += 1
        continue

    # === scattered-stars: no images in folder, use pre-existing cover ===
    if slug == "scattered-stars":
        # Cover image already exists at posts/images/scattered-stars/cover.jpg (downloaded from Unsplash)
        cover_path = os.path.join(BASE_DST, "posts", "images", slug, "cover.jpg")
        if os.path.exists(cover_path):
            pass  # keep existing cover
        # Process docx normally but with this cover
        docx_path = None
        for f in os.listdir(src_folder):
            if f.endswith('.docx'):
                docx_path = os.path.join(src_folder, f)
                break
        if docx_path:
            content_items = read_docx_content(docx_path)
            title = "那些散落的星星 讀後討論"
            excerpt = get_excerpt(content_items)
            all_text = ''.join(item[1] for item in content_items if item[0] == 'text')
            reading_time = max(3, len(all_text) // 300)
            content_html = content_to_html(content_items, slug, [])
            html = make_post_html(title, date_str, category, slug, "cover.jpg", content_html, excerpt, [], keywords=meta.get("keywords",""))
            with open(os.path.join(BASE_DST, "posts", f"{slug}.html"), "w", encoding="utf-8") as fout:
                fout.write(html)
            posts_index.append({
                "slug": slug, "title": title, "category": category, "date": date_str,
                "excerpt": excerpt, "image": f"posts/images/{slug}/cover.jpg", "readingTime": reading_time
            })
            print(f"OK (special-cover): {folder_name}")
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
        content_items = read_docx_content(docx_path)
    except Exception as e:
        print(f"ERROR: {folder_name}: {e}")
        continue

    # Extract title from first text item
    title = folder_name
    for item in content_items:
        if item[0] == 'text':
            title = item[1]
            break
    excerpt = get_excerpt(content_items)
    all_text = ''.join(item[1] for item in content_items if item[0] == 'text')
    reading_time = max(3, len(all_text) // 300)
    imgs = copy_images(src_folder, slug)
    cover_img = imgs[0] if imgs else ""
    # Images are now inlined by content_to_html, no extra_imgs needed
    content_html = content_to_html(content_items, slug, imgs)

    # VEX article: images not embedded in Word, manually distribute across sections
    if slug == "vex-parent-questions" and len(imgs) > 1:
        # Insert images between paragraphs (use full closing/opening tags as markers)
        vex_img_insertions = [
            ('與全世界高手同場競技。</p>', imgs[3] if len(imgs)>3 else None),
            ('只能打 support。</p>', imgs[4] if len(imgs)>4 else None),
            ('這樣的經驗，最是難得。</p>', imgs[2] if len(imgs)>2 else None),
            ('走得更遠。</p>', imgs[5] if len(imgs)>5 else None),
            ('配到更好的隊伍。</p>', imgs[6] if len(imgs)>6 else None),
            ('非常有意思。</p>', imgs[1] if len(imgs)>1 else None),
        ]
        for marker, img_file in vex_img_insertions:
            if img_file and marker in content_html:
                img_tag = f'\n<figure class="article-img"><img src="images/{slug}/{img_file}" alt="" loading="lazy"></figure>'
                content_html = content_html.replace(marker, marker + img_tag, 1)

    html = make_post_html(title, date_str, category, slug, cover_img, content_html, excerpt, [], keywords=meta.get("keywords",""))
    with open(os.path.join(BASE_DST, "posts", f"{slug}.html"), "w", encoding="utf-8") as fout:
        fout.write(html)
    posts_index.append({
        "slug": slug, "title": title, "category": category, "date": date_str,
        "excerpt": excerpt, "image": f"posts/images/{slug}/{cover_img}" if cover_img else "",
        "readingTime": reading_time
    })
    print(f"OK: {folder_name} ({len(content_items)} items, {len(imgs)} imgs)")
    generated += 1

posts_index.sort(key=lambda x: x["date"], reverse=True)
data_json = {
    "categories": ["全部", "閱讀筆記", "教養思考", "時事觀點", "醫療教育", "生活健康"],
    "posts": posts_index
}
with open(os.path.join(BASE_DST, "posts", "data.json"), "w", encoding="utf-8") as fout:
    json.dump(data_json, fout, ensure_ascii=False, indent=2)

# === Second pass: inject related articles into each post ===
print("\nInjecting related articles...")
for post in posts_index:
    # Find related: same category first, then recent, exclude self, max 3
    same_cat = [p for p in posts_index if p["category"] == post["category"] and p["slug"] != post["slug"]]
    others = [p for p in posts_index if p["category"] != post["category"] and p["slug"] != post["slug"]]
    related = same_cat[:2] + others[:1] if len(same_cat) >= 2 else same_cat + others[:3-len(same_cat)]
    related = related[:3]

    if not related:
        continue

    links_html = []
    for r in related:
        r_title = r["title"].replace('"', '&quot;')
        r_img = f'../{r["image"]}' if r.get("image") else ''
        img_tag = f'<img src="{r_img}" alt="{r_title}" loading="lazy">' if r_img else ''
        links_html.append(
            f'<a href="{r["slug"]}.html" class="related-link">'
            f'{img_tag}'
            f'<div class="rl-text"><span class="rl-cat">{r["category"]}</span>'
            f'<span class="rl-title">{r["title"]}</span></div></a>'
        )

    related_section = (
        '<div class="related"><h2>相關閱讀</h2>'
        '<div class="related-list">' + '\n'.join(links_html) + '</div></div>'
    )

    post_path = os.path.join(BASE_DST, "posts", f"{post['slug']}.html")
    with open(post_path, "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace('<!--RELATED_ARTICLES-->', related_section)
    with open(post_path, "w", encoding="utf-8") as f:
        f.write(html)

print(f"Related articles injected into {len(posts_index)} posts")

print(f"\nDone: {generated} posts generated, data.json with {len(posts_index)} entries")

# Generate RSS feed
from xml.sax.saxutils import escape
rss_items = []
for post in posts_index[:20]:
    rss_items.append(f"""  <item>
    <title>{escape(post['title'])}</title>
    <link>https://ichentsaitw.github.io/ic-blog/posts/{post['slug']}.html</link>
    <guid>https://ichentsaitw.github.io/ic-blog/posts/{post['slug']}.html</guid>
    <pubDate>{post['date']}</pubDate>
    <description>{escape(post['excerpt'])}</description>
    <category>{escape(post['category'])}</category>
  </item>""")

rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>IC 觀點</title>
  <link>https://ichentsaitw.github.io/ic-blog/</link>
  <description>蔡依橙的個人部落格。關於教養、醫療教育、閱讀與時事的思考紀錄。</description>
  <language>zh-TW</language>
  <atom:link href="https://ichentsaitw.github.io/ic-blog/feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(rss_items)}
</channel>
</rss>"""

with open(os.path.join(BASE_DST, "feed.xml"), "w", encoding="utf-8") as fout:
    fout.write(rss_xml)
print(f"RSS feed generated with {len(rss_items)} items")

# Generate sitemap.xml with changefreq
sitemap_entries = [f"""  <url>
    <loc>https://ichentsaitw.github.io/ic-blog/</loc>
    <lastmod>{BUILD_DATE}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>"""]
for post in posts_index:
    sitemap_entries.append(f"""  <url>
    <loc>https://ichentsaitw.github.io/ic-blog/posts/{post['slug']}.html</loc>
    <lastmod>{post['date']}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.8</priority>
  </url>""")
sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(sitemap_entries) + '\n</urlset>\n'
with open(os.path.join(BASE_DST, "sitemap.xml"), "w", encoding="utf-8") as fout:
    fout.write(sitemap_xml)
print(f"Sitemap generated with {len(sitemap_entries)} URLs")

# === Pre-render article cards into index.html for SEO ===
index_path = os.path.join(BASE_DST, "index.html")
with open(index_path, "r", encoding="utf-8") as f:
    index_html = f.read()

# Build static card HTML for all posts
cards_html_parts = []
for post in posts_index:
    date_parts = post['date'].split('-')
    date_display = f"{date_parts[0]}/{date_parts[1]}/{date_parts[2]}"
    read_min = post.get('readingTime', 5)
    excerpt_safe = post['excerpt'].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    title_safe = post['title'].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    cards_html_parts.append(f'''<a class="article-card" href="posts/{post['slug']}.html" data-category="{post['category']}">
    <div class="card-image-wrap">
      <img src="{post['image']}" alt="{title_safe}" loading="lazy">
      <span class="card-category">{post['category']}</span>
    </div>
    <div class="card-body">
      <div class="card-meta">
        <span class="card-date">{date_display}</span>
        <span class="card-read">{read_min} 分鐘</span>
      </div>
      <div class="card-title">{title_safe}</div>
      <div class="card-excerpt">{excerpt_safe}</div>
      <div class="card-read-more">閱讀全文 →</div>
    </div>
  </a>''')

cards_html = '\n  '.join(cards_html_parts)

# Also pre-render category buttons
cat_list = ["全部", "閱讀筆記", "教養思考", "時事觀點", "醫療教育", "生活健康"]
cat_buttons = '\n    '.join(
    f'<button class="cat-btn{" active" if cat == "全部" else ""}" data-cat="{cat}">{cat}</button>'
    for cat in cat_list
)

# Replace empty grid with pre-rendered cards
index_html = index_html.replace(
    '<div class="articles-grid" id="articlesGrid"></div>',
    f'<div class="articles-grid" id="articlesGrid">\n  {cards_html}\n</div>'
)

# Replace empty category scroll with pre-rendered buttons
index_html = index_html.replace(
    '<div class="category-scroll" id="catScroll">\n    <!-- Populated by JS -->\n  </div>',
    f'<div class="category-scroll" id="catScroll">\n    {cat_buttons}\n  </div>'
)

# Replace empty nav with pre-rendered links
nav_links = '\n      '.join(
    f'<a href="#">{cat}</a>' for cat in cat_list
)
index_html = index_html.replace(
    '<nav class="nav-desktop" id="catNavDesktop">\n      <!-- Populated by JS -->\n    </nav>',
    f'<nav class="nav-desktop" id="catNavDesktop">\n      {nav_links}\n    </nav>'
)

# Update post count
index_html = index_html.replace(
    '<span class="counter-number" id="postCount">—</span>',
    f'<span class="counter-number" id="postCount">{len(posts_index)}</span>'
)

# Update last updated date
index_html = index_html.replace('<!--LAST_UPDATED-->', BUILD_DATE)

with open(index_path, "w", encoding="utf-8") as f:
    f.write(index_html)
print(f"index.html updated with {len(posts_index)} pre-rendered cards")
