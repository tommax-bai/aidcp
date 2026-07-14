## ADDED Requirements

### Requirement: 发版不再需要改 console 源码的版本号

Publishing a new desktop installer SHALL consist of building the artifact and placing it in the target host's downloads directory. The release procedure MUST NOT require editing a version constant in console source, nor rebuilding and redeploying the console, in order for the download page to offer the new installer.

This removes the class of release bug where the page and the directory disagree: a forgotten source edit used to leave the page advertising an old version or linking to a file that was never uploaded, and the page had no way to detect that it was lying.

#### Scenario: 上架新包即生效

- **WHEN** a new signed installer is placed in a host's downloads directory
- **THEN** that host's download page offers it without any console source change, rebuild, or redeploy

#### Scenario: 版本号不再是需要跨分支对账的东西

- **WHEN** a release branch is cut from trunk
- **THEN** no installer version constant needs to be reconciled between the release branch and trunk, because the version is not carried in source
