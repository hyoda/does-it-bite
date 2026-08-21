#!/usr/bin/env python3
"""공개 산출물에 나가면 안 되는 이름이 남았는지 본다.

목록에서 항목을 지우는 것만으로는 부족하다. **다른 필드가 그 이름을 문자열로
품고 있으면 소속이 드러난다.** 설명문, 링크 URL, 예제 코드, 스크린샷 파일명 —
지운 줄 알았던 이름이 옆 칸에 남아 있다.

    checks/leaked_names.py dist/ --forbidden private-names.txt
    checks/leaked_names.py dist/ --forbidden names.txt --allow allow.tsv

allow.tsv 는 예외다. 탭 3칸이고 **이유와 확인일이 필수**다:
    이름 <TAB> 왜 공개해도 되는가 <TAB> 확인일
이유 없는 예외는 예외가 아니라 구멍이다. 이 검사는 이유 칸이 비면 거부한다.

종료 코드 1 = 누출됐다.
"""
import argparse
import os
import re
import sys

TEXTLIKE = (".html", ".htm", ".json", ".txt", ".xml", ".md", ".css", ".js",
            ".jsonld", ".csv", ".tsv", ".yml", ".yaml", ".svg")


def load_allow(path):
    """예외 목록. 이유가 비면 예외로 인정하지 않는다."""
    allow, bad = set(), []
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        name = parts[0].strip()
        reason = parts[1].strip() if len(parts) > 1 else ""
        checked = parts[2].strip() if len(parts) > 2 else ""
        if not reason or not checked:
            bad.append(f"{path}:{n} '{name}' — 이유·확인일이 있어야 예외가 된다")
        else:
            allow.add(name.lower())
    return allow, bad


def main():
    ap = argparse.ArgumentParser(description="공개물에 금지된 이름이 남았는지 본다")
    ap.add_argument("root", help="공개 산출물 디렉토리")
    ap.add_argument("--forbidden", required=True,
                    help="한 줄에 하나씩 적은 금지 이름 파일")
    ap.add_argument("--allow", help="예외 TSV (이름·이유·확인일)")
    ap.add_argument("--min-len", type=int, default=4,
                    help="이 길이 미만의 이름은 건너뛴다 (오탐 방지, 기본 4)")
    a = ap.parse_args()

    names = {l.strip().lower() for l in open(a.forbidden, encoding="utf-8")
             if l.strip() and not l.lstrip().startswith("#")}
    allow, allow_bad = (set(), [])
    if a.allow:
        allow, allow_bad = load_allow(a.allow)
    for b in allow_bad:
        print(b)

    targets = sorted(n for n in names - allow if len(n) >= a.min_len)
    if not targets:
        print("검사할 이름이 없다", file=sys.stderr)
        return 2 if not allow_bad else 1

    hits = []
    for dp, _, fs in os.walk(a.root):
        for f in fs:
            if not f.lower().endswith(TEXTLIKE):
                continue
            p = os.path.join(dp, f)
            body = open(p, encoding="utf-8", errors="replace").read().lower()
            for name in targets:
                # 단어 경계로 본다. 부분일치는 오탐이 너무 많다
                # (`api` 가 `rapid` 에 걸리는 식).
                if re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(name), body):
                    hits.append((p, name))
            # 파일명 자체도 이름을 품는다 — 본문만 보면 놓친다.
            for name in targets:
                if name in f.lower():
                    hits.append((p, f"{name} (파일명)"))

    for p, name in sorted(set(hits)):
        print(f"{p}: {name}")
    if allow_bad:
        return 1
    if hits:
        print(f"\n누출 {len(set(hits))}건 — 항목을 지워도 다른 필드가 품고 있다",
              file=sys.stderr)
        return 1
    print(f"✓ 금지 이름 {len(targets)}개가 공개물에 없다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
