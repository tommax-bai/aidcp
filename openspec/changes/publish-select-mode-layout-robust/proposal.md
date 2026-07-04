## Why

`/publish` 审批通过后进入下发段，序列第一步 `navigate_entry`（打开创作发布页）成功，第二步 `select_mode`（点「上传图文」切图文模式）偶发 `no_target`，发布 fail-fast 中止 → 浏览恢复把标签页导回 feed → 表现为「审批通过后直接结束 / 发布页打开就闪退」（云端 ECS `aidcp-cloud.service` 2026-07-03 23:45，`recordId=37 failedAt seq=1 kind=select_mode error=no_target`）。

根因：小红书**创作发布页是宽/窄双布局**——真机实测（2026-07-04 登录态只读）该页 tab **重复渲染两套**（`上传视频`×2、`上传图文`×3 等，一套可见一套隐藏），与消费端首页/搜索页同机理（`docs/xhs-layout-states.md`）。而 `select_mode` 现在「取第一个文本匹配就点」、**不挑可见的那个**、也不等 tab 真渲染、只等 12s。双布局下第一个可能是隐藏副本；窄布局 / 冷加载慢时又可能 12s 内文本选择器全不命中 → `no_target`。

这与已定型的消费端双布局套路（`self-identity` / `notification` / `search` 都是「取可见的那个 + 有界等待渲染」）背离。本 change 把该套路补到创作发布页的模式选择步。

## What Changes

- **【边端·稳健定位】** 重写 `select_mode`：候选里**只点可见的**那个「上传图文」tab（复用消费端可见性判据 `offsetParent!==null || getClientRects().length>0`，兼容窄布局 `position:fixed`），躲开隐藏副本。
- **【边端·幂等早退】** 点击前先以**保守的「当前激活 tab 是图文」信号**判是否已在图文模式，已在则直接成功（治「本已在图文模式却报 no_target」）；该早退信号 MUST 保守——绝不在仍是视频模式时谎报图文（不静默假成功）。
- **【边端·有界重试】** 把「找+点+确认」并进一个有界重试环（放宽到约 20s，仍**严格低于云端单指令 30s 超时**），点后留一小段 grace 再重点，容忍冷加载晚渲染。
- **【边端·窄布局兜底】** 补窄布局候选（文本含「图文」而非「视频/长文/播客」、tab 形态），窄布局真机形态**待标定**、先 best-effort 不死绑精确中文文案。
- **【诚实红线不破】** 始终没有可见 tab 且未在图文模式 → 诚实 `no_target`；点了但模式没切上 → 诚实 `post_validate_failed`；绝不假成功往下走。
- **【文档】** 给 `aidcp-edge/docs/xhs-layout-states.md` 补一节「创作发布页（creator.xiaohongshu.com）双布局」——该文档此前只覆盖消费端。

> 非 BREAKING：纯 `aidcp-edge` 侧、单函数 `runSelectMode` 的稳健性修复；协议 / 云端 / 序列均不改。窄布局精确形态与端到端真机验证（发布链路簇 3）留作真机标定项。

## Capabilities

### Modified Capabilities
- `publish-pipeline`: 新增一条「发布模式选择须跨双布局稳健且失败诚实」需求（ADDED），把消费端已定型的「取可见 + 有界等待渲染 + 幂等 + 诚实失败」套路补到下发段 `select_mode` 步。既有发布需求不变。

## Impact

- **aidcp-edge**（全部工作量）
  - `src/flows/publish-command-handlers.ts` `runSelectMode()`：可见性过滤 + 幂等早退 + 统一有界重试 + 窄布局候选 + 诚实失败分类。
  - `test/flows/publish-command-handlers.test.ts`：新增 `select_mode` 双布局单测（取可见 / 幂等 / 冷加载 / no_target / post_validate_failed / 不假成功）。
  - `docs/xhs-layout-states.md`：补「创作发布页双布局」一节。
- **协调**：`publish-command-handlers.ts` 是活跃 change `publish-trigger-and-apply` 的热点文件——其剩余 task（配图下沉 `publish-media-upload` + 部署）不触及 `runSelectMode`，本 change 与之无重叠段落；仍守单写者纪律、集成前 rebase 到最新 edge master。
- **真机遗留**：窄布局 tab 精确形态标定 + 发布链路端到端真机验（AdsPower 该账号浏览器，本会话未在跑）。
