# 무효 판정 재현하기

생성 파이프라인 앞에서 생성물을 변이시키면 어떻게 되는지 직접 본다.

```bash
examples/build.sh                      # examples/site → examples/generated
printf '무효 시연\texamples/generated/index.html\ts.replace('"'"'<a href="/a/">A</a>'"'"', '"'"'A'"'"')\texamples/build.sh && checks/orphan_pages.py examples/generated --ignore orphan\n' > /tmp/void.tsv
mutation/mutate.sh /tmp/void.tsv
```

```
⚠  무효 시연   무효 — 변이가 덮어써졌다. 생성물 말고 정본을 변이시켜라
```

검사 명령의 첫 단계(`build.sh`)가 변이된 파일을 다시 짓는다.
검사는 깨끗한 파일을 보고 통과를 보고한다 — **변이를 본 적이 없다.**

이 판정이 없으면 이 케이스는 "안 물었다"로 보고되고,
멀쩡한 검사기를 고치느라 시간을 쓰게 된다. 실제로 그랬다.
