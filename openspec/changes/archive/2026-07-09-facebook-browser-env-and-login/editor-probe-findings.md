# Facebook Editor Probe Findings

Date: 2026-07-06

Probe environment:

- AdsPower profile: `k1ebny3j`
- Target: Meta Page post permalink
- Probe artifacts: `/tmp/aidcp-fb-editor-probe-2026-07-06T03-47-37-180Z`
- Probe mode: focus, type, observe controls, clear; no submit

No comment was submitted. No credentials, cookies, tokens, storage values, or real account identifiers were saved.

## Result

The Page permalink comment editor accepted typed input and could be cleared without submitting.

Observed editor:

- selector shape: `div[contenteditable="true"][role="textbox"]`
- aria label: `写评论…`
- active element matched the chosen editor after focus
- marker text was accepted by the controlled editor
- `发布评论` control appeared after typing
- keyboard clear left final editor text length at `0`

Probe summary:

| Step | Result |
| --- | --- |
| Focus editor | passed |
| Insert marker via CDP text input | passed |
| Marker accepted by editor | passed |
| Send/post control observed | passed; label `发布评论` |
| Submit clicked | no |
| Keyboard clear | passed |
| Final text length | `0` |

The saved marker proof is only a hash: `3a3241490ceb6ba1`.

## Locator Notes

The editor was found without relying on brittle class names:

- `role="textbox"`
- `contenteditable="true"`
- aria label matching `写评论…`

Observed nearby controls:

- `发表评论`
- `发布评论`
- `发送给好友或发布到你的个人主页。`
- `用虚拟形象贴图评论`
- `用动图评论`
- `用贴图评论`

The runtime sender must distinguish between `发表评论` as an action/entry affordance and `发布评论` as the actual post/submit control after text is present.

## Implementation Implications

For the first implementation, the Facebook editor flow should:

1. Run login/challenge/blocking detection first.
2. Prefer a single-post permalink surface.
3. Locate `div[contenteditable="true"][role="textbox"]` with a comment-like aria label.
4. Focus the editor and verify `document.activeElement` is the chosen editor.
5. Use browser input events rather than raw `textContent` assignment.
6. After input, verify editor text was accepted and a post/submit control appears.
7. Before any production submit, require gated target approval and server-confirmed verification.
8. If running a no-submit probe, clear with keyboard selection and verify final text length is `0`.
