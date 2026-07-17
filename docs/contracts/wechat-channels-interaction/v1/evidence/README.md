# Real-session request evidence

The JSON manifests in this directory record structural request and response shapes from one authorized AdsPower video-channel session. They intentionally contain no Cookie, token, raw key, finder ID, message body, QR data, debug address, or raw HAR.

Evidence is deliberately narrow:

- authorization identity and content-list shapes were observed read-only;
- non-empty DM session-info participant fields were observed read-only on 2026-07-17; only field names/types and privacy boundaries were persisted;
- the 2026-07-16 capture records the earlier empty-only boundary;
- the 2026-07-17 capture records the non-empty comment-list and DM-history field sets, opaque cursors, Cloud persistence counts and client presentation result;
- comment roots/replies and DM sessions/messages are parsed from sanitized field allowlists; unknown DM types remain `unknown` and private raw/image encryption fields are discarded;
- no comment or DM write endpoint was observed or dispatched.

The implementation may synchronize the verified empty and non-empty read shapes. It must still fail closed on missing required identity, direction, timestamp, pagination or stable-ID fields. Multi-page real-account pagination and multi-account isolation remain separate acceptance work.
