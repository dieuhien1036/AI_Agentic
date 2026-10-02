# Module 4 — Lab Starter

```
sample_pr/               # the sample PR trainees review
  diff.patch             # the PR diff (8 seeded issues)
  SEEDED_ISSUES.md       # instructor reference: list of 8 issues
pipeline/                # subagent + driver scaffolds trainees adapt under work/pipeline.py
  planner.md.tpl
  reviewer.md.tpl
  aggregator.md.tpl
  verifier.md.tpl
  pipeline.py.tpl
  schemas/               # JSON schemas for each handoff
hardening/               # hardening pass template
  HARDENING.md.tpl
```

Được dùng bởi `labs/module4/HANDOUT.md`. Lab là một session gộp duy nhất, chạy vào Day 3.

## Inactive folders (stubs only)

`lab4a/`, `lab4b/`, `lab4c/`, `lab4d/` — sót lại từ v1.x. Mọi file bên trong đều là stub `DEPRECATED` một dòng. Các phiên bản đang dùng nằm ở các path phía trên. Môi trường authoring không cho xoá file; nếu bạn có shell access ở máy local, chạy:

```
rm -rf labs/module4/starter/lab4a labs/module4/starter/lab4b labs/module4/starter/lab4c labs/module4/starter/lab4d
```
