## Context

Cloud 当前通过 Facebook 平台注册表声明 `feedScrollDwellFloorMs=7_000`，所有经统一 scroll 出口下发的 Facebook `page.scroll` 都会取「卡片计算中心」与「平台地板乘当前 tempo」的较大值。Feed 与 Reels 因而已经共享中心值；搜索和恢复类滚动也沿用这个既有平台出口。

Edge 当前对所有平台的 `page.scroll.dwellMs` 使用 `sigma=0.20` 的无界乘性 lognormal 抖动，然后扣除从最近一批内容到达至今的已用时间，只等待正差额。该等待发生在 Native 页面执行器及其 180 秒命令超时启动之前，并且可由会话接管/停止信号取消。

## Goals / Non-Goals

**Goals:**

- 让 Facebook Feed 与 Reels 的正常翻页中心统一为 11 秒，并保留现有风险 `tempo` 放大与卡片计算上限语义。
- 扩大 Facebook 翻页随机性，同时用反射边界避免硬裁剪尖峰和异常长等待。
- 保持已用时间抵扣、内联阅读 floor 取最大值、取消语义和诊断可验证性。
- 证明既有页面、命令、空闲和会话超时无需联动调整。

**Non-Goals:**

- 不新增 Feed/Reels 判别字段、协议版本或第二套 pacing authority。
- 不改变非 Facebook 平台、详情页 dwell、think、动作间隔或滚动手势物理参数。
- 不改变 Reel 身份水合、输入预留、Native 命令执行、空闲唤醒、会话结束或 quiesce 超时。
- 不在本变更中打包或安装 Edge 客户端，不部署 OL，也不执行真实 Facebook 账号动作。

## Decisions

### 1. 在既有 Facebook 平台地板上把正常中心从 7 秒改为 11 秒

Cloud 将 `feedScrollDwellFloorMs` 改为 `11_000`。统一 scroll 出口继续计算：

`max(cardFloor, 11_000 × effectiveTempo)`

因此 normal / warned / restricted 仍单调放慢，且更高的既有卡片中心仍可胜出。选择平台地板而不是为 Feed/Reels 分别加常量，是因为两条路径已经共享该出口，拆分会引入新的列表状态与校准面。

这一选择也保留既有作用域：Facebook 搜索与恢复类 `page.scroll` 同样通过平台出口取得该地板。若以后需要为搜索建立不同节奏，应由独立观测证据驱动新变更，而不是在本次调整中推断列表类型。

### 2. 仅在 Edge 的 Facebook `page.scroll` 使用中心保持的有界反射采样

新增独立 helper，先生成：

`raw = centerMs × exp(0.30 × N(0,1))`

再把样本以三角波反射进：

`[0.55 × centerMs, min(1.90 × centerMs, 60_000)]`

反射而非硬裁剪可避免样本堆在边界形成固定尖峰；原始分布的中位中心仍为 `centerMs`。helper 不修改共享 `jitterAround`，非 Facebook、详情页和动作等待继续保持原参数。

以 normal 中心 11 秒计算，理论 5/50/95 分位约为 6.7/11.0/18.0 秒，实际安全区间为 6.05..20.9 秒。warned/restricted 先由 Cloud 放大中心，再使用同一相对边界；绝对上限兜住异常中心值。

### 3. 等待仍只补目标与已用时间的正差额

Edge 继续以最近内容批次到达为锚点，计算：

`waitMs = max(0, sampledTargetMs - elapsedMs)`

如存在内联阅读 floor，则与该 floor 的剩余差额取最大值而不相加。Cloud 决策耗时、页面观察耗时已经覆盖目标时不再额外等待。诊断记录中心值、采样目标、已用时间、最终等待和采样策略，便于区分“已消费但被耗时抵扣”与“字段丢失”。

### 4. 不联动调整既有超时

最大 60 秒的 Edge pacing 等待在 Native 页面执行器启动前发生，且保持可取消；随后 `page_scroll` 仍拥有独立 180 秒执行预算。因此无需扩大 Facebook Reel 15 秒身份水合窗口、18 秒输入预留或 180 秒页面命令超时。

60 秒上限也低于既有空闲恢复最小 200 秒（默认 240 秒）和 3600 秒会话结束窗口；等待期间的接管/停止仍通过 abort 立即打断，故无需扩大 5 秒 quiesce 预算。

## Risks / Trade-offs

- **[共享平台地板也放慢 Facebook 搜索/恢复滚动]** → 明确这是既有统一出口的作用域；本次不引入缺乏观测依据的列表类型状态，并用诊断为后续分拆提供证据。
- **[更长尾部降低浏览吞吐]** → 以 11 秒中位、1.90x 相对上界和 60 秒绝对上界控制；风险档位继续由 Cloud 单一 authority 放大。
- **[Cloud 与已安装 Edge 的交付可见性不同]** → Cloud 可独立在 DEV 生效 11 秒中心；更宽抖动只有新 Edge 源码被显式打包安装后生效，交付记录必须分开声明。
- **[边界实现产生固定墙尖峰]** → 使用反射采样并对中心、区间、绝对上限和非 Facebook 回归做确定性测试。

## Migration Plan

1. 合入 Cloud 的 11 秒 Facebook 平台地板并在 DEV 部署、验证运行版本与健康状态。
2. 合入 Edge 的 Facebook 专属有界抖动与诊断；本次停在源码交付，不打包、不安装。
3. 后续获得明确打包授权时，生成并安装 Edge 构建，再用真实运行诊断验证分布；不以源码或包产物代替已安装客户端证据。
4. 回滚时 Cloud 把平台地板恢复为 7 秒；Edge 恢复 Facebook `page.scroll` 使用既有 `jitterAround(..., 0.20)`。两仓可独立回滚，不涉及协议或数据迁移。

## Open Questions

无。
