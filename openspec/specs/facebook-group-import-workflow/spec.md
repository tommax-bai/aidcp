# facebook-group-import-workflow Specification

## Purpose
TBD - created by archiving change facebook-group-import-modes. Update Purpose after archive.
## Requirements
### Requirement: Facebook group addition exposes two explicit modes
The console SHALL present mutually exclusive `单条添加` and `文件导入` modes in the Facebook groups management section. The single-group mode SHALL be selected by default, and changing modes MUST NOT submit data automatically.

#### Scenario: Page opens in single-group mode
- **WHEN** an operator opens the Facebook groups page
- **THEN** the single-group URL and metadata controls are shown and the file-import controls are hidden

#### Scenario: Operator switches to file import
- **WHEN** an operator selects the file-import mode
- **THEN** the CSV upload and template download controls are shown without sending an import request

### Requirement: Single-group mode adds one URL with optional metadata
Single-group mode SHALL accept one Facebook group URL and optional region, park, and direction values. The add command MUST remain unavailable when the URL is empty. The park selector SHALL depend on the selected region, and changing or clearing region MUST clear the selected park.

#### Scenario: Add a URL without metadata
- **WHEN** an operator enters one group URL, leaves all metadata empty, and selects add
- **THEN** the console sends one structured import item containing the URL and no required metadata

#### Scenario: Add a URL with selected metadata
- **WHEN** an operator enters one group URL and selects region, park, and direction values
- **THEN** the console sends one structured import item containing the URL and selected metadata

#### Scenario: Region change clears park
- **WHEN** an operator has selected a park and then changes or clears the region
- **THEN** the selected park is cleared before a group can be added

### Requirement: File mode parses and imports CSV rows
File-import mode SHALL accept `.csv` files up to 5 MB and parse them in the browser. The parser SHALL support UTF-8 BOM, LF or CRLF records, quoted fields, commas inside quoted fields, and escaped double quotes. It SHALL map the template columns into structured group import items, ignore fully empty rows, and require a recognized group URL column. The console MUST NOT send an import request when parsing fails or no importable row exists.

#### Scenario: Valid template CSV is ready to import
- **WHEN** an operator selects a CSV containing the required URL header and one or more rows with non-empty group URLs
- **THEN** the console shows the selected filename and importable-row count and enables the file import command

#### Scenario: Optional cells are empty
- **WHEN** a CSV row has a group URL but empty region, park, direction, or group-name cells
- **THEN** the row remains importable and empty optional values are omitted from its structured item

#### Scenario: CSV contains quoted commas
- **WHEN** a quoted CSV field contains a comma or escaped double quote
- **THEN** the parser treats that content as one field and maps the complete value

#### Scenario: CSV has no recognized URL column
- **WHEN** an operator selects a CSV whose header has no supported group URL column
- **THEN** the console reports a template/header error and does not send an import request

#### Scenario: File is too large or not CSV
- **WHEN** an operator selects a non-CSV file or a CSV larger than 5 MB
- **THEN** the console rejects the file before import and does not send an import request

### Requirement: Console provides a downloadable CSV template
File-import mode SHALL provide a command that downloads a UTF-8 BOM-prefixed CSV template named `facebook-group-import-template.csv`. The template SHALL contain the columns `群组URL`, `区域`, `园区`, `方向`, and `群组名称`, with `群组URL` as the only required per-row field, and SHALL contain no sample group row.

#### Scenario: Operator downloads the template
- **WHEN** an operator selects the template download command
- **THEN** the browser downloads `facebook-group-import-template.csv` with the supported header row and no data row

### Requirement: Import feedback remains truthful
Both modes SHALL submit through the existing structured Facebook group import API and SHALL display the server-reported imported, updated, duplicate, and invalid counts. A successful response MUST NOT be presented as though every submitted row was imported.

#### Scenario: Server reports mixed import outcomes
- **WHEN** the import response contains imported, updated, duplicate, and invalid counts
- **THEN** the console displays each count and clears only the successfully submitted mode's input state

### Requirement: 群组导入可选应用公共账号分组范围且缺省不清空

单条添加和文件导入 SHALL 提供可选公共适用范围，并允许运营显式选择 `global` 或 `restricted + accountGroupLabels`，把该范围应用到本次提交所有导入目标。请求未携带任何范围字段时，已存在目标的范围 MUST 保持不变，新目标 SHALL 保持 `restricted + empty`；请求显式携带范围时，成功导入/更新的目标 SHALL 用该完整范围替换原值。`global` 与非空账号分组标签同时出现 MUST 整块拒绝。范围校验失败 MUST 在写目标、元数据和映射前拒绝该提交，不能出现半成功。

#### Scenario: 重复导入未选择范围时保留映射
- **WHEN** 已映射“华东组”的受限目标被再次导入且请求没有范围字段
- **THEN** 目标元数据按既有规则更新，而 `restricted + 华东组` 范围保持不变

#### Scenario: 导入统一应用全局范围
- **WHEN** 运营选择“全局分组”后导入一个 CSV
- **THEN** 本次成功导入或更新的每个目标都回读为 `global` 且标签集合为空

#### Scenario: 文件导入统一应用多个分组
- **WHEN** 运营选择受限模式及“华东组”和“招聘组”后导入一个 CSV
- **THEN** 本次成功导入或更新的每个目标都回读为 `restricted` 并同时映射这两个分组

#### Scenario: 显式受限空集合清除范围
- **WHEN** 运营明确提交 `restricted` 且账号分组集合为空
- **THEN** 成功目标的范围被清空并诚实标记为不会被自动或裸 `--join` 认领

#### Scenario: 矛盾范围不产生元数据半写
- **WHEN** 导入请求同时提交 `global` 和非空账号分组集合
- **THEN** 整个导入具名拒绝，群元数据、范围与 membership 均不改变

