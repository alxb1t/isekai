# Tasks — 0038 the changelog

The oldest versions first, then the middle, then the newest with the preamble; the rules and their tests last, so
each phase ends green, per [design](design.md).

## Progress

- [x] 1 — v0.1 to v0.13, rewritten
- [x] 2 — v0.14 to v0.22.3, rewritten
- [x] 3 — v0.22.4 to v0.26.0 and the preamble, rewritten
- [ ] 4 — The rules and their tests

Line numbers are `9dc8240`'s. Each rewrite follows [D1](design.md#d1) and [D3](design.md#d3), and each heading from
`0.7.0` takes its change id per [D2](design.md#d2).

## 1 — v0.1 to v0.13, rewritten

- [x] 1.1 **HALT CHECK** — both current flow digests are in the changelog, and `0.5.0` still has its heading.
  Verify: `grep -c -e f2bd3202079b1288 -e 96c605821e68a8ac CHANGELOG.md` prints `2`, and `grep -c '^## \[0.5.0\]' CHANGELOG.md` prints `1`.
- [x] 1.2 Rewrite `0.7.0` to `0.13.0` in `CHANGELOG.md`, each heading with its change id.
  Verify: `test "$(sed -n '/^## \[0.13.0\]/,/^## \[0.6.0\]/p' CHANGELOG.md | wc -l)" -lt 150 && echo ok` prints `ok`, and `sed -n '/^## \[0.13.0\]/,/^## \[0.7.0\]/p' CHANGELOG.md | grep '^## \[' | grep -vc ' · 00'` prints `0`.
- [x] 1.3 Rewrite `0.1.0` to `0.6.0`, and drop the `## [0.5.0]` heading and the link-reference block, per [D3](design.md#d3).
  Verify: `grep -c -e '^## \[0.5.0\]' -e '^\[Unreleased\]:' CHANGELOG.md` prints `0`, and `test "$(sed -n '/^## \[0.6.0\]/,$p' CHANGELOG.md | wc -l)" -lt 40 && echo ok` prints `ok`.
- [x] 1.4 Keep only the Keep a Changelog sections from `0.13.0` down.
  Verify: `sed -n '/^## \[0.13.0\]/,$p' CHANGELOG.md | grep '^### ' | grep -vcE '^### (Added|Changed|Deprecated|Removed|Fixed|Security)$'` prints `0`.

## 2 — v0.14 to v0.22.3, rewritten

- [x] 2.1 Rewrite `0.14.0` to `0.22.3`, each heading with its change id; the `0.22.3` re-pin table goes, per [D3](design.md#d3).
  Verify: `test "$(sed -n '/^## \[0.22.3\]/,/^## \[0.13.0\]/p' CHANGELOG.md | wc -l)" -lt 250 && echo ok` prints `ok`, and `sed -n '/^## \[0.22.3\]/,/^## \[0.14.0\]/p' CHANGELOG.md | grep '^## \[' | grep -vc ' · 00'` prints `0`.
- [x] 2.2 Keep only the Keep a Changelog sections from `0.22.3` down.
  Verify: `sed -n '/^## \[0.22.3\]/,$p' CHANGELOG.md | grep '^### ' | grep -vcE '^### (Added|Changed|Deprecated|Removed|Fixed|Security)$'` prints `0`.

## 3 — v0.22.4 to v0.26.0 and the preamble, rewritten

- [x] 3.1 Rewrite `0.22.4` to `0.26.0`, each heading with its change id, keeping the `conjure` and `summon` digests in the bullets [D4](design.md#d4) names.
  Verify: `test "$(sed -n '/^## \[0.26.0\]/,/^## \[0.22.3\]/p' CHANGELOG.md | wc -l)" -lt 250 && echo ok` prints `ok`, `sed -n '/^## \[0.26.0\]/,/^## \[0.22.4\]/p' CHANGELOG.md | grep '^## \[' | grep -vc ' · 00'` prints `0`, and `grep -c -e f2bd3202079b1288068aed7ccf57e2b6b0e3b9a1db037973b4be99f83bf22a1f -e 96c605821e68a8ac2f1c7a60807cfcfb4c3658ae4112cc84d21a00bf39f3e698 CHANGELOG.md` prints `2`.
- [x] 3.2 Replace everything above `## [Unreleased]` with the preamble [D5](design.md#d5) gives.
  Verify: `test "$(sed -n '1,/^## \[Unreleased\]/p' CHANGELOG.md | wc -l)" -lt 15 && echo ok` prints `ok`, and `grep -c 'backfilled' CHANGELOG.md` prints `0`.
- [x] 3.3 Check the whole file: only Keep a Changelog's sections, no nested bullet, no pod id, and a length an agent loads cheaply.
  Verify: `grep '^### ' CHANGELOG.md | grep -vcE '^### (Added|Changed|Deprecated|Removed|Fixed|Security)$'` prints `0`, `grep -cE '^ +[-*] ' CHANGELOG.md` prints `0`, `` git show v0.26.0:CHANGELOG.md | grep -oE '`[a-z0-9]{14}`' | grep '[0-9]' | tr -d '`' | sort -u | grep -cFf - CHANGELOG.md `` prints `0`, and `test "$(wc -l < CHANGELOG.md)" -lt 700 && echo ok` prints `ok`.

## 4 — The rules and their tests

- [ ] 4.1 **HALT CHECK** — the evaluation baseline still cites the changelog.
  Verify: `git grep -l CHANGELOG -- evaluation | grep -c .` prints `2`.
- [ ] 4.2 Rewrite `CLAUDE.md:117-118` and `:204-205` per [D6](design.md#d6).
  Verify: `grep -c 'the three pod ids already in' CLAUDE.md` prints `0`, and `grep -cF 'No code, doc or README' CLAUDE.md` prints `1`.
- [ ] 4.3 Remove the citations in `evaluation/baseline/README.md` and `evaluation/baseline/build_subjects.py` per [D7](design.md#d7).
  Verify: `git grep -l CHANGELOG -- evaluation | grep -c .` prints `0`.
- [ ] 4.4 Add `tests/test_changelog.py` per [D8](design.md#d8): `test_the_changelog_keeps_its_format` and `test_nothing_cites_the_changelog`, each with its twin.
  Verify: `grep -c -e '^def test_the_changelog_keeps_its_format' -e '^def test_nothing_cites_the_changelog' tests/test_changelog.py` prints `2`, and `grep -c '^def test_' tests/test_changelog.py` prints `4`.
