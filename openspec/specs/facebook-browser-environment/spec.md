# facebook-browser-environment Specification

## Purpose
TBD - created by archiving change facebook-browser-env-and-login. Update Purpose after archive.
## Requirements
### Requirement: Facebook profile startup uses AdsPower/CDP without credential automation

edge SHALL support starting or attaching to a Facebook AdsPower profile through the existing browser-provider/CDP boundary. The profile MUST already be manually logged in or able to prompt the operator for manual login; the system MUST NOT script passwords, 2FA, device confirmations, or checkpoint solving. Missing profile id, missing debug port, or unreadable login identity MUST fail honestly.

#### Scenario: Logged-in Facebook profile attaches through CDP
- **WHEN** `AIDCP_PLATFORM=facebook` and a valid AdsPower profile id is configured
- **THEN** edge starts/attaches through the existing provider, obtains a CDP endpoint, opens/selects a Facebook tab, and proceeds only after identity probing succeeds

#### Scenario: Profile not logged in fails honestly
- **WHEN** the Facebook profile opens to login or no stable identity can be read
- **THEN** edge reports a login/identity failure and does not start account-scoped browsing or commenting

### Requirement: Facebook storage probe redacts all secret values

The Facebook storage probe SHALL inspect cookies, localStorage, sessionStorage, IndexedDB, and service-worker/cache presence only to the extent needed to understand persistence shape. Probe output MUST NOT include raw cookie values, token values, raw localStorage/sessionStorage key names, raw IndexedDB/cache names, IndexedDB record payloads, request headers, or credentials. It MAY include origin names, counts, expiry presence, value length buckets, redacted key/name hashes, and boolean/token-like presence markers.

#### Scenario: Storage summary omits values
- **WHEN** the storage probe runs on a logged-in Facebook profile
- **THEN** the output contains only redacted metadata such as counts/origins/key-name hashes and contains no raw cookie, token, localStorage key, sessionStorage key, IndexedDB/cache name, IndexedDB payload, or header values

### Requirement: Facebook page structure probes map Page, Group, and post surfaces

Read-only Facebook probes SHALL collect current page URL, page type, post container candidates, permalink/id candidates, author/text/comment-count candidates, visible comment region shape, and virtualization/expand-controls observations for operator-specified Page, Group, and post URLs. Probes MUST NOT click publish/submit controls or mutate account state unless an explicit gated-post mode is enabled.

#### Scenario: Read-only structure probe does not mutate
- **WHEN** the page structure probe runs against a Facebook Page, Group, or post URL without gated-post mode
- **THEN** it records structural observations and screenshots/logs safe metadata only, and does not submit comments, reactions, follows, joins, or posts

### Requirement: Facebook comment editor probe is read-only by default

The comment editor probe SHALL locate and focus the Facebook comment editor, test whether text enters the controlled model, observe send-button enablement, then clear or abandon the editor without submitting by default. Any real submit test MUST require an explicit env flag, a disposable account, and an operator-supplied test target.

#### Scenario: Editor input probe does not submit by default
- **WHEN** the comment editor probe runs without the gated submit flag
- **THEN** it may focus/type/clear in the editor but MUST NOT press Enter or click a submit/send control that posts a comment

#### Scenario: Gated submit requires explicit target
- **WHEN** the gated submit flag is set but no disposable test target URL is provided
- **THEN** the probe refuses to submit and reports configuration error

### Requirement: Phase-0 gates block scheduled comment implementation

`facebook-browser-env-and-login` SHALL define and record Phase-0 outcomes before `facebook-scheduled-comment` can start: F1 server-confirmed comment verification feasibility, F2 URL/location checkpoint/login detection, and F3 AdsPower/CDP profile stability under low-frequency realistic use. Any failed gate MUST stop the scheduled-comment change until the design is revised.

#### Scenario: F1 failure blocks later commented success path
- **WHEN** the gated post probe cannot distinguish optimistic local rendering from server-confirmed comment acceptance
- **THEN** later Facebook automation MUST NOT report `commented`; `facebook-scheduled-comment` remains blocked pending redesign

#### Scenario: F2 failure blocks later automation
- **WHEN** checkpoint/login/full-page blocked states cannot be reliably detected by URL/location and page state
- **THEN** later automation remains blocked because it cannot fail closed safely

#### Scenario: F3 failure blocks later automation
- **WHEN** a disposable AdsPower Facebook profile checkpoints quickly under low-frequency probe operation
- **THEN** later scheduled-comment automation remains blocked pending provider/fingerprint/operator workflow review

