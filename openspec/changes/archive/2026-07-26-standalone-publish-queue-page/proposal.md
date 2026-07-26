## Why

The admin Content page currently mixes the editorial ledger with a large operational publish-queue surface. As active drafts and queued tasks grow, operators cannot scan publishing work as a queue, while the content history is pushed below unrelated pipeline detail.

## What Changes

- Add a dedicated `/publish-queue` destination under the Content navigation group.
- Move the existing truthful lifecycle view and queued publish-task list from `/content` to the dedicated page without changing their Cloud data sources or status semantics.
- Give the standalone page an operational summary for active drafts, human-waiting drafts, and queued tasks, followed by separate active-work and queued-work regions.
- Keep draft editing, approval, rejection, and published history on `/content`; queue items waiting for human approval link operators back to the corresponding content record instead of duplicating approval behavior.
- Preserve active/recent/terminal separation, the eight-stage lifecycle evidence, and legacy queue fallback while removing the operator-facing raw-field disclosure.
- Group active journeys by account: show accounts in a horizontally scrollable selector and render every active task for the selected account in the detail area below.

## Capabilities

### New Capabilities

- `admin-publish-queue-page`: Defines the standalone admin route, navigation placement, operational hierarchy, lifecycle rendering, and handoff to content approval.

### Modified Capabilities

- `console-panel-api`: Relocates the existing publish queue and queued-task presentation requirement from the Content page to the standalone Publish Queue page without changing API semantics.

## Impact

- `aidcp-console`: route metadata, Content page composition, a new Publish Queue page/component, focused tests, and queue-specific responsive styles.
- OpenSpec: a new page capability plus an updated console-panel presentation requirement.
- No Cloud API, protocol, persistence, publish execution, approval, or risk-state change.
