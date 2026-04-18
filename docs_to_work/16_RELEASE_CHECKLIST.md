# Release Checklist
## Чеклист выпуска релиза

**Редакция пакета:** v3  
**Связанный индекс:** `00_INDEX.md`


## 1. Назначение

Чеклист нужен, чтобы не выпускать релиз по ощущению.  
Релиз считается готовым только после прохождения явных quality gates.

## 2. Главный принцип

`build succeeded` != `release ready`.

Нужны проверки:
- build;
- runtime;
- first-run;
- import/export smoke;
- diagnostics/recovery readiness;
- clean-machine path;
- docs readiness;
- bundle completeness.

## 3. Предрелизная подготовка

Проверить:
- version/build info fixed;
- correct code state;
- pinned requirements актуальны;
- wheel-cache and manifest согласованы;
- build environment stable.

## 4. Build quality gate

Проверить:
- build script runs normally;
- manifest valid;
- wheel files present;
- versions match;
- hashes match;
- build artifact produced;
- build logs usable.

## 5. Runtime quality gate

Проверить:
- app starts;
- first-run works;
- profile created;
- settings initialized;
- resources found;
- second-run works.

## 6. Functional smoke gate

Проверить:
- main window opens;
- tournaments screen opens;
- players screen opens;
- ratings screen opens;
- import screen opens;
- settings open;
- journal opens;
- reports/export entrypoints work.

## 7. Export and print gate

Проверить:
- single export works;
- batch export works;
- print flow not broken;
- outputs are real files and usable.

## 8. Diagnostics / recovery gate

Проверить:
- audit screen works;
- audit export works;
- logs path understandable;
- diagnostics entrypoint works, if included;
- no silent fatal failures;
- recovery path not dead-end.

## 9. Clean-machine gate

На чистой Windows-машине проверить:
- release starts;
- first-run works;
- major screens open;
- sample import works;
- export works;
- relaunch works.

## 10. Documentation gate

Проверить актуальность:
- Build guide
- User guide
- Admin guide
- Recovery guide
- README

## 11. Release bundle gate

Проверить:
- main exe present;
- version naming correct;
- no dev garbage;
- optional release notes/docs included as intended.

## 12. Acceptance gate

Ручная проверка минимум:
- first-run;
- import;
- tournament open/recalc;
- rating open/export;
- player open/history;
- journal open/export;
- relaunch.

Known limitations, если есть, должны быть:
- сознательными;
- описанными;
- не скрытыми.

## 13. Release decision

Релиз можно выпускать только если пройдены:
- build gate;
- runtime gate;
- functional smoke;
- export/print gate;
- diagnostics/recovery gate;
- clean-machine gate;
- documentation gate;
- bundle gate;
- acceptance gate.

## 14. Короткий чеклист

- [ ] version fixed
- [ ] pinned deps актуальны
- [ ] wheel-cache valid
- [ ] manifest valid
- [ ] build passes
- [ ] artifact exists
- [ ] app starts
- [ ] first-run works
- [ ] second-run works
- [ ] tournaments open
- [ ] players open
- [ ] ratings open
- [ ] import opens
- [ ] export works
- [ ] journal works
- [ ] diagnostics path usable
- [ ] clean-machine check passed
- [ ] docs updated
- [ ] release bundle clean

## 15. Итог

Release checklist finished, если:
- по нему реально можно принять решение о выпуске;
- он не сводится к “собралось = готово”;
- он покрывает build, runtime, smoke, diagnostics, clean-machine и docs.
