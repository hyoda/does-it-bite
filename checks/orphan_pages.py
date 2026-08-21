#!/usr/bin/env python3
"""링크 없는 페이지를 찾는다. **링크 없는 페이지는 없는 페이지다.**

사이트맵에 실려 있으면 기계는 찾는다. 사람은 못 찾는다.
그 둘을 같은 것으로 착각하면, 만들어서 배포까지 한 페이지가 아무에게도 안 닿는다.

    checks/orphan_pages.py dist/ --entry index.html
    checks/orphan_pages.py dist/ --ignore '404/*' --ignore 'draft/*'

종료 코드 1 = 고아가 있다.
"""
import argparse
import fnmatch
import os
import re
import sys


def page_url(path, root, index_name):
    """파일 경로 → 사이트 내 URL. dist/a/index.html → /a/"""
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    if rel.endswith("/" + index_name):
        rel = rel[: -len(index_name)]
    elif rel == index_name:
        rel = ""
    return "/" + rel


def main():
    ap = argparse.ArgumentParser(description="링크 없는 페이지를 찾는다")
    ap.add_argument("root", help="배포 디렉토리")
    ap.add_argument("--entry", default="index.html",
                    help="디렉토리 인덱스 파일명 (기본 index.html)")
    ap.add_argument("--ignore", action="append", default=[],
                    help="검사에서 뺄 URL 글롭. 여러 번 쓸 수 있다")
    ap.add_argument("--min", type=int, default=1,
                    help="필요한 최소 인바운드 수 (기본 1)")
    a = ap.parse_args()

    files = [os.path.join(dp, f)
             for dp, _, fs in os.walk(a.root)
             for f in fs if f.endswith((".html", ".htm"))]
    if not files:
        print(f"{a.root} 에 HTML 이 없다", file=sys.stderr)
        return 2

    bodies = {f: open(f, encoding="utf-8", errors="replace").read() for f in files}
    pages = {f: page_url(f, a.root, a.entry) for f in files}

    orphans = []
    for f, url in sorted(pages.items(), key=lambda kv: kv[1]):
        # 루트는 진입점이라 인바운드가 없어도 된다.
        if url == "/":
            continue
        # 사람은 'draft', 'draft/', 'draft/*' 를 다 같은 뜻으로 쓴다. 셋 다 받는다 —
        # 안 받으면 "뺐는데 왜 걸리지" 로 시간을 버리고, 결국 검사를 끄게 된다.
        bare = url.strip("/")
        if any(fnmatch.fnmatch(bare, pat.strip("/").rstrip("*").rstrip("/") or "*")
               or fnmatch.fnmatch(bare, pat.strip("/"))
               for pat in a.ignore):
            continue
        # 자기 자신에서 온 링크는 세지 않는다 — 스스로를 가리키는 건 들어오는 길이 아니다.
        n = sum(1 for g, body in bodies.items()
                if pages[g] != url and re.search(r'href="%s"' % re.escape(url), body))
        if n < a.min:
            orphans.append((url, n))

    for url, n in orphans:
        print(f"{url} — 인바운드 {n} (필요 {a.min})")
    if orphans:
        print(f"\n고아 {len(orphans)}개 / 전체 {len(pages)}개", file=sys.stderr)
        return 1
    print(f"✓ 페이지 {len(pages)}개 전부 들어오는 길이 있다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
