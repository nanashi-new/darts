# Implementation Plan: PNO Indication

## Overview

Добавление визуальной индикации статуса ПНО в гриде журнала простоев (подсветка ячейки) и чекбокса управления статусом ПНО в форме редактирования простоя. Реализация затрагивает два файла: `externalFunctionsBase.js` (подсветка грида) и `UtilizationUpdate.js` (чекбокс + payload).

## Tasks

- [x] 1. Add cellStyle for PNO column in externalFunctionsBase.js
  - [x] 1.1 Add cellStyle block for PNO column highlighting
    - Open `Utilization/tasks/pno-indication/wwwroot/assets/external-js/externalFunctionsBase.js`
    - Add a new block after the existing "Состояния использования" cellStyle block
    - Guard the block with journal name check: `component.eventFrameLogDto.name == "Журнал простоев"` (placeholder — adjust if needed)
    - Find the PNO column dynamically: `columnDefs.findIndex(col => col.field === 'ReasonPending')`
    - Apply cellStyle: return `{ backgroundColor: '#FFF3CD' }` when `params.value === true || params.value === 'true'`, otherwise return `null`
    - Call `component.gridView.gridApi.setColumnDefs(columnDefs)` to apply changes
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Implement PNO checkbox in UtilizationUpdate.js
  - [x] 2.1 Add isTrueValue helper function
    - Open `Utilization/functions/Utilization/UtilizationUpdate.js`
    - Add the `isTrueValue` helper near the top utility functions section (same implementation as in UtilizationSplit.js)
    - The helper normalizes boolean/string/null/undefined values to a boolean result
    - _Requirements: 2.2_

  - [x] 2.2 Add PNO checkbox field to initialData
    - In the same file `UtilizationUpdate.js`, add a variable: `const currentIsPno = isTrueValue(fullRow?.OperatorRequest) || isTrueValue(fullRow?.ReasonPending);`
    - Add field to `initialData` array: `{ title: 'ПНО', dataField: 'ПНО', value: currentIsPno, type: 'checkbox', required: false, disabled: false, order: 8, group: 'Причина простоя' }`
    - _Requirements: 2.1, 2.2, 2.4, 2.5_

  - [x] 2.3 Fix save payload to use checkbox value
    - In the same file `UtilizationUpdate.js`, locate the save payload construction
    - Replace `OperatorRequest: false,` with `OperatorRequest: ef['ПНО'] === true || ef['ПНО'] === 'true',`
    - This ensures the saved value reflects the actual checkbox state
    - _Requirements: 2.3_

- [x] 3. Checkpoint - Verify all changes are correct
  - Ensure all changes are consistent across files, ask the user if questions arise.

- [x] 4. Copy modified files to deployment folder
  - [x] 4.1 Copy UtilizationUpdate.js to to_upload folder
    - Copy the modified `Utilization/functions/Utilization/UtilizationUpdate.js` to `Utilization/to_upload/UtilizationUpdate.js`
    - This is the version that gets deployed to the target environment
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 5. Final checkpoint - Ensure all files are in place
  - Ensure all modified files are saved and the to_upload copy matches the source, ask the user if questions arise.

## Notes

- No property-based tests are included as tasks — this is a simple UI enhancement with straightforward logic. The correctness properties in the design document serve as documentation of expected behavior.
- The journal name `"Журнал простоев"` in externalFunctionsBase.js is a placeholder and may need adjustment based on the deployment configuration.
- The `isTrueValue` helper already exists in `UtilizationSplit.js` — the same implementation is reused in `UtilizationUpdate.js`.
- Task 1 (grid cellStyle) is independent from Tasks 2.x (form checkbox). Task 4 depends on completion of Task 2.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1"] },
    { "id": 1, "tasks": ["2.2"] },
    { "id": 2, "tasks": ["2.3"] },
    { "id": 3, "tasks": ["4.1"] }
  ]
}
```
