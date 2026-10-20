"""Build the Absent Brethren site from _source/posts.json.

Writes the finished pages into the repository root, which GitHub Pages serves:
  index.html            the latest update in full, then recent ones
  updates/index.html    every update, by month
  post/<slug>/          one page per update (same addresses as the old Wix blog)
Links are relative, so the site works at any address.

Usage: python3 -I _source/build.py
"""
import html
import json
import re
import shutil
from datetime import date
from pathlib import Path

SRC = Path(__file__).resolve().parent
OUT = SRC.parent
SITE = "Absent Brethren"
MOTTO = "News from home for the brethren away"
RECENT = 6  # earlier updates listed under the featured one on the home page


def load_posts():
    posts = json.loads((SRC / "posts.json").read_text())
    for p in posts:
        p["day"] = date.fromisoformat(p["date"])
    return sorted(posts, key=lambda p: p["day"], reverse=True)


def long_date(d):
    return f"{d:%A}, {d:%B} {d.day}, {d.year}"


def gist(p, words=28):
    text = html.unescape(re.sub(r"<[^>]+>", " ", p["html"]))
    text = " ".join(text.split()).split(" ")
    return " ".join(text[:words]) + ("…" if len(text) > words else "")


def page(title, body, root, current=""):
    def nav_link(href, label, key):
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{root}{href}"{cur}>{label}</a>'

    full_title = SITE if not title else f"{title} · {SITE}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{html.escape(full_title)}</title>
<link rel="stylesheet" href="{root}style.css">
</head>
<body>
<header class="mast wrap">
  <span class="cross" aria-hidden="true">✠</span>
  <a class="name" href="{root}">{SITE}</a>
  <p class="motto">{MOTTO}</p>
  <nav aria-label="Main">
    {nav_link("", "Latest", "home")}
    {nav_link("updates/", "All updates", "updates")}
  </nav>
</header>
<div class="orn wrap" aria-hidden="true">✠</div>
<main class="wrap">
{body}
</main>
<footer class="wrap"><span class="cross" aria-hidden="true">✠</span> Ut in omnibus glorificetur Deus</footer>
</body>
</html>
"""


def article(p, root, heading="h1", link=False, initial=False):
    title = html.escape(p["title"])
    if link:
        title = f'<a href="{root}post/{p["slug"]}/">{title}</a>'
    cls = "body initial" if initial else "body"
    return f"""<{heading} class="title">{title}</{heading}>
<p class="date">{long_date(p["day"])}</p>
<div class="{cls}">
{p["html"]}
</div>"""


def item(p, root):
    return f"""<li><a href="{root}post/{p["slug"]}/">{html.escape(p["title"])}</a>
<span class="when">{long_date(p["day"])}</span>
<span class="gist">{html.escape(gist(p))}</span></li>"""


def home(posts):
    root = ""
    latest, rest = posts[0], posts[1:RECENT + 1]
    body = f"""<article class="leaf">
<p class="label">Latest update</p>
{article(latest, root, heading="h2", link=True, initial=True)}
</article>
<section class="leaf" aria-labelledby="recent">
<p class="label" id="recent">Earlier updates</p>
<ul class="list">
{"".join(item(p, root) for p in rest)}
</ul>
<p class="more"><a href="updates/">All {len(posts)} updates →</a></p>
</section>"""
    return page("", body, root, "home")


def updates(posts):
    root = "../"
    months = {}
    for p in posts:
        months.setdefault(f"{p['day']:%B %Y}", []).append(p)
    jump = " ".join(f'<a href="#{m.replace(" ", "-").lower()}">{m}</a>' for m in months)
    groups = "".join(
        f"""<h2 class="month" id="{m.replace(" ", "-").lower()}">{m}</h2>
<ul class="list">{"".join(item(p, root) for p in ps)}</ul>"""
        for m, ps in months.items()
    )
    body = f"""<section class="leaf">
<h1>All updates</h1>
<p class="date">{len(posts)} updates, newest first</p>
<nav class="months" aria-label="Months">{jump}</nav>
{groups}
</section>"""
    return page("All updates", body, root, "updates")


def post(p, newer, older):
    root = "../../"
    links = ""
    if older:
        links += f'<a class="prev" href="{root}post/{older["slug"]}/"><span class="dir">← Earlier</span>{html.escape(older["title"])}</a>'
    if newer:
        links += f'<a class="next" href="{root}post/{newer["slug"]}/"><span class="dir">Later →</span>{html.escape(newer["title"])}</a>'
    body = f"""<article class="leaf">
{article(p, root, initial=True)}
<nav class="pager" aria-label="More updates">{links}</nav>
</article>
<p class="more" style="text-align:center"><a href="{root}updates/">All updates</a></p>"""
    return page(p["title"], body, root)


def not_found():
    # GitHub Pages serves this for any unknown address, at that address, so links are absolute.
    root = "/absentbrethren/"
    body = """<section class="leaf" style="text-align:center">
<h1>Page not found</h1>
<p>That page isn't here. Try the <a href="/absentbrethren/">latest update</a> or <a href="/absentbrethren/updates/">all updates</a>.</p>
</section>"""
    return page("Page not found", body, root)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def main():
    posts = load_posts()
    if (OUT / "post").exists():
        shutil.rmtree(OUT / "post")
    write(OUT / "index.html", home(posts))
    write(OUT / "updates" / "index.html", updates(posts))
    for i, p in enumerate(posts):
        newer = posts[i - 1] if i > 0 else None
        older = posts[i + 1] if i + 1 < len(posts) else None
        write(OUT / "post" / p["slug"] / "index.html", post(p, newer, older))
    write(OUT / "404.html", not_found())
    shutil.copy(SRC / "style.css", OUT / "style.css")
    write(OUT / "robots.txt", "User-agent: *\nDisallow: /\n")
    write(OUT / ".nojekyll", "")
    print(f"Built {len(posts)} updates.")


if __name__ == "__main__":
    main()
