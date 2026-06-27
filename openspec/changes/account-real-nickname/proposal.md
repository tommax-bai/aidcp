## Why

后台「账号」列要显示登录账号的小红书真实昵称（如「工程师大白」），而不是占位串 / 24 位 userid。

**初版（已部分实装+部署）走错了架构,本提案纠正它。** 初版让 **edge 在握手时读昵称 + 写「诚实闸」判定要不要发**——这违背铁律「**edge 只执行原子操作、绝不做任何决策;一切决策/编排/数据判定收口云端、由云端角色驱动**」(CLAUDE.md §2,[[edge-execute-only-cloud-roles-decide]])。而且真机坐实:**昵称根本不在 feed 页 DOM 里,只在账号自己的主页才读得到**;初版「就地读 ID 一次成功→永不走进主页那条路」,所以实际永远采不到昵称。

纠正方向(经 §3 业界方案 + 3 路对抗评审,0 BLOCKER / 7 MAJOR 全收敛):**由一个云端角色驱动一次「访问自己主页」来采集昵称**。云端早有现成链路——角色 emit `profile_open{authorId}` → edge 纯执行打开 `/user/profile/<id>`、原样报 `profile.detail{nickname}`(抓不到诚实置空)。账号 ID 即 userid 即主页 id,故**云端拿自己连接的 accountId 当 authorId 下发即可**;edge 对「自己」与「他人」主页一视同仁、只执行。

## What Changes

- **新增云端角色 `nickname_enricher`(按连接)**:握手时同步算一次「需采集」(accountId 是真实 userid 非 `default` 且库内 `nickname IS NULL`)→ 会话开始(`feed.entered{session_start}`)时,若需采集则**暂停自主浏览 + 置在途标记 + 武装 ~20s 兜底超时**,emit 云端内部事件 `self.profile.capture{accountId}`;翻译为现成命令 `profile_open{authorId=accountId, direct:true}`;收到本人的 `profile.detail` 后 `setNickname` 持久化(非空才写)、清标记、恢复浏览、emit `feed.entered{back_to_feed}` 干净回 feed。**只在库内昵称为空时采,一旦写入此后不再绕路**(无放大、无持久 flag)。
- **隔离(红线:自己绝不进社交管线)**:本人主页访问**绝不**产生 `profile.browsed` / 关注决策 / 关注命令 / `interaction_feed` / 去重行。判据 `detail.authorId === 连接 accountId`(race-free),四处守卫:ProfileBrowser 本人早退、profile.done 关注自跳过、`server.ts` 全局观测 upsertMeta 自跳过、note-scoped 链对直驱自访问天然不触发。
- **edge(净缩,但非零;全部纯执行)**:
  - **revert 初版 28ba097 的昵称传输与决策**(`HelloPayload.nickname`、edge-client 透传/`setNickname`、`main.ts` 诚实闸、`self-identity` 自作用域昵称读)——就地路径 `displayName/redId` 置 `null`(**不**恢复无作用域 `readDisplay`,那会复活「feed 抓成被浏览作者名」的错配 bug)。
  - **新增一个通用纯执行能力** `ProfileOpenPayload.direct?: boolean`:`direct===true` 时 edge 直接 `Page.navigate` 到 `/user/profile/<authorId>`(而非在当前页 scrape 第一个作者链接);缺省/false 维持已部署 scrape 路径逐字不变(关注链路零回归)。edge 不带任何「这是自己」标志——云端独知。
  - **把昵称读与「数字渲染门」解耦**:`profile.detail` 即便 `extracted===false` 也带上 `.user-name`/`.user-nickname` + `document.title`(「<名> - 小红书」去尾)兜底,使昵称不依赖粉丝/获赞数渲染即可采到。
- **cloud revert 初版 hello 摄取**:`HelloPayload.nickname`、`handler.onHello` 摄取 + `recordAccountNickname` 依赖 + `server.ts` 接线——改由角色经注入的 `setNickname` 写。
- **保留(都在云端/展示层,复用)**:`accounts.nickname` 列 + 自愈 ALTER + 迁移 0021(均已部署)、`AccountStore.setNickname` 单写、panel-store 暴露 + 发布历史折叠、console `accountDisplayName` helper、`ProfileDetailPayload.nickname`(interaction-feed-enrichment 既有字段,角色直接消费)、`dev-run.sh` 去强制 default(身份引导,仅删过时注释)。

## Capabilities

### Modified Capabilities
- `accounts-master-data`: 「账号真实昵称」要求改为**由云端角色驱动一次本人主页访问采集**(edge 纯执行),并明确隔离(自己不进社交管线)、幂等(仅库内空时采)、风控中性、诚实失败、有界回 feed。废止初版「随握手由 edge 判定带回」。

## Impact

- **协议(两 sub-repo + docs,消息计数恒 56)**:
  - 两份 `protocol.ts`:`HelloPayload.nickname` **删除**;`ProfileOpenPayload.direct?: boolean` **新增**(逐字一致)。均为字段增删、**无新 MessageType**,`Record<MessageType,true>` 穷举与 `AC-PROTO-02` 计数 56 不变。
  - `self.profile.capture` 是**云端内部事件**(EventBus/RoleEventMap),**不是协议消息**——无 `protocol.ts` 面、无四处同步。
  - `command-bridge.ts`:`profile_open` 已映射,`params` 原样透传 `direct`,无新增映射。
  - `docs/protocol.md`:hello payload 去 `nickname`、profile.open payload 加 `direct`;头部计数仍 56。
- **edge(aidcp-edge)**:`src/comm/protocol.ts`(删 hello.nickname / 加 profile.open.direct)、`src/client/edge-client.ts`(revert 昵称透传)、`src/main.ts`(revert 诚实闸)、`src/cdp/self-identity.ts`(in-place displayName/redId→null,撤日志装饰)+ 其测试、`src/browse/browse-session.ts`(direct 直navi 分支 + 昵称读解耦数字门)、`scripts/dev-run.sh`(删过时注释)。
- **cloud(aidcp-cloud)**:`src/comm/protocol.ts`(同 edge);`src/comm/handler.ts` + `src/server.ts`(revert hello 摄取/接线);`src/event-bus/types.ts`(RoleName + RoleEventMap 加 self.profile.capture);新 `src/agents/nickname-enricher.ts`;`src/orchestrator/role-dispatcher.ts`(注册角色 + session_start 钩子 + self.profile.capture 翻译 + chokepoint 限定放行 + profile.done 关注自跳过)、`SessionContext`(pendingNicknameCapture / selfCaptureInFlight / 尝试计数 / 超时);`src/agents/profile-browser.ts`(本人早退);`src/account-store.ts`(加 `getNickname`);`server.ts`(注入 get/setNickname 进 dispatcher、握手算 pending)。
- **console**:零改(复用 helper)。
- **红线/保留**:edge 纯执行;自己绝不进社交管线(无自关注/自互动流);单写 + 诚实空不覆盖;风控/预算/节奏中性;有界回 feed(~20s 超时 + K=3 尝试上限)、绝不困死会话。
- **并发**:cloud 满并发(且 session-auto-resume / prompt-preview 近期已部署进 master)——精确 git add、提交后核 commit diff 只含自己改动、部署用干净 origin/master worktree。
