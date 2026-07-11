## ADDED Requirements

### Requirement: Facebook group targets carry optional business filters
Facebook group targets SHALL support optional `region`, `park`, and `direction` metadata. None of the three fields is required to create or list a target. Existing targets without metadata SHALL remain valid.

#### Scenario: URL-only target remains valid
- **WHEN** an operator imports a Facebook group URL without region, park, or direction
- **THEN** the target is accepted and its metadata fields are stored as null

#### Scenario: Metadata target is returned to the console
- **WHEN** a target has region, park, and direction metadata
- **THEN** the group target list returns those metadata fields with the target row

### Requirement: Facebook group URLs are canonicalized before storage
Facebook group import SHALL canonicalize every accepted URL to `https://www.facebook.com/groups/<slug-or-id>` before storage and duplicate detection. Query strings, fragments, locale parameters, share tracking parameters, and deeper path suffixes after the group identifier MUST NOT be stored as part of the target key. Invalid or non-group Facebook URLs SHALL be rejected as invalid imports.

#### Scenario: Query parameters are discarded
- **WHEN** an operator imports `https://www.facebook.com/groups/322376783153364/?cft[0]=abc&tn=-UC`
- **THEN** the stored group URL is `https://www.facebook.com/groups/322376783153364`

#### Scenario: Deeper post path is reduced to the group
- **WHEN** an operator imports `https://m.facebook.com/groups/group-a/posts/123?ref=share`
- **THEN** the stored group URL is `https://www.facebook.com/groups/group-a`

### Requirement: Re-import enriches existing group metadata without changing assignment state
When an import item resolves to an existing canonical group URL, the catalog SHALL update the target's group name, region, park, direction, and import batch from the new import when those values are provided. It MUST NOT reset enabled state, priority, join gating, membership, assignment, or coverage state.

#### Scenario: Existing target receives metadata
- **WHEN** a previously URL-only group is re-imported with region `河南区域` and park `同文1工业区`
- **THEN** the existing target row has those metadata fields after import and any membership row for the group remains unchanged

### Requirement: Group target list supports optional region, park, and direction filters
The group target list SHALL accept optional exact-match filters for region, park, and direction. Omitting any filter SHALL leave that dimension unconstrained. Combining filters SHALL apply all provided filters together with existing status and enabled filters.

#### Scenario: Region-only filter
- **WHEN** the group target list is requested with `region=河南区域`
- **THEN** only targets whose region is `河南区域` are returned, regardless of park or direction

#### Scenario: Combined optional filters
- **WHEN** the group target list is requested with `region=北宁区域`, `park=周山工业区/VSIP 1`, and `direction=机械和电气`
- **THEN** only targets matching all three provided metadata values are returned

### Requirement: Filter facets expose stored regions, parks, and directions
The Facebook group target catalog SHALL expose filter facets derived from stored targets. Facets SHALL include regions with their known parks and a de-duplicated direction list. Null or empty metadata values MUST NOT appear as selectable facet values.

#### Scenario: Region facets include nested parks
- **WHEN** stored targets include region `河南区域` with parks `同文1工业区` and `同文2工业区`
- **THEN** the facets response includes `河南区域` with those two park options

#### Scenario: Empty metadata is omitted from facets
- **WHEN** stored targets include URL-only rows with null region, park, and direction
- **THEN** those null values are not returned as selectable facets
