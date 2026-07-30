## MODIFIED Requirements

### Requirement: Fail-closed button fallback
The button fallback SHALL exclude page-header, reaction, and in-video media controls and SHALL scope candidates relative to the freshly active video. A control MUST retain a bounded normalized visible fraction and span before it may establish an axis. Axis classification SHALL use viewport-normalized relationships among clipped visible control rectangles, the active video, and the viewport rather than raw control dimensions or absolute pixel gaps. It SHALL identify a vertical rail from semantically identified and predominantly Y-separated previous/next controls in one outer side lane and select only its unique lower forward control, or identify a horizontal rail from predominantly X-separated controls on opposite sides of the video and select only its unique right forward control. Unknown same-side controls MUST NOT establish a vertical rail; an unknown candidate MAY establish direction only as part of one unique opposite-side horizontal pair. One unique explicitly next-labelled overlay MAY prove a horizontal axis without a previous control only when its normalized topology is adjacent to the video, occupies substantial viewport width and height, substantially overlaps the video's height, and fills most of the remaining right-side gutter through the viewport edge. Axis evidence SHALL remain independent from safe pointer-target eligibility: disabled previous controls and non-click-safe overlays MAY establish layout structure, but they MUST NOT be clicked. A disabled or occluded forward control MUST establish no input-eligible axis. Pointer coordinates SHALL be exposed only for an enabled, fully visible, viewport-proportional control whose center-point hit test resolves to that control or its descendant. Ambiguous, single generic, moved, or axis-drifting controls MUST NOT be clicked.

#### Scenario: First vertical Reel with disabled previous control
- **WHEN** the previous control is disabled and a unique enabled next control forms one vertical rail with it beside the active video
- **THEN** the driver SHALL classify the layout as vertical and select only the lower enabled next control

#### Scenario: Horizontal previous and next controls
- **WHEN** one previous control is left of the active video and one enabled next control is right of it on the same horizontal rail
- **THEN** the driver SHALL classify the layout as horizontal and select only the right control

#### Scenario: One viewport-scale horizontal next overlay
- **WHEN** one unique next-labelled overlay is adjacent to the active video, occupies substantial viewport width and height, substantially overlaps the video, and fills the remaining right-side gutter through the viewport edge at any supported viewport size
- **THEN** the driver SHALL classify the layout as horizontal from that normalized topology
- **AND** it SHALL expose no pointer coordinates when the forward overlay is not a safe bounded click target

#### Scenario: Compact control beside a small video is not an overlay
- **WHEN** one compact generic next control fills a small gutter beside a transient small video
- **THEN** the driver SHALL expose no axis or pointer target

#### Scenario: Outer vertical rail beside a wide video
- **WHEN** a previous/next pair is Y-separated in the outer portion of the right-side gutter and a separate reaction column is nearer the active video
- **THEN** the driver SHALL classify only the outer pair as the vertical navigation rail
- **AND** it SHALL select only the lower enabled next control

#### Scenario: Reaction controls do not form a vertical rail
- **WHEN** two same-side controls with unknown or reaction semantics occupy positions that otherwise resemble an outer vertical pair
- **THEN** the driver SHALL refuse unknown vertical pairing and expose no axis or pointer target

#### Scenario: Disabled forward control blocks input
- **WHEN** a structural pair has a disabled next control
- **THEN** the driver SHALL expose no input-eligible axis or pointer target

#### Scenario: Offscreen remnants do not establish an axis
- **WHEN** previous and next controls retain only an insignificant clipped fraction inside the viewport
- **THEN** the driver SHALL ignore them and expose no axis

#### Scenario: Forward control is occluded
- **WHEN** the unique axis is proven but the forward control is not the topmost actionable element at its center point
- **THEN** the driver SHALL expose neither an input-eligible axis nor pointer coordinates

#### Scenario: Ambiguous next controls
- **WHEN** multiple credible axes or forward controls remain after semantic and structural scoping
- **THEN** the driver SHALL perform zero button clicks and SHALL return no next Reel
