## Why

The DEV three-process deployment failed before synchronization because Bash parsed a variable immediately followed by Chinese punctuation as a longer, unset variable under `set -u`. The deployment path must reject this source pattern before it can interrupt a topology switch.

## What Changes

- Delimit shell variable expansions that are immediately followed by non-ASCII text in the Cloud multi-service deployment script.
- Add a static regression test that rejects unbraced shell variables adjacent to non-ASCII characters.
- Re-run the supported three-process deployment and verify all three AIDCP services.

## Capabilities

### New Capabilities

- `cloud-multi-service-deployment`: Safe execution and validation of the Cloud three-process deployment script.

### Modified Capabilities

None.

## Impact

The change affects `aidcp-cloud/deploy/multi-service/deploy-multi.sh`, one focused Cloud test, and DEV deployment evidence. It does not change application protocol, database schema, dependencies, or isales services.
