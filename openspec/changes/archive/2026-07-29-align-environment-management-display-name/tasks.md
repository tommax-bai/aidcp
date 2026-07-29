## 1. Renderer display projection

- [x] 1.1 Add an environment-management display projection that joins AdsPower profiles to fleet/roster by stable profile ID and delegates nickname priority to the shared resolver. <!-- repo=aidcp-edge; commit=88ff177; validation=fleet-console 92/92; deployment=not applicable; deviations=none -->
- [x] 1.2 Use the resolved name for management rows, accessible selection labels, proxy/platform/delete prompts and open-list refreshes while preserving stable IDs for every action. <!-- repo=aidcp-edge; commit=88ff177; validation=fleet-console 92/92 and diff review; deployment=not applicable; deviations=none -->

## 2. Regression coverage

- [x] 2.1 Add renderer integration coverage where the manual nickname differs from the AdsPower name, proving the rail and management surface agree and action payloads retain the profile ID. <!-- repo=aidcp-edge; commit=88ff177; validation=focused regression 1/1; deployment=not applicable; deviations=none -->
- [x] 2.2 Run focused environment-management and renderer identity tests. <!-- repo=aidcp-edge; commit=88ff177; validation=fleet-console 92/92 and renderer-smoke 3/3; deployment=not applicable; deviations=none -->

## 3. Validation and delivery

- [x] 3.1 Run the Edge typecheck and proportionate full test suite. <!-- repo=aidcp-edge; commit=88ff177; validation=acceptance 31/31, full 2716 passed 1 gated skip, typecheck passed; deployment=not applicable; deviations=AIDCP_E2E remained gated -->
- [x] 3.2 Run `openspec validate align-environment-management-display-name --strict`, record implementation evidence, and integrate the clean Edge and control commits. <!-- repo=aidcp; commit=8e716ff0; validation=openspec strict passed; delivery=aidcp-edge 88ff177 on origin/master; deployment=not applicable; deviations=no Edge installer built -->
