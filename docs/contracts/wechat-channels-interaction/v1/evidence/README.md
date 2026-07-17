# Real-session request evidence

The JSON manifest in this directory records structural request and response shapes from one authorized AdsPower video-channel session. It intentionally contains no Cookie, token, raw key, finder ID, message body, QR data, debug address, or raw HAR.

Evidence is deliberately narrow:

- authorization identity and content-list shapes were observed read-only;
- the interaction-page post list returned one post with `commentCount=0` and `commentList=[]`;
- DM history and session-info returned empty arrays;
- non-empty comment, DM session and DM history semantics remain unverified;
- no comment or DM write endpoint was observed or dispatched.

The implementation may treat those empty responses as successful synchronization. It must fail closed on non-empty shapes until a separate sanitized capture extends the evidence.
