#!/usr/bin/env bash
# 빌드가 멱등한지 본다. 두 번 돌려 결과가 다르면
# **"생성물이 커밋과 일치하는가" 를 영원히 검증할 수 없다.**
#
# 멱등하지 않은 빌드는 조용히 비싼 값을 치른다. 매번 diff 가 뜨니 사람이
# 그 diff 를 안 보게 되고, 안 보게 된 diff 속에 진짜 변경이 섞여 들어간다.
#
# 흔한 원인 넷:
#   · 타임스탬프를 산출물에 박는다 (generatedAt, 빌드 시각, 캐시 버스터)
#   · append 로 쌓는다 (지우고 다시 쓰지 않는다)
#   · 순서가 없는 자료구조를 순서대로 낸다 (set, dict 순회, glob 순서)
#   · 난수·UUID 를 매번 새로 만든다
#
# 사용법:  checks/idempotent_build.sh '<빌드 명령>' <산출 디렉토리>
#   예:    checks/idempotent_build.sh 'make site' dist/

set -uo pipefail
CMD="${1:?빌드 명령이 필요하다}"
OUT="${2:?산출 디렉토리가 필요하다}"

snap() {  # 디렉토리를 '경로 해시' 목록으로 찍는다
  find "$OUT" -type f -print0 2>/dev/null | sort -z |
    while IFS= read -r -d '' f; do
      printf '%s  %s\n' "$(shasum -a 256 <"$f" | cut -d' ' -f1)" "${f#"$OUT"/}"
    done
}

echo "── 1회차: $CMD"
eval "$CMD" >/dev/null 2>&1 || { echo "빌드가 실패했다" >&2; exit 2; }
A="$(mktemp)"; snap >"$A"

echo "── 2회차: $CMD"
eval "$CMD" >/dev/null 2>&1 || { echo "2회차 빌드가 실패했다" >&2; exit 2; }
B="$(mktemp)"; snap >"$B"

if diff -q "$A" "$B" >/dev/null; then
  echo "✓ 멱등하다 — 파일 $(wc -l <"$A" | tr -d ' ')개가 두 번 다 같다"
  rm -f "$A" "$B"; exit 0
fi

echo "✖ 빌드가 멱등하지 않다 — 두 번 돌려 결과가 다르다"
echo
# 어느 파일이 흔들리는지 보여준다. 원인은 대개 그 파일 안에 적혀 있다.
join -j 2 <(sort -k2 "$A") <(sort -k2 "$B") 2>/dev/null |
  awk '$2 != $3 { print "    " $1 }' | head -20
rm -f "$A" "$B"
exit 1
