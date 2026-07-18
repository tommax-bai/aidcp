## ADDED Requirements

### Requirement: Manual browser inspection opens the selected local profile without an engine dependency

For a current customer-visible WeChat Channels environment, the Electron client SHALL provide a manual "打开浏览器" action that opens or reuses that environment's local AdsPower profile. The action SHALL use the local bundled runtime and LocalAPI directly, MUST NOT require Cloud reachability, an online environment engine, or active WeChat authentication, and MUST NOT start, resume, pause, stop, or attach the environment engine.

#### Scenario: Engine is stopped and the operator opens the browser

- **WHEN** the selected customer-visible WeChat Channels environment has a valid local AdsPower profile but its engine is stopped or disconnected
- **AND** the operator clicks "打开浏览器"
- **THEN** the Electron main process prepares the local AdsPower runtime/kernel and opens or reuses that profile
- **AND** the environment engine remains stopped and no Cloud browser-control request is sent

#### Scenario: WeChat authentication is not active

- **WHEN** WeChat authentication is waiting for login, requires reauthentication, requires verification, or is still unconfirmed
- **THEN** the manual browser-open action remains available for that valid local environment
- **AND** a successful local open MUST NOT change or claim the WeChat authentication result

### Requirement: Local browser inspection is scoped and non-arbitrary

The renderer SHALL send only the selected `envKey`. The Electron main process SHALL revalidate a current customer session, membership in the authoritative customer-visible environment set, authoritative `wechat_channels` platform, and an exact matching local AdsPower handle. The main process SHALL derive the profile id, LocalAPI authority, credentials, start URL, kernel version, and launch arguments. It MUST NOT accept a renderer-supplied profile id, URL, API base, token, headers, launch arguments, or stop action.

#### Scenario: Renderer submits an out-of-scope environment

- **WHEN** the renderer submits an environment that is not visible to the current customer, is not authoritatively a WeChat Channels environment, or has no exact local AdsPower handle
- **THEN** the main process rejects the request before any LocalAPI call
- **AND** MUST NOT fall back to the currently selected or another local profile

### Requirement: Browser inspection shares the main-process LocalAPI serialization boundary

The manual open call SHALL share the Electron main process's existing serialized AdsPower LocalAPI queue so it does not create a second unsynchronized request lane. Its write authority SHALL be limited to `browser/start`; it MUST NOT expose browser stop/close or general LocalAPI access to the renderer.

#### Scenario: A list request and manual open overlap

- **WHEN** a profile list request and a manual browser-open request arrive concurrently
- **THEN** the main-process LocalAPI client serializes them with the configured minimum interval
- **AND** each failure is reported honestly without fake browser-open success

### Requirement: Later explicit engine startup reuses the manually opened profile

After local browser opening succeeds, the shell SHALL remember that the selected profile is already running so a later explicit engine start follows the existing adoption path and does not intentionally open a second instance. The local-open action itself MUST NOT initiate that later startup.

#### Scenario: Operator opens browser and later starts engine

- **WHEN** manual browser opening succeeds while the engine is stopped
- **AND** the operator later explicitly starts the environment engine
- **THEN** the shell treats the profile as already running and follows the existing adoption path
- **AND** the earlier manual-open action is not reclassified as an engine start
