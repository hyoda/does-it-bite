#!/usr/bin/env python3
"""문서에 손으로 쓴 수치가 코드와 어긋났는지 본다.

README 의 "검사 21종", 발표자료의 "고객사 18곳", 랜딩의 "리포 40개" —
**손으로 쓴 수치는 반드시 낡는다.** 문제는 낡았다는 걸 아무도 모른다는 것이다.
읽는 사람은 그게 사실인 줄 알고, 쓴 사람은 고친 기억이 없다.

고치는 방법은 수치를 지우는 게 아니라 **표시를 붙이고 대조하는 것**이다:

    회귀 **34항목**<!--N:verify-->  ← 이 34 를 코드에서 세어 대조한다

    checks/doc_drift.py README.md --values counts.json
    checks/doc_drift.py README.md --values-cmd 'scripts/count.sh'

counts.json 은 {"verify": 34, "clients": 20} 같은 평평한 객체다.
`--values-cmd` 는 그 JSON 을 stdout 으로 내는 명령이다 —
**세는 일은 코드가 하고, 문서는 결과만 든다.**

종료 코드 1 = 표류했다.
"""
import argparse
import json
import re
import subprocess
import sys

# 값 바로 뒤에 오는 표시. 값은 숫자이고 사이에 굵게·쉼표·공백이 낄 수 있다.
MARKER = re.compile(r"([\d,]+)\s*[^\n<]{0,12}?<!--\s*N:([A-Za-z0-9_.-]+)\s*-->")

# 펜스 코드 블록. 그 안의 표시는 **문법 설명이지 주장이 아니다** —
# 이 검사기를 자기 README 에 처음 돌렸을 때 문법 예제를 실제 수치로 읽고 거짓 양성을 냈다.
FENCE = re.compile(r"^\s*(```|~~~)", re.M)


def strip_fences(text):
    """펜스 블록을 같은 길이의 공백으로 지운다 — 줄 번호와 위치가 보존된다."""
    out, fence = [], None
    for line in text.splitlines(keepends=True):
        m = FENCE.match(line)
        if m and fence is None:
            fence = m.group(1)
            out.append(" " * len(line))
        elif m and line.strip().startswith(fence):
            fence = None
            out.append(" " * len(line))
        else:
            out.append(" " * len(line) if fence else line)
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(description="문서 수치와 실제 값을 대조한다")
    ap.add_argument("docs", nargs="+", help="검사할 문서")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--values", help="{키: 값} JSON 파일")
    g.add_argument("--values-cmd", help="그 JSON 을 stdout 으로 내는 명령")
    a = ap.parse_args()

    if a.values:
        vals = json.load(open(a.values, encoding="utf-8"))
    else:
        r = subprocess.run(a.values_cmd, shell=True, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"값 명령이 실패했다: {r.stderr.strip()[:200]}", file=sys.stderr)
            return 2
        vals = json.loads(r.stdout)

    bad, seen = [], set()
    for doc in a.docs:
        text = strip_fences(open(doc, encoding="utf-8").read())
        for m in MARKER.finditer(text):
            wrote, key = int(m.group(1).replace(",", "")), m.group(2)
            seen.add(key)
            if key not in vals:
                bad.append(f"{doc}: N:{key} 에 대응하는 값이 없다")
            elif int(vals[key]) != wrote:
                bad.append(f"{doc}: {key} = {wrote} (실제 {vals[key]})")

    # 반대 방향도 본다 — 값은 있는데 문서가 안 들고 있는 것.
    # 이건 실패가 아니라 알림이다. 안 실어도 되는 값이 있을 수 있다.
    unused = sorted(set(vals) - seen)

    for b in bad:
        print(b)
    if unused:
        print(f"\n(문서가 안 드는 값: {', '.join(unused)})", file=sys.stderr)
    if bad:
        print(f"\n표류 {len(bad)}건 — 손으로 쓴 수치는 반드시 낡는다", file=sys.stderr)
        return 1
    print(f"✓ 표시된 수치 {len(seen)}개가 실제와 일치")
    return 0


if __name__ == "__main__":
    sys.exit(main())
