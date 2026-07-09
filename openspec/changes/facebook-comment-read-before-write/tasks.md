## 1. Edge — read post caption + comments

- [x] 1.1 Protocol: optional `NoteDetailPayload.comments?` (byte-identical both protocol.ts; reuse message, count unchanged).
  <!-- aidcp-edge landed on master e09bb80. -->
- [x] 1.2 `FacebookCommentExecutor.openPost` extracts post caption (often empty for photo posts) + top N other-people comment texts (nested role=article; strips author name / UI chrome / bare-name tag comments; dedups; honest empty, never fabricates). Reports via note.detail (content + comments) in the handler.
  <!-- aidcp-edge e09bb80: readPostContent + buildPostContentJs; validated live on a real PR-group post (photo post no caption + the substantive Spanish comment, name/tag comments filtered). 2 extraction plumbing tests. Edge full 753/753. -->

## 2. Cloud — compose after open, grounded + local language

- [x] 2.1 `facebook-edge-steps.openPost` returns note.detail content (postText) + comments.
  <!-- aidcp-cloud landed on master 5947d3d. -->
- [x] 2.2 Reorder `runFacebookTargetedTask`: edge-online -> (real) canDo+dailyCap -> search -> pick candidate -> openPost(read caption+comments) -> compose(keyword,container,postText,comments) -> validate -> shadow stops (read-only browse, no submit) / real dedup+submit. Relevance gate uses [keyword + postText + comments] context. Anti-double-post + success accounting + kill switch unchanged.
  <!-- aidcp-cloud 5947d3d. -->
- [x] 2.3 `facebookCompose` prompt: include the post caption + other comments; instruct writing in the SAME language as the content (never the Chinese UI language unless the content is Chinese); respond to the discussion. Fixes the weak_relevance / Chinese-in-a-Spanish-group bug.
  <!-- aidcp-cloud 5947d3d (server.ts). -->
- [x] 2.4 Shadow becomes a read-only browse (search+open+compose+validate, never submits); tests updated (shadow posts search.execute+note.open but never interaction.comment). New test: compose runs after open and receives caption+comments. Full cloud 1619/1619, acceptance 46/46, typecheck clean.

## 3. Rollout

- [x] 3.1 Deploy: cloud master 5947d3d live on dev (read-before-write present; healthcheck green; isales intact); edge runs from master worktree (e09bb80) for the live test. Backup cloud.bak.20260709-111555.tar.gz.
- [ ] 3.2 Real-machine: re-trigger `/comment FBProbe` on the armed disposable account → expect a Spanish comment grounded in the PR-group discussion that passes relevance and (if F1 production verify holds) posts server-confirmed. Records into facebook-scheduled-comment 7.4 + backlog 簇 14.
- [x] 3.3 `openspec validate facebook-comment-read-before-write --strict`.
