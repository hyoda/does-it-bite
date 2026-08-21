#!/usr/bin/env bash
# 정본(examples/site)에서 생성물(examples/generated)을 짓는 척하는 최소 빌드.
rm -rf examples/generated && cp -R examples/site examples/generated
