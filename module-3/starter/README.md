# Module 3 — Lab Starter

```
skill_template/          # skill scaffold trainees copy to work/<skill-name>/
  SKILL.md.tpl
  README.md
scenarios/               # three scenarios (happy/edge/failure) per supported skill task
  SCENARIOS.md
```

Được dùng bởi `labs/module3/HANDOUT.md`. Lab là một session gộp duy nhất chạy trong Day 2.

## Inactive folders (stubs only)

`lab3a/`, `lab3b_template/`, `lab3c/`, `lab3d/` — sót lại từ v1.x. Mọi file bên trong là stub `DEPRECATED` một dòng. Các bản active nằm ở những path phía trên. Việc xoá file (filesystem deletion) không khả dụng trong authoring environment; nếu bạn có shell access tại máy, chạy:

```
rm -rf labs/module3/starter/lab3a labs/module3/starter/lab3b_template labs/module3/starter/lab3c labs/module3/starter/lab3d
```
