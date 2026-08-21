#!/usr/bin/env bash
# 이 저장소의 수치를 센다. README 는 이 값을 들 뿐 자기가 세지 않는다 —
# 손으로 쓴 수치는 반드시 낡는다(FAILURES.md F1).
# doc_drift.py 가 이 출력과 README 의 <!--N:키--> 표시를 대조한다.
set -euo pipefail
cd "$(dirname "$0")/.."

checks=$(find checks -maxdepth 1 -type f \( -name '*.py' -o -name '*.sh' \) | wc -l)
failures=$(grep -c '^## F[0-9]' FAILURES.md)

printf '{"checks": %d, "failures": %d}\n' "$checks" "$failures"
