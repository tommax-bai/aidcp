## ADDED Requirements

### Requirement: Final packages exclude all migrated platform browser rules
The desktop build SHALL exclude migrated Facebook and WeChat browser-rule modules, production-reachable page probes, development probe scripts, standalone embedded-router sources, and source maps from distributable JavaScript and packaged resources. Verification MUST inspect both the production import graph and the final ASAR/resources rather than inferring absence from source imports.

#### Scenario: Migrated Facebook marker remains
- **WHEN** production-dist or final-package inspection finds a denied Facebook executor/probe path or representative cleartext page-rule marker
- **THEN** the desktop build fails and no distributable is accepted

#### Scenario: Development probe is accidentally packaged
- **WHEN** any `scripts/*probe*` input or equivalent calibration payload appears in ASAR or packaged resources
- **THEN** final-package verification fails

### Requirement: Expanded Native artifact is package-compatible
The packaged Native Page Engine manifest SHALL declare the protocol and adapter coverage required for Xiaohongshu, Facebook, and WeChat browser-session capture, and the executable SHALL match the target architecture and verified digest. Missing platform coverage or a mismatched artifact MUST fail packaging/startup.

#### Scenario: Facebook adapter is absent
- **WHEN** a customer package requires Facebook but its Native manifest does not declare the compatible Facebook adapter/protocol
- **THEN** package verification fails before a distributable is emitted

#### Scenario: Packaged smoke test opens each adapter
- **WHEN** the final packaged resource is smoke-tested
- **THEN** the executable starts outside ASAR and accepts bounded session/protocol validation for every declared platform adapter
