## Why

**记账函数在写下「这件事发生了」之前，先问一次「这个号现在还允许做这件事吗」——不允许就什么都不写。而这时候事情已经做完了。**

`RiskController.record(action)`（`risk-controller.ts:179-191`）：

```
async record(action: RiskAction): Promise<boolean> {
  // 撞自己的速率配额是「节奏背压」，不是风控信号：被拒只返 false（canDo 已拦住动作），…
  if (!this.canDo(action)) {
    return false;                      // ← 静默丢弃：不写计数、不落库
  }
  this.counter.record(action, now);
  await this.store?.appendCounter(this.accountId, action, now);
  return true;
}
```

它被 `interaction.occurred` 的订阅者调用（`server.ts:1391`），而那条事件**在边缘回执「我已经在真实页面上做完了」之后才发**。所以这道闸只可能在**动作已成既成事实**时开火，而它的动作是**抹掉证据**。

### 这道闸是一场停在最后一行的拆迁留下的遗蜕

`git blame` 的结论是决定性的，而且与直觉相反：

| | |
| --- | --- |
| **出生（`1c51477`，建文件那一版）** | `if (!canDo) return false` **就是 `applySignal({kind:'quota_exceeded'})` 的触发点**——它存在的唯一目的**就是那个自残**。 |
| **change `decouple-quota-hit-from-risk`（`7355d0f`）** | 专门来杀这个自残：删掉了 `applySignal`，**把这句光秃秃的 `return false` 留在原地**。 |
| **今天** | 它是那个反模式的**空壳**——原本的功能被摘掉了，附带的「所以就当没发生过」被留下了。 |

**16 天里没有任何一行设计说过「计数器不许写」。** 全仓（commit message / `src/risk/` 注释 / `docs/` / `CLAUDE.md` / 全部 `openspec/specs/` 与 `changes/`）搜遍，唯一近似理由的是它自己那句注释：**「canDo 已拦住动作」**——这是对调用方的**假设**，不是对这道闸的设计意图。**而这个假设在写下时就已经是假的**：手动 `/comment` 绕配额闸（change `comment-search-command`）**比 `7355d0f` 还早**。

### 它不是「统计偏保守」，是**预算真的会被打穿**

加群的小时配额在**保守档与正常档都 = 1**（`max(1, min(HOUR_BURST_CAP=2, ceil(daily/4)))`）。**小时窗会污染日账本**：

| 运营一小时内手动加 3 个群（全部真点、全部真进） | 记账时问「现在允许吗」 | 日计数 |
| --- | --- | --- |
| 第 1 个 | 这小时还没加过 → 允许 | 1 |
| 第 2 个 | 这小时已有 1 个 → **拒** | **仍 1**（连日窗都没写进去） |
| 第 3 个 | 还是 1 个 → **拒** | **仍 1** |

日闸（正常档 = 3）于是认为「今天才加了 1 个、还有 2 格」⇒ **自动加群再打 2 次 ⇒ 当天真实 5 次 / 预算 3。** 严重度不是「指标偏悲观」，是**紧的那个窗把松的那个窗的账本毒了**。

### 这是「绝不静默假成功」的镜像

本仓的核心红线是**绝不静默假成功**。这道闸干的是它的**镜像**：**静默假失败**——系统对自己**少报**了它真实做过的事。方向相反，species 相同。

上一个 change（`fb-join-quota-counts-attempts`，已归档）在**上一层**修的正是这个病：「平台还没批 → 就当没做过」。它的 design 把本 change 预登记为「**最重要，是 D3 的前置**」，并诊断为与它**同构、只是低一层**。两层现在在同一条代码路径里**公开互相打脸**：

- 上层（`handler.ts:558`）：`clicked=true` 是边缘事后回执、**既成事实**，平台批没批 **MUST NOT** 决定它算不算数。
- 下层（`risk-controller.ts:184`）：**策略说你现在不该做 → 那就当你没做过。**

## What Changes

- **记账只记既成事实**：`record(action)` **无条件写入**计数与持久化。**「该不该做」是动手之前那道闸的事**——每一条自动下发路径都已经在 `canDo` / `explain` 上预闸过（角色调度 `server.ts:2661`、发布排期 `publish-scheduler:297/351/398`、`gated-auto-comment`、`send-orchestrator:116/178`、加群 `canJoin:3264`）。这道事后重判**买不到任何预闸没给的保护**，它只在预闸**失效的那个缝里**开火——而那正是真相最要紧的时候。
- **返回值语义逐字不变**：`record` 在被 `canDo` 拒时**仍返回 `false`**。**红线保住**（见下）。改的只是它的**副作用**，不是它的**答案**。
- **修同一个病的第二处**（`interaction-inbox-service.ts:94-108`）：微信入站回复在 `status === 'confirmed'`（**平台已确认发出**）时调 `record`，被拒则**释放幂等占位 + 记 `denied` 指标** ⇒ 那条已发出的回复对风控**永远隐形**。写入无条件化后，**占位只在真抛错时才释放**（否则重放会重复计数）。
- **不动**：`canDo` / `explain` / 状态机 / 配额档 / `quota_config` / 协议 / 边缘 / console。

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `interaction-risk-gating`: 三处 **MODIFIED**——
  ① 「速率配额饱和是节奏背压、不是风控状态输入」：`MUST 只返回 false` 这句会被敌意解读成「且什么都别干」（即禁止写入）。**本 change 必须显式改写它、绝不靠解释含混过关**，否则就是拿本仓自己的红线文本去赌一个歧义。改法照该要求**自己立的先例**（`spec:127`：「此要求**强化**既有红线：返 false 不变，只去掉『撞自己配额还自升状态』的自残副作用」）——同一招再进一格：**返 false 不变，只去掉「所以就当没发生过」这个丢证据的副作用。**
  ② 「互动发生后必须按账号持久计数」：补「既成事实回执 MUST NOT 被策略二次否决而丢弃」，与既有的 `MUST NOT 凭下发即记` 构成一对（**下发不算，做完了必须算**）。
  ③ 「Facebook group join is a first-class rate-limited action」：其中「任何计数都只是下界，因为记账路径会二次判策略并静默丢弃既成事实回执」这段**是在把本 change 的靶子写成 spec 事实**，前提溶解后必须改；配套 scenario「A gate is never relaxed onto a looser bound」的 setup 亦然。**注意那条禁令是有条件的**（`MUST NOT be done **while** that counter can silently drop a real click`）——本 change **解除前置条件**，而不是与它冲突。

## Impact

- **aidcp-cloud（唯一动代码的仓）**：`src/risk/risk-controller.ts`（把写入移出 `canDo` 分支）、`src/interactions/interaction-inbox-service.ts`（占位只在抛错时释放）、`src/server.ts:1394` 一带（告警改读 `explain()`，见 design D3）。
- **协议 / DB / 边缘 / console**：**全部零改动**、无迁移。
- **部署**：纯云端单边，dev 当天可部署，无需出安装包。
- **回滚**：还原上一版本 tar。改动期间多记的计数会残留，**滑动窗一天内自然收敛**，无需数据修复。

### 红线：不是「求例外」，是「红线从来没瞄准这里」——**这是跑出来的，不是论证出来的**

把四条 `AC-RISK-*` 断言**原样**跑在新语义下（无条件写入 + 仍返 `false`）：**4/4 全过，零改测试**。**全量套件同跑：2432 pass / 0 fail，零改测试** ⇒ **桩层爆炸半径 = 零**（一次性副本实跑，未碰任何 canonical checkout）。

> **但这把刀是双刃的，且警告那一面更重要**：桩层零爆炸半径 = **整个测试套件根本看不见这个改动**——2440 条里没有一条能区分「写了」和「没写」。所以「全绿」在本 change 上**不构成任何证据**，新测试是唯一的机械保障、真机是唯一的真实验证。（上一个 change 的「统一分子」正是全绿着走到提交前才被对抗性复核打穿的。）

- 它们全都在管两件事：`record()` 的**返回值**，或**威胁状态机**（`status` / `signal_count` / `last_signal_at`）。**没有一条读计数器。**
- 而且它们**结构上看不见**这个写入：`RiskState`（`types.ts:59-67`）**没有计数器字段**，计数器活在互不相交的 `this.counter` / `this.store` 里。所以这不是「测试碰巧过了」，是「测试根本看不到」。
- **`绝不自残` 在 spec 里是有定义的，而定义排除了计数器**：`spec:127` 明写自残的副作用是「**撞自己配额还自升状态**」；`spec:123` 的 MUST NOT 清单五条——`applySignal` / `signal_count` / `last_signal_at` / `normal→warned→restricted` / `quota_exceeded` 进 `RiskSignalKind`——**全是状态机，零条计数器**。
- **方向性是决定性的**：计数器只增（`sliding-window-counter.ts:26` 只 push），每道闸都是 `count >= quota → deny`。**诚实记账只可能让闸更早拒绝，不存在任何路径让它放行今天会挡住的动作。** 自残的定义是「凭空的信号把自己越限越死」；记下一次真实点击**造不出幻象，它是在消掉一个幻象**——一个「我还有额度」的幻象。

### 没有任何人拿 `record()` 当权限判据（5 个调用点已逐个坐实）

| 调用点 | 用返回值吗 |
| --- | --- |
| `server.ts:1391` 互动订阅者 | 用——但只喂 P2 节奏告警，且**当场又调 `explain()` 重算真信号** |
| `server.ts:2726` 热帖联系评论 | **丢弃**（裸 `await`） |
| `server.ts:2735` → `gated-auto-comment:87` | **丢弃**（`.catch(() => false)` 造一个 false 出来然后无视它） |
| `interaction-inbox-service.ts:97` | 用——**但那是这次要修的 bug**（已确认发出还释放占位） |
| `handler.ts:869` `risk.record` 协议 | 用——**但是死路**：边缘从不发这两条消息，spec 明列为保留通道 |

**最强的反证**：`send-orchestrator.ts:25` 自己的接口上**声明了** `record`，却**从不调用**——它的两道闸（`:116` / `:178`）都用 `explain()`。**唯一握着 record 句柄的模块，回答「能不能做」时选的是 `explain()`。**

### 同类洞（本 change **不修**，只登记）

- **`publish` 从不进 `record()`**——全仓零调用点（`record('publish')` grep 无命中，而 `record()` 是 `risk_counters` 的**唯一写入者**）⇒ **发布计数器恒为 0，发布日配额是装饰品**（`canDo('publish')` 的配额分支永不开火，发布只受状态闸约束）。**这比本 change 的病更大**：不是回执被丢，是**根本没有回执**。**佐证**：后台早就绕开它了——`panel/types.ts:381` 注释自陈 publish 键用 `publish_log` 真实数**覆盖** `risk_counters` 同名键。有人撞见「面板发布数是 0」，从另一张表把**显示**修好了，把计数器留在死地。
- **`view` 在手动 `/comment` 路径上无预闸**：`comment-scheduler` 的读帖不过 `explainView`，而 `skipRiskRecord` 只覆盖 `comment` ⇒ 手动跑一轮多开几篇，view 回执被自己丢掉。**这一处的丢弃是在放松闸**（见 design 的方向性讨论）。

### Non-Goals

- **不改** `canDo` / `explain` / 状态机 / 配额数值 / 三档 / `quota_config`。
- **不改** `record()` 的**返回值语义**（拒时仍返 `false`）。
- **不做** join 配额的「统一分子」。上一个 change 已在**独立**理由上把它证伪并反转（两个分子是同量的两个独立下界、两闸 AND = 取较紧）。本 change 只是**解除**了那条禁令的前置条件，使其**变为可做**——**不等于该做**。要做另提。
- **不修** `publish` 无回执、`view` 手动路径无预闸（见上，只登记）。
