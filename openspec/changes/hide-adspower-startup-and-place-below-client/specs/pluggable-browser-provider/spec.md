## MODIFIED Requirements

### Requirement: Browser window parking keeps driven browser headful
The edge browser startup path SHALL support browser window parking for both AdsPower and self providers without switching to headless or minimized mode. When Electron supplies a startup staging position, the browser provider SHALL request that best-effort position together with the fixed desktop window size and MUST NOT simultaneously request a maximized startup state. The staging position SHALL be independent from the selected final parking bounds. Parking SHALL preserve the fixed desktop viewport required by the driven web platform and SHALL apply after CDP attach as the authoritative window placement step.

#### Scenario: Parking is applied after CDP attach
- **WHEN** edge has attached to a driven browser page and a browser parking mode is configured
- **THEN** edge applies normal-window bounds over CDP for the selected or effective parking mode
- **AND** the browser remains headful and non-minimized

#### Scenario: Provider receives an off-display startup staging hint
- **WHEN** Electron knows the local display geometry and starts a driven browser with parking enabled
- **THEN** the provider includes a best-effort position beyond the right-most known display together with the fixed desktop window size
- **AND** the provider does not include `--start-maximized` in that launch
- **AND** the final selected parking bounds are still applied authoritatively after CDP attach

#### Scenario: Standalone launch has no staging geometry
- **WHEN** a provider is started without an Electron-supplied window position
- **THEN** it MAY retain the historical maximized fallback needed to defeat a remembered narrow profile
- **AND** it MUST retain the fixed desktop window-size requirement

