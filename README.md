# Absent Brethren

News from home for the brethren away, served with GitHub Pages at
https://munkachy.github.io/absentbrethren/

The pages are built from `_source/posts.json` by `_source/build.py`:

    python3 -I _source/build.py

To add an update, add an entry to the top of `_source/posts.json`
(`slug`, `title`, `date` as YYYY-MM-DD, `html`), rebuild, and commit.
The site asks search engines not to list it (`robots.txt` and a
`noindex` tag on every page).
