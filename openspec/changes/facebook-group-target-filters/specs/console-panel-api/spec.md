## ADDED Requirements

### Requirement: Facebook groups API accepts metadata filters and metadata-bearing imports
The panel API SHALL extend Facebook group management endpoints additively. `GET /api/facebook/groups` SHALL accept optional `region`, `park`, and `direction` query parameters. `POST /api/facebook/groups/import` SHALL accept `items[]` entries containing `url` plus optional `name`, `region`, `park`, and `direction`. Existing URL-only `text` and `urls` import payloads SHALL remain accepted.

#### Scenario: Metadata import item is accepted
- **WHEN** the console posts an import item with `url`, `region`, `park`, and `direction`
- **THEN** the panel API validates the fields and passes the metadata to the Facebook group target store

#### Scenario: Existing text import still works
- **WHEN** an API caller posts `text` containing one or more Facebook group URLs
- **THEN** the panel API still imports those URLs without requiring metadata

#### Scenario: Bad metadata type is rejected
- **WHEN** an import item has a non-string `region`, `park`, or `direction`
- **THEN** the panel API returns a bad request and does not import the malformed item

### Requirement: Console supports wide spreadsheet paste import for Facebook groups
The console SHALL parse pasted Facebook group data from both URL-only text and wide spreadsheet-like tabular text. For wide tables, it SHALL associate URLs under repeated `序号 + 园区名` column pairs with the active region header above them, and SHALL associate trailing non-park URL columns with their direction header. Missing region, park, or direction metadata SHALL be allowed.

#### Scenario: Repeated park columns import with region and park
- **WHEN** an operator pastes rows whose region header is `河南区域` and whose URL column belongs to `序号 + 同文1工业区`
- **THEN** the console sends import items for those URLs with `region=河南区域` and `park=同文1工业区`

#### Scenario: Direction columns import with direction
- **WHEN** an operator pastes rows whose URL column belongs to a header such as `机械和电气`
- **THEN** the console sends import items for those URLs with `direction=机械和电气`

#### Scenario: URL-only text import remains supported
- **WHEN** an operator pastes plain URL-only lines
- **THEN** the console sends URL-only import items and no metadata is required

### Requirement: Console exposes optional cascading metadata filters
The console Facebook groups page SHALL expose optional filters for region, park, and direction. The park selector SHALL be presented as a child of the selected region: changing or clearing region MUST clear the selected park, and only parks known under the selected region are selectable. None of the three filters SHALL be mandatory.

#### Scenario: Region controls park options
- **WHEN** an operator selects region `北宁区域`
- **THEN** the park selector only offers parks stored under `北宁区域`

#### Scenario: Clearing region clears park
- **WHEN** an operator clears the selected region
- **THEN** the selected park is cleared and the group list no longer applies a park filter

#### Scenario: All metadata filters are optional
- **WHEN** an operator leaves region, park, and direction unset
- **THEN** the group list still loads using the existing status/enabled filters
