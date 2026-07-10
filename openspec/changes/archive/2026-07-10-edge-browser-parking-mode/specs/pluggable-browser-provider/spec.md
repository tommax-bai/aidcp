## ADDED Requirements

### Requirement: Browser window parking keeps driven browser headful
The edge browser startup path SHALL support browser window parking for both AdsPower and self providers without switching to headless or minimized mode. Parking SHALL preserve the fixed desktop viewport required by the driven web platform and SHALL apply after CDP attach as the authoritative window placement step.

#### Scenario: Parking is applied after CDP attach
- **WHEN** edge has attached to a driven browser page and a browser parking mode is configured
- **THEN** edge applies normal-window bounds over CDP for the selected or effective parking mode
- **AND** the browser remains headful and non-minimized

#### Scenario: AdsPower receives early launch position hint
- **WHEN** AdsPower provider starts a browser and a parking position is configured
- **THEN** the provider includes a best-effort launch position hint together with the fixed desktop window size
- **AND** CDP window placement after attach remains the authoritative correction step

### Requirement: Browser parking verifies page visibility before continuing
After applying browser parking, edge SHALL verify that the driven page remains visible and keeps a valid desktop viewport. If verification fails, edge SHALL degrade to a recoverable visible placement or stop honestly; it MUST NOT continue automated interaction while `document.hidden` is true or `document.visibilityState` is not `visible`.

#### Scenario: Parking preserves visible page
- **WHEN** edge applies browser parking and the visibility probe returns `document.hidden=false`, `document.visibilityState='visible'`, and a valid desktop viewport
- **THEN** edge continues normal startup and operation

#### Scenario: Parking makes page hidden
- **WHEN** edge applies browser parking and the visibility probe returns hidden or non-visible state
- **THEN** edge falls back to `edge-strip` or a normal visible position
- **AND** it MUST NOT continue in the hidden state as if parking succeeded

#### Scenario: Preferred parking display is unavailable
- **WHEN** the selected mode is `parking-display` but no non-primary display bounds are available
- **THEN** edge uses `edge-strip` as the effective placement
- **AND** it reports the fallback in logs or UI status rather than silently pretending a parking display was used
