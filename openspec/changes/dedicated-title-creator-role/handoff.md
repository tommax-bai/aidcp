# 交接文档 — dedicated-title-creator-role

> 给**新 session**：本 change 已 propose 完成（proposal/design/specs/tasks 四件套齐、`openspec validate --strict` 通过、已提交推送），**尚未实装代码**。你的任务是实装它。
> 阅读顺序：**本文 → proposal.md → design.md → tasks.md**。实装入口：`/opsx:apply dedicated-title-creator-role`。

---

## 0. 一句话目标

把"标题生成"从内容生成里拆成一个**独立角色**，排在**正文定稿之后、发布之前**，依据定稿正文单独写标题；顺带修掉一个已实测的失真红线 bug——**LLM 写的标题被整条丢弃，真正发出去的"标题"其实是正文首行盲切 30 字**。

四条已拍板的产品决策（**不要再改方向，用户已定**）：
1. 独立 `TitleCreator` 角色，输入取**最终定稿正文** `assembledContent.finalContent`（非草稿）。
2. **标题失败 = 发布失败**：`fallback:'abort'`，不派生兜底、不造假标题；默认 `timeoutMs=120000`。
3. **发布严格接在标题就绪事件之后**：`PublishExecutor` 改 `watchKeys=['gateDecision','titleSelection']` + `waitAll:true`；因此**审批卡发出时标题必已就绪、卡片显示真实标题**。
4. **长度收口云端一处、字形安全、记录==真实发布**；**edge 不做任何标题策略**（移除 edge 截断）；模型默认 qwen3.7-max、后台「角色配置页」可独立配。

---

## 1. 当前状态（务必先认清，别重复劳动）

**已完成：**
- 本 change 四件套已写好并校验通过；已提交推送到本仓 `main`（commit `3e5548d`）。
- **临时修复已部署在线、当前发帖可用**：edge `472cda1`（填标题截断 20）+ cloud `9630364`（prompt≤18 + parseOutput 截断 20）。cloud 这 2 个文件已 rsync 到 ECS（备份 `/opt/aidcp/cloud.bak.20260621-201534.tar.gz`）。
- **飞书全自动发帖真机首发成功**：publish-11 已发到真账号（`publish_log` id=11 `status=published`）。

**未完成（=你要做的）：**
- 实装 tasks.md 的全部 task（新角色 + 黑板字段 + clamp util + executor 接线 + 模型配置 + edge 移除截断 + 测试 + 部署 + 真机验证）。

**关键衔接**：临时修复就是现在让发帖能用的东西。本 change 的正解里要**移除 edge 那道截断**（task 6.1，即撤回 `472cda1`），所以 **edge 撤截断必须和云端 `TitleCreator`（保证 ≤18）同批上线**——否则云端还在发长标题、单撤 edge 会复发"发布按钮静默失效"。

---

## 2. 三个必须先知道的"地雷"

1. **BLOCKING task 0 — 先坐实 abort 的失败语义**。标题 `abort` 后不写 `titleSelection`，下游 `waitAll` 缺键。要先确认现状：流水线是**即时判 `failed`** 还是**干等 `pipelineTimeoutMs`(18 分钟)**。读 `base-role.ts` 失败分支 + `pipeline-context.ts` 的 `waitAll` + `PublishOrchestrator` 如何结束 run。若是干等超时，本 change 内要让标题失败**即时**冒泡为 `failed`（不留 18 分钟挂死）。**这是最大风险点，先做 task 0 再动别的。**
2. **并发会话在改两仓 `protocol.ts`**（comment-like change）。本 change **绝不碰 `protocol.ts`**（无新消息类型）。提交务必**精确 `git add` 仅本 change 文件、绝不 `git add -A`**（这台机器多会话共用同仓、有未提交 WIP）。
3. **行号会漂移**。design/tasks 里的 `文件:行` 是写作时快照；`publish-executor.ts`、`prompts.ts` 近期被标题相关 commit（`9630364`/`3c5214c`）动过。**实装前先 `git pull --rebase`，按符号（函数/字段名）定位，不要死认行号。**

---

## 3. 红线（实装中不可破）

- MUST NOT 静默假成功：标题生成不出合规结果就**诚实判发布失败**，绝不派生/编造标题顶替。
- **记录 == 真实发布**：长度收口必须发生在 **DB 写入与下发 edge 之前**（收口在云端 `TitleCreator`/`clampTitle`）；edge 端同类截断一并移除，edge 只原样填、失败如实回报。
- `clampTitle` **绝不返空**、不从汉字词/emoji 代理对中间盲切（用 `Intl.Segmenter` 按 grapheme）。
- 不动协议、不加 DB migration、不碰风控/浏览闭环、不碰同机 isales。
- 保留 `createdContent.title` 及 `content-creator.ts:73` 截断不动（`ImagePlanner` 经 `prompts.ts:240` 仍用它配图，删了坏配图）。

---

## 4. 仓库与前置检查

三仓同级：本仓中控 `.`（branch `main`）、`../aidcp-cloud`（`master`，云端主战场）、`../aidcp-edge`（`master`，仅一处改动）。

**动手前 §0 前置检查（CLAUDE.md）：**
- `ls -d ../aidcp-edge ../aidcp-cloud` 确认子仓在本机。
- 部署前 `ls -l ~/codes/isales-4.pem` 确认私钥存在且 `chmod 600`。

---

## 5. 要改的文件（按符号定位，行号仅参考）

**aidcp-cloud（主）：**
- `src/publish-agent/types.ts` — 加 `TitleSelection{title,source:'llm'|'derived',decidedAt}`；`PipelineFields` 加 `titleSelection`。
- `src/publish-agent/title-clamp.ts`（新）— `clampTitle(s, max=18)` 字形安全 + `firstSentence(s)`。
- `src/publish-agent/prompts.ts` — 加 `buildTitlePrompt(body, persona, styleType, seedTitle?)`（短提示，复用 `BANNED_PHRASES`）。
- `src/publish-agent/roles/title-creator.ts`（新）— 角色本体（`watch assembledContent`→`titleSelection`，`abort`，120s，重试≤2 + clamp，失败抛错不写键）。
- `src/publish-agent/roles/index.ts` — 导出。
- `src/publish-agent/roles/publish-executor.ts` — `watchKeys`+`waitAll`、`extractInput`+`titleSelection`、全部标题出口（DB/序列/审批卡/manual_review/abort）改读 `input.titleSelection.title`、`deriveTitle` 降级为字段缺失兜底（内部也用 `clampTitle`）。
- `src/config/role-catalog.ts` — 加目录行（`publish:TitleCreator`/技术帖标题创作/publish/text/tunableTemperature）。
- `src/server.ts` — `registerRole(new TitleCreatorRole({ llmClient: roleLlm('publish:TitleCreator') }))`（装配器之后；注册顺序与正确性无关）。

**aidcp-edge（一处）：**
- `src/flows/publish-command-handlers.ts` — 移除 `XHS_TITLE_MAX`（约 `:166`）与 `runFillField` 标题分支 `slice`（约 `:370`），标题原样填入；正文分支不动。同步更新任何断言"标题被截断"的单测为"原样填入"。

---

## 6. 测试与部署纪律

**回归（每仓改完）：** 先 `npm run test:acceptance` → 再全量 `npm test` → 再 `npm run typecheck`，全绿。红线 `AC-PUB-*`/`AC-PROTO-*`/`AC-RISK-*` 不破，新增 `AC-TITLE-*`（clamp 边界/不返空/单超长CJK词/emoji不拆/空正文；角色 abort 即时失败不写键；标题全路径一致==记录==下发==卡片）。

**部署（云端 + edge 同批）：**
1. 云端：§0 私钥/子仓检查 → ECS `tar` 备份 `.bak.<ts>.tar.gz` → `rsync --dry-run` 先 surface scope（**只带本 change 文件、绝不带并发会话的 `protocol.ts`**；cloud 从源码 `tsx` 跑、无需 build）→ rsync → `systemctl restart aidcp-cloud.service` → healthcheck（active + 8787 监听 + 飞书长连接已建立 + PG + **isales 未触碰**）→ 失败回滚。SSH：`ssh -i ~/codes/isales-4.pem root@121.89.85.150`（命令需 `dangerouslyDisableSandbox`）。
2. edge：本地重启，连云端。

---

## 7. 怎么跑一次真机验证（task 7.3）

每次云端 restart 会断掉 edge 的 WS（无自动重连），所以**先重启 edge 再测**：
```
cd /Users/baitianxing/aidcp-edge && AIDCP_AUTO_BROWSE=false AIDCP_CLOUD_URL=ws://121.89.85.150:8787 npm start
```
（会拉起 Chrome on 9222、复用 `~/.aidcp-chrome-profile` 的小红书登录态；日志出现 `已连接云端 … 等待命令` 即就绪）

然后飞书群发 `/publish` → 审批卡**标题栏应是真实 ≤18 字标题** → 点「通过」→ 发布成功（页面 URL 跳 `/publish/success`）→ 核对 `publish_log.title` == 平台显示标题（≤18、未切碎）。

**小红书发布页校准锚点**（直驱 CDP 实证，验证/排障用）：上传图文 tab `div.creator-tab`；图片 input `input.upload-input`；标题 `input[placeholder="填写标题会有更多赞哦"]`（React 受控，须 `Input.insertText`）；正文 `.tiptap.ProseMirror`；发布按钮在**闭合 shadow** 内 `button.ce-btn.bg-red`（`DOM.getDocument{pierce}`+`getBoxModel` 取中心坐标点击）；成功信号 URL 跳 `/publish/success`。

**查 DB**（ECS，列名注意 `platform_post_id` 不是 post_id）：
```
ssh -i ~/codes/isales-4.pem root@121.89.85.150 'cd /tmp && sudo -u postgres psql -d aidcp -c "select id,status,char_length(title) tlen,left(title,30) title,platform_post_id,images_attached from publish_log order by id desc limit 4;"'
```

---

## 8. 收尾

tasks.md task 8：各 task HTML 注释标 `[x]` + `<!-- <repo> <sha> 备注 -->`（部署后加 `<!-- <date> deployed -->`）；三仓精确提交推送（本仓 `main`，cloud/edge `master`，commit 末尾带 `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`）；`openspec validate dedicated-title-creator-role --strict` → `openspec archive dedicated-title-creator-role`（delta 并入 `openspec/specs/publish-pipeline/`）。

---

## 9. 相关记忆 / 文档指针

- 记忆：`edge-no-strategy-honest-failure`（本 change 的失败哲学根据）、`publish-pipeline-deployed`（发帖链现状 + 标题 bug 始末 + 发布页锚点）、`ecs-deploy-scope-full-master`、`precise-git-add-concurrent-sessions`。
- 部署台账：`docs/handoff-2026-06-05.md`（顶部注记块为现役版本来源）、`aidcp-cloud/docs/deployment-ecs.md`。
- 本 change：`openspec/changes/dedicated-title-creator-role/{proposal,design,tasks,specs/publish-pipeline/spec}.md`。
