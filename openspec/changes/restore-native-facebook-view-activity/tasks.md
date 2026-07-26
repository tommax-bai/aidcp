## 1. Shared Facebook evidence rules

- [x] 1.1 Move the strict canonical Feed-video identity predicate into the shared Facebook identity module without changing the legacy boundary.
- [x] 1.2 Reuse the existing Facebook companion formatters from Native instead of keeping independent read wording.

## 2. Native projection and deduplication

- [x] 2.1 Project eligible single-card Reels and unique Feed videos into structured activity events with `statsDelta.views=1`.
- [x] 2.2 Retain session-lifetime canonical projection witnesses and suppress only the matching later local `note_open`, while continuing to report detail data to Cloud.
- [x] 2.3 Add focused Native session parity tests for success, deduplication, malformed/ambiguous batches, later detail, and unchanged ordinary Feed behavior.

## 3. Validation and delivery evidence

- [x] 3.1 Run focused Native and legacy Facebook session tests plus relevant Edge acceptance coverage.
- [x] 3.2 Run Edge typecheck and strict OpenSpec validation.
- [x] 3.3 Record owning repository, local commit SHA, validation evidence, and explicit non-deployment boundary.

<!-- implementation-evidence
edge_repo=/Users/baitianxing/codes/aidcp-edge.wt/restore-native-facebook-view-activity
edge_commit=b188f7d821b917fa5a1dba52213999742e0d7a28
control_repo=/Users/baitianxing/codes/aidcp.wt/restore-native-facebook-view-activity
control_commit=this-change-metadata-commit
native_session_test=17_pass
legacy_facebook_session_test=54_pass
post_identity_test=11_pass
protocol_acceptance_test=23_pass
edge_typecheck=pass
openspec_strict_validation=pass
deployment=not_performed
packaging=not_performed
real_browser_actions=not_performed
-->
