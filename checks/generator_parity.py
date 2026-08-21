#!/usr/bin/env python3
"""같은 사실을 두 곳에서 짓고 있을 때, 둘이 갈렸는지 본다.

한 프로젝트에 같은 데이터를 내는 생성기가 둘 생기는 것은 흔하다.
하나는 API 응답을, 하나는 페이지 <head> 를, 하나는 사이트맵을 짓는다.
문제는 **한쪽만 고쳐도 아무도 알려주지 않는다**는 것이다.
고친 쪽만 보고 "반영됐다"고 결론짓고, 다른 표면은 조용히 낡는다.

    checks/generator_parity.py a.json b.json --path 'person.sameAs'
    checks/generator_parity.py a.json b.json --path '@graph[*].url' --path 'id'

경로 문법 (JSONPath 아님 — 필요한 만큼만):
    a.b.c        중첩 키
    a[0].b       배열 인덱스
    a[*].b       배열 전체를 훑어 b 를 모은다
    a[?type=X].b type 이 X 인 원소만

종료 코드 1 = 갈렸다.
"""
import argparse
import json
import re
import sys

_SEG = re.compile(r"([^.\[\]]+)|\[(\*|\d+|\?[^\]]+)\]")


def select(node, path):
    """경로를 따라 값을 모은다. 항상 리스트를 낸다."""
    cur = [node]
    for key, idx in _SEG.findall(path):
        nxt = []
        for c in cur:
            if key:
                if isinstance(c, dict) and key in c:
                    nxt.append(c[key])
            elif idx == "*":
                if isinstance(c, list):
                    nxt.extend(c)
            elif idx.startswith("?"):
                k, _, v = idx[1:].partition("=")
                if isinstance(c, list):
                    nxt.extend(x for x in c if isinstance(x, dict) and str(x.get(k)) == v)
            elif isinstance(c, list) and int(idx) < len(c):
                nxt.append(c[int(idx)])
        cur = nxt
    return cur


def norm(vals):
    """비교용 정규화. 순서 차이는 갈림이 아니다 — 내용 차이만 본다."""
    out = []
    for v in vals:
        out.append(json.dumps(v, ensure_ascii=False, sort_keys=True)
                   if isinstance(v, (dict, list)) else v)
    return sorted(out, key=str)


def main():
    ap = argparse.ArgumentParser(description="두 생성기의 산출물이 갈렸는지 본다")
    ap.add_argument("files", nargs="+", help="비교할 JSON 파일 둘 이상")
    ap.add_argument("--path", action="append", required=True,
                    help="대조할 경로. 여러 번 쓸 수 있다")
    ap.add_argument("--label", action="append", default=[],
                    help="파일 표시 이름 (없으면 경로를 쓴다)")
    a = ap.parse_args()

    if len(a.files) < 2:
        print("파일이 둘 이상이어야 한다", file=sys.stderr)
        return 2
    labels = a.label + a.files[len(a.label):]

    docs = []
    for f in a.files:
        try:
            docs.append(json.load(open(f, encoding="utf-8")))
        except Exception as e:
            print(f"{f} 를 읽지 못했다: {e}", file=sys.stderr)
            return 2

    bad = 0
    for path in a.path:
        got = [norm(select(d, path)) for d in docs]
        if all(g == got[0] for g in got):
            continue
        bad += 1
        print(f"✖ {path} 가 갈렸다")
        base = set(map(str, got[0]))
        for lb, g in zip(labels, got):
            g_set = set(map(str, g))
            mark = "" if g_set == base else "  ←"
            print(f"    {lb}: 선택 {len(g)}건{mark}")
            for only in sorted(g_set - base)[:5]:
                print(f"        + {only[:100]}")
            for miss in sorted(base - g_set)[:5]:
                print(f"        - {miss[:100]}")

    if bad:
        print(f"\n갈린 경로 {bad}개 — 한쪽만 고쳤을 것이다", file=sys.stderr)
        return 1
    print(f"✓ 경로 {len(a.path)}개가 파일 {len(a.files)}개에서 일치")
    return 0


if __name__ == "__main__":
    sys.exit(main())
