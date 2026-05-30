# Requirements Document

## Introduction

Добавление визуальной индикации и управления статусом ПНО (Pending Operator Request / Ожидание оператора) в журнале простоев (Utilization). Функциональность включает подсветку ячейки в колонке "ПНО" в гриде ag-grid и чекбокс в форме редактирования простоя для переключения статуса ПНО.

## Glossary

- **Grid**: Таблица ag-grid, отображающая данные журнала простоев (Utilization)
- **UtilizationUpdate_Form**: Модальная форма редактирования записи простоя, реализованная на Preact (компонент `UtilizationForm`)
- **PNO_Column**: Колонка в гриде, отображающая значение поля `ReasonPending` (алиас `OperatorRequest` из представления `v_Utilization`)
- **OperatorRequest**: Булево поле в таблице `Utilization`, хранящее статус ПНО (true — ожидание оператора, false — нет)
- **CellStyle**: Функция ag-grid `cellStyle`, определяющая визуальное оформление ячейки на основе значения данных
- **ExternalFunctionsBase**: Скрипт `externalFunctionsBase.js`, выполняющий настройку грида при загрузке журнала
- **Save_Payload**: Объект `body.data`, передаваемый в API `upsertLightCustomTable` при сохранении формы

## Requirements

### Requirement 1: Подсветка ячейки ПНО в гриде

**User Story:** Как оператор, я хочу видеть визуальную индикацию статуса ПНО в гриде журнала простоев, чтобы быстро определять записи, ожидающие действия оператора.

#### Acceptance Criteria

1. WHEN the Grid loads for the downtime journal, THE ExternalFunctionsBase SHALL apply a `cellStyle` function to the PNO_Column that evaluates the cell value for each row
2. WHILE the PNO_Column cell value equals `true`, THE CellStyle function SHALL set the cell background color to `#FFF3CD`
3. WHILE the PNO_Column cell value equals `false` or is null or undefined, THE CellStyle function SHALL return `null` (standard grid background, no custom color)
4. WHEN the grid data is refreshed after a save operation, THE CellStyle function SHALL re-evaluate and apply the correct background color based on the updated PNO_Column value
5. THE ExternalFunctionsBase SHALL apply the PNO_Column cellStyle only when the journal name matches the downtime journal (determined by `component.eventFrameLogDto.name`)

### Requirement 2: Чекбокс ПНО в форме редактирования простоя

**User Story:** Как оператор, я хочу иметь возможность устанавливать или снимать статус ПНО при редактировании записи простоя, чтобы управлять флагом ожидания оператора.

#### Acceptance Criteria

1. WHEN the UtilizationUpdate_Form opens, THE UtilizationUpdate_Form SHALL display a checkbox field with the title "ПНО" in the "Причина простоя" group
2. WHEN the UtilizationUpdate_Form opens, THE checkbox "ПНО" SHALL be initialized with the current `OperatorRequest` value from the selected row (true = checked, false = unchecked)
3. WHEN the operator toggles the "ПНО" checkbox and saves the form, THE Save_Payload SHALL include the `OperatorRequest` field set to the checkbox value (true or false)
4. THE "ПНО" checkbox field SHALL have `order: 8` to position it after the "Причина" dropdown in the "Причина простоя" group
5. THE "ПНО" checkbox field SHALL use `type: "checkbox"`, `required: false`, and `disabled: false`

### Requirement 3: Определение колонки ПНО в гриде

**User Story:** Как оператор, я хочу видеть колонку "ПНО" в журнале простоев, чтобы данные о статусе ожидания оператора были доступны в табличном виде.

#### Acceptance Criteria

1. THE view `v_Utilization` SHALL expose the field `OperatorRequest` aliased as `ReasonPending` (boolean)
2. WHEN the grid column definitions are configured, THE PNO_Column SHALL be identified by its field name `ReasonPending` (or the corresponding display header "ПНО")
3. THE PNO_Column SHALL display boolean values from the `ReasonPending` field for each row in the downtime journal
