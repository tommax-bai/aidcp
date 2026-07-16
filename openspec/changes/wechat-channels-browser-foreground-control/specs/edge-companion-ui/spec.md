## ADDED Requirements

### Requirement: Video-channel workspace exposes truthful browser foreground controls
The Electron video-channel workspace SHALL show an environment-scoped browser control when authorization is active: `browserState=closed` SHALL expose “打开浏览器”, `browserState=open` SHALL expose “转入后台”, and transitional states SHALL show a disabled progress label. Reauthorization and customer logout controls MUST remain separate actions with distinct copy.

#### Scenario: Active browser is closed normally
- **WHEN** the selected video-channel environment reports `status=active` and `browserState=closed`
- **THEN** the workspace states that API background operation is active and exposes “打开浏览器” for that environment

#### Scenario: Active browser is visible
- **WHEN** the selected video-channel environment reports `status=active` and `browserState=open`
- **THEN** the workspace states that the browser is open and exposes “转入后台” without labeling the account as newly logged in

#### Scenario: Browser action is awaiting Edge truth
- **WHEN** the customer API accepts an open or close request but the target browser state has not yet arrived
- **THEN** the workspace displays a waiting-for-Edge message and MUST NOT claim the browser has opened or closed

#### Scenario: Authorization requires user action
- **WHEN** auth status is login required, reauthorization required, or challenge required
- **THEN** the workspace shows the existing login or challenge action instead of the ordinary foreground/background control
