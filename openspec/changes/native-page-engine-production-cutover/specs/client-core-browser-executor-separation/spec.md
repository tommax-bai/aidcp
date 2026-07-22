## ADDED Requirements

### Requirement: The browser-independent core SHALL supervise Native only after page admission

The Edge core SHALL remain online without a browser or Native page session. For Xiaohongshu `page_automation`, it SHALL start/attach the browser provider, complete existing CDP readiness and real-page identity admission, acquire the page-task lease, then supervise the Native Page Engine for that executor. Starting the core or performing `local`, `cloud`, or `platform_api` operations MUST NOT start Native or acquire a browser slot.

#### Scenario: Core is online with browser closed
- **WHEN** a trusted environment has no admitted page-automation work
- **THEN** the Edge/Cloud core remains online while no Xiaohongshu Native session or browser slot exists

#### Scenario: Page automation is admitted
- **WHEN** a Xiaohongshu page operation passes the complete existing admission chain
- **THEN** the core starts or reuses the matching Native executor session and hands it the admitted loopback endpoint

### Requirement: Native failure MUST remain scoped to the page executor

A Native process crash, protocol failure, or CDP-session failure SHALL fail or recover the active page task honestly while the browser-independent Edge core and Cloud connection remain alive. The core MUST NOT hide the failure by reporting the environment as successfully executing, and MUST NOT start the legacy Xiaohongshu JavaScript executor.

#### Scenario: Native crashes during page read
- **WHEN** Native exits before any write dispatch
- **THEN** the page task receives an explicit executor failure while the Edge core stays connected and can accept browser-independent operations

#### Scenario: Native crashes after a possible write
- **WHEN** Native exits after dispatch may have occurred
- **THEN** the task is surfaced as ambiguous/needs-review under the existing contract and is not replayed through JavaScript

### Requirement: Non-Xiaohongshu executors MUST remain isolated

The Native Xiaohongshu cutover MUST NOT route Facebook, Douyin, WeChat Channels, or other platform operations into the Xiaohongshu Native adapter and MUST NOT remove their required executors from the package.

#### Scenario: Facebook page command is admitted
- **WHEN** the active platform is Facebook
- **THEN** the existing Facebook executor handles it and no Xiaohongshu Native session is created

