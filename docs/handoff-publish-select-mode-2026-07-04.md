# 交接：发布 `select_mode` 选「上传图文」偶发 `no_target`（疑宽/窄双布局）

> 建立 2026-07-04。状态：**已定位、未修**，留给另一个 session 起 change 修。
> 关联仓：`../aidcp-edge`（代码）；关联活跃 change：`publish-trigger-and-apply`（29/37，**同文件热点**，见文末协调）。

## TL;DR

`/publish` 审批通过后，发布**确实接管并打开了创作发布页**（`navigate_entry` 成功），但下一步「点『上传图文』tab」（`select_mode`）偶发 `no_target`，发布 fail-fast 中止 → 浏览恢复把标签页导回 feed → 表现为「审批通过后直接结束 / 发布页打开就闪退」。**根因高度疑似小红书创作发布页的宽/窄双布局**：真机实测该页 tab **重复渲染两套**，而 `select_mode` 现在「取第一个文本匹配的元素就点」、不挑**可见**的那个，也不等 tab 真渲染。修复方向 = 复用消费端早已定型的「取可见的那个 + 有界等待渲染」双布局套路。

## 现象与证据（三方对齐，勿重复排查）

**云端日志（ECS `aidcp-cloud.service`，2026-07-03 23:44–23:45）**：
```
23:44:09 [PublishExecutor] 审批卡已发 requestId=publish-37 → 草稿待审 recordId=37
23:44:09 [PublishOrchestrator] pipeline completed status=pending_approval
~23:45:07 [RoleDispatcher] 会话结束: publish_takeover          # 审批通过、发布接管浏览器
23:45:24 [PublishDispatcher] recordId=37 下发失败 failedAt={"seq":1,"kind":"select_mode","error":"no_target"}
```
- `seq=0 navigate_entry` **成功**（序列推进到了 seq=1），说明**发布页确实打开了**、`isPublishPage` 后置校验过了。
- `seq=1 select_mode` 报 **`no_target`**（在其 12s 轮询窗口内没找到/点到「上传图文」）。
- 发布链路 fail-fast（防残帖），到此整条中止。

**边缘日志**：发布指令流**静默无日志**（`PublishCommandDispatcher` 正常步骤不 console.log，只有 `[publish-submit-diag]` 警告），故 `edge.log` 那段只是一个 15s 空档（`15:45:09 → 15:45:24 resume_redrive`）——**不是没发生，是没打日志**。别被「edge.log 没有发布行」误导。

**真机 DOM 实测（2026-07-04，登录态 `工程师大白` 创作发布页，只读）**：
- 页面正常打开、账号登录着（截图 `/tmp/aidcp-publish-tab.png` 当时留存，见下方复现命令可再生成）。
- **默认停在「上传视频」tab**（active）；文件输入 `accept=.mp4,.mov,...`（视频）；要发图文**必须先点「上传图文」**切模式。
- **tab 重复渲染两套**（关键）：`div.header-tabs` 文本 = `上传视频\n上传视频\n上传图文\n上传图文`，`div.creator-tab` 里「上传视频」×2（其一 active）、「上传图文」×3、「写长文」×2、「发播客」×2。→ **典型宽/窄双布局：两套同 tab 同时在 DOM，一套可见一套隐藏**（同 `docs/xhs-layout-states.md` 记的消费端双布局机理）。

## 定位：代码在哪、为什么脆

`aidcp-edge/src/flows/publish-command-handlers.ts` → `runSelectMode()`（约 358–423）：

- **点 tab 用「取第一个文本匹配」**（约 369–378，`CLICK_TAB`）：
  ```js
  const tab = els.find(e => e.innerText.trim()==='上传图文' && String(e.className||'').includes('creator-tab'))
           || els.find(e => e.innerText.trim()==='上传图文' && String(e.className||'').includes('tab'))
           || els.find(e => e.innerText.trim()==='上传图文');
  if (!tab) return { clicked:false };   // ← clicked=false → 上层 no_target
  tab.click();
  ```
  `els.find` 取**第一个**，**不判可见性**。双布局下第一个可能是**隐藏副本**。
- 轮询点击窗口 **12s**（约 387–401，`clickDeadline = clock()+12_000`）；12s 内没点中 → `no_target`（402–403）。
- 点中后再轮询 **10s** 确认进入图文模式（`IMG_MODE_ACTIVE`，405–421）；没进 → `post_validate_failed`（418–419）。

**两种失败签名，对应两条根因**（本次踩的是前者）：
1. **`no_target`（本次观测到）**：`els.find` 全程返回空 = 那 12s 内 DOM 里没有「文本恰为『上传图文』」的元素被匹配。可能：①**窄布局**下该 tab 渲染成图标/文案不同/结构不同 → 文本选择器不命中；②创作页冷加载慢、tab 渲染晚于 12s 窗口（时序）。两者都会表现为 `no_target`。
2. **`post_validate_failed`（潜在、这次没踩）**：`find` 命中了**隐藏副本**、`click()` 无效 → 图文模式没切上 → 10s 后 `post_validate_failed`。这是「取第一个不挑可见」的直接隐患，修 no_target 后若只放宽等待、不挑可见，就会转成这个。

## 用户判断（记录）

> "select_mode，我理解是宽模式和窄模式的问题"

**与证据一致**：重复两套 tab = 宽/窄双布局；`select_mode` 的「取第一个不挑可见 + 只认精确文本」正是双布局脆点。宽/窄很可能是主因（时序为次要/叠加因素）。

## 修复方向（给修复 session）

对齐 `docs/xhs-layout-states.md` 既定的双布局套路——**「取可见的那个 + 有界等待渲染」**（消费端 self-identity/notification/scroll 都这么修的）：

1. **点「可见」的那个 tab**，不取第一个：候选里过滤 `offsetParent!==null && rect.w>0 && rect.h>0`，再点。躲开隐藏副本（既治潜在 `post_validate_failed`，也治窄布局命中隐藏 wide 副本）。
2. **等 tab 真渲染再判**：`navigate_entry` 的后置校验（`isPublishPage`）过早（页壳/URL 命中即返回，tab 还没 hydrate）。要么让 `navigate_entry` 等到 tab 出现，要么把 `select_mode` 的点击轮询放宽（现 12s → 视真机冷加载放宽，或改成「出现即点」的有界重试）。
3. **窄布局 tab 形态待真机标定**：若窄布局把「上传图文」收成图标/换文案，需补候选（图标语义/`aria`/其它稳定语义片段），别死绑精确中文文案。**建议给 `docs/xhs-layout-states.md` 补一节「创作发布页（creator.xiaohongshu.com）双布局」**——该文档目前只覆盖消费端，创作子域是新面。
4. （可选）**若默认视频模式可跳过**：确认发布页是否有「直接进图文」的入口（URL 参数 / 记忆上次模式），能省掉 select_mode 这步最稳。需真机验。

**红线**：任何放宽都不得破坏 fail-fast「找不到诚实报 no_target、绝不假成功往下走」；`post_validate_failed`（点了但没切上模式）也必须如实报、不得当成功。

## 真机复现 / 验证（修复 session 用）

前置：AdsPower 该账号浏览器已登录。起浏览器拿调试端口：
```
curl -s "http://local.adspower.net:50325/api/v1/browser/start?user_id=k1e0ero8&open_tabs=1"   # 取 debug_port
```
只读探 DOM（导航到发布页 + dump tab 结构 + 截图；绝不上传/发布）——参照本次用过的一次性探针写法（`attachToPage({host:'127.0.0.1',port})` → `Page.navigate` 到 `https://creator.xiaohongshu.com/publish/publish?source=official` → 读 `div.creator-tab`/`header-tabs`/`input[type=file]` 的可见性与文案 → 复位 explore → 关浏览器）。**关键要在宽窗口和窄窗口各测一次**（改 AdsPower 窗口宽度或 `Emulation.setDeviceMetricsOverride`），看「上传图文」在两态各自的可见元素/文案/class，据此定选择器。

修完接 backlog **簇 3**（发布链路真机）一并端到端验：`/publish` → 审批 → `navigate_entry`→`select_mode`→…→ 发布落地。

## 协调（重要）

- `publish-command-handlers.ts` 是**活跃 change `publish-trigger-and-apply`（29/37）的热点文件**。修复 session **先 `git fetch` + rebase 到最新 edge master**，`runSelectMode` 段落若被并发方动过要手工并轨；单写者纪律，别与那条线并行乱改同段。
- 本 handoff 不含身份修复内容——身份误判停摆是**另一件事**、已修已归档（`identity-recheck-page-context-guard`，edge master `0765e00`），与 `select_mode` 无关，勿混。

## 指针

- 代码：`aidcp-edge/src/flows/publish-command-handlers.ts:358`（`runSelectMode`）、`:200`（`XHS_CREATOR_PUBLISH_URL`）、`:313`（`runNavigateEntry`）。
- 序列：`aidcp-cloud/src/publish-agent/command-sequencer.ts:116`（`add('navigate_entry')`→`select_mode`…，fail-fast）。
- 双布局权威文档：`docs/xhs-layout-states.md`（消费端；创作页那节待补）。
- 关联记忆：`note.open miss livelock`、`/comment open modal_timeout on AI search`（同属边缘定位/布局脆点族）。
