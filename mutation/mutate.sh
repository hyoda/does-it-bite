#!/usr/bin/env bash
# mutate.sh — 검사기가 실제로 무는지 시험한다.
#
# 검사가 "통과"를 보고하는 것은 근거가 아니다. 아무것도 안 보는 검사도 통과를 보고한다.
# 알 수 있는 방법은 하나뿐이다 — **틀린 것을 넣어보고 무는지 본다.**
#
# 사용법:  mutation/mutate.sh <cases.tsv> [--only <라벨>]
#
# cases.tsv 는 탭 4칸:
#   라벨 <TAB> 변이시킬_파일 <TAB> python3 표현식 <TAB> 검사_명령
#
#   표현식은 `s` (파일 내용 문자열)를 받아 변이된 문자열을 낸다.
#     예:  s.replace('href="/about/"', 'href="/gone/"', 1)
#
#   검사_명령은 정상일 때 0, 문제를 찾으면 0이 아닌 값을 내야 한다.
#
# 판정 넷:
#   물었다      변이 후 검사가 실패했다 — 이 검사는 살아 있다
#   안 물었다   변이했는데도 통과했다 — **이 검사는 아무것도 안 보고 있다**
#   무효        변이가 덮어써졌다 — 생성물을 변이시켰다 (아래 참조)
#   불성립      변이 전에 이미 실패하고 있었다 — 먼저 그걸 고친다
#
# ── 무효 판정이 이 스크립트의 존재 이유다 ──────────────────────────
# 생성 파이프라인을 가진 저장소에서 `dist/index.html` 을 변이시키고 검사를 돌리면,
# 검사가 1단계에서 dist/ 를 재생성하며 변이를 덮어쓴다. 검사는 깨끗한 파일을 보고
# 통과를 보고하고, 우리는 "검사가 문다"고 잘못 결론짓는다.
# **생성물을 변이시키는 시험은 생성 파이프라인 앞에서 무효다.** 정본을 변이시켜야 한다.
# 그래서 이 스크립트는 검사 실행 뒤 파일이 그대로인지 확인하고, 아니면 무효로 판정한다.
# (실제로 이 함정에 빠진 적이 있다 — FAILURES.md 의 F4 를 보라.)

set -uo pipefail

CASES="${1:-mutation/cases.tsv}"
ONLY=""
[ "${2:-}" = "--only" ] && ONLY="${3:-}"

[ -f "$CASES" ] || { echo "케이스 파일이 없다: $CASES" >&2; exit 2; }

bit=0; miss=0; void=0; moot=0
printf '── 변이 시험 · %s\n\n' "$CASES"

while IFS=$'\t' read -r label file expr cmd; do
  case "$label" in ''|'#'*) continue ;; esac
  [ -n "$ONLY" ] && [ "$label" != "$ONLY" ] && continue

  if [ ! -f "$file" ]; then
    printf '  ?  %-38s 대상 파일 없음: %s\n' "$label" "$file"
    moot=$((moot+1)); continue
  fi

  # 변이 전에 검사가 통과하는지 본다. 이미 실패하고 있으면 시험이 성립하지 않는다 —
  # 변이 후의 실패가 변이 때문인지 원래 그런 건지 구별할 수 없다.
  if ! eval "$cmd" >/dev/null 2>&1; then
    printf '  ?  %-38s 변이 전에 이미 실패 — 그것부터 고친다\n' "$label"
    moot=$((moot+1)); continue
  fi

  backup="$(mktemp)"; cp "$file" "$backup"

  if ! MUT_FILE="$file" python3 - "$expr" <<'PY'
import os, sys
p = os.environ["MUT_FILE"]
s = open(p, encoding="utf-8").read()
out = eval(sys.argv[1], {"s": s, "re": __import__("re")})
if out == s:
    sys.stderr.write("표현식이 아무것도 바꾸지 않았다\n"); sys.exit(3)
open(p, "w", encoding="utf-8").write(out)
PY
  then
    cp "$backup" "$file"; rm -f "$backup"
    printf '  ?  %-38s 변이 실패 (표현식이 안 맞는다)\n' "$label"
    moot=$((moot+1)); continue
  fi

  mutated="$(mktemp)"; cp "$file" "$mutated"

  eval "$cmd" >/dev/null 2>&1; rc=$?

  # 검사가 파일을 되돌려놨는가? 그렇다면 검사는 변이를 본 적이 없다.
  if ! cmp -s "$file" "$mutated"; then
    verdict="void"
  elif [ "$rc" -ne 0 ]; then
    verdict="bit"
  else
    verdict="miss"
  fi

  cp "$backup" "$file"; rm -f "$backup" "$mutated"

  case "$verdict" in
    bit)  printf '  ✓  %-38s 물었다\n' "$label"; bit=$((bit+1)) ;;
    miss) printf '  ✖  %-38s **안 물었다 — 이 검사는 아무것도 안 보고 있다**\n' "$label"; miss=$((miss+1)) ;;
    void) printf '  ⚠  %-38s 무효 — 변이가 덮어써졌다. 생성물 말고 정본을 변이시켜라\n' "$label"; void=$((void+1)) ;;
  esac
done < "$CASES"

printf '\n────────────────────────\n'
printf '무는 검사 %d · 안 무는 검사 %d · 무효 %d · 불성립 %d\n' "$bit" "$miss" "$void" "$moot"
[ "$miss" -eq 0 ] && [ "$void" -eq 0 ] || {
  echo "위 검사는 통과해도 의미가 없다"; exit 1; }
echo "✓ 시험한 검사가 전부 문다"
