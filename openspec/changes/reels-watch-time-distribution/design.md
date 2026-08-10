# Design: reels-watch-time-distribution

## Context

每条 Reel 的观看时长由「翻到下一条」命令附带的 `dwellMs` 决定,链路是:

- 云端 `role-dispatcher.ts` 的 `sendScrollCommand` → `scrollDwellParams(floorMs)` → `Math.max(floorMs, feedScrollDwellMs())`;`feedScrollDwellMs()` 不区分 feed / reels 面,对 Facebook 恒取 `max(feed_card_read 地板 × 8 张, 11_000 × tempo)`,正常账号 = 11s 常数(`platform/registry.ts:286`)。
- 边缘 `facebook-session.ts` 的 `ensureFeedDwell`:`jitterAround(dwellMs × tempo, σ=0.2)`,锚定 `lastCardsAt`(吸收云端评估耗时),重复下发不叠加。
- 结果:实际每条 Reel 停留 ≈ 11s × lognormal(0.2),95% 落在 7.5–16.5s。

预算约束(全部已核实,90s 可行):

- idle 看门狗轻推 240s(`resume-limits.ts:25`),`session-monitor-role.ts:34` 注释明写「N 须 > 详情页停留上限(pacing capMs=90s)」——90s 是系统设计时预留过的量级。
- 阅读模型 `READ.capMs = 90_000`(`pacing.ts:23`),`content_read`/`content_glance` 的类别上限同为 90s。
- 停留等待发生在边缘 TS 层、Native 引擎调用之前(`facebook-session.ts:547`),Native 命令超时表不受影响。

## Goals / Non-Goals

**Goals:**

- reels 面每条翻页命令的 `dwellMs` 中心值来自重尾采样,长期分布覆盖 10–90s。
- tempo(风控/配额)与 fatigue(会话进度)照常参与,只放慢不加速。
- 纯云端改动,部署 dev 即生效。

**Non-Goals:**

- 不动边缘抖动层、不新增协议字段 / PacingOp(避开两份 protocol.ts 热点文件与配置面扩表)。
- 不做后台可配(常量内置;将来若要运营可调,再走 PacingOp 扩展 + 协议同步,是独立 change)。
- 不改 feed / search 面的停留计算;不改 view 记账、配额、会话预算。
- 不保证实际停留硬上界 90s(边缘 ±20% 抖动长尾可至 ~110–130s,仍 ≪ 240s 看门狗;10–90s 指中心值)。

## Decisions

1. **三段加权混合 + 段内均匀,而非单一宽 σ lognormal。**
   权重/区间:55% 快划 [10s, 20s)、35% 正常 [20s, 45s)、10% 深看 [45s, 90s]。
   理由:混合分布直接对应「快划 / 看完 / 深看」三种真人行为,参数可读可调;单一 lognormal 要同时满足 median≈20s 与 P90≈50s 需要 σ≈0.7,尾部形状不直观、review 时难核对。边缘再叠 σ=0.2 抖动后,段间边界自然模糊,不会出现可识别的三峰。

2. **采样函数落 `pacing.ts`,随机源注入。**
   新增 `computeReelsWatchMs({ status, quotaLevel, progress, random? })`,常量表 `REELS_WATCH` 与 `FEED_FLOOR` 同层同风格;`random` 缺省 `Math.random`,测试注入确定性序列(边缘 `timing.ts` 的既有惯例)。tempo/fatigue 乘在采样值上,最终 `clamp(v, 10_000, 90_000)`——`restricted` 账号深看段会顶到 90s 上限,可接受(风控差本就该更慢,且 90s 是全局停留上限)。

3. **分流点放 `sendScrollCommand`,按解析后的 surface 分支。**
   先解析 `resolved = surface ?? currentScrollSurface()`,`resolved === 'reels'` 时走 `Math.max(floorMs, computeReelsWatchMs(...))`,否则走既有 `scrollDwellParams`。理由:`sendScrollCommand` 是 reels 翻页唯一出口(规则模式 `continue_after_*`、终态续翻、消费模式全都汇到这里),一处分流全覆盖;`sendBrowseRedrive`(resume_redrive 恢复路径)不带 dwell,保持不变——恢复是纠偏动作,不该背 90s 停留。
   `surface='reels'` 当前只有 Facebook 会解析出来,不需要再叠 platform 判断。

4. **`floorMs` 参数语义保留。**
   reels 路径对传入 `floorMs` 仍取 max(现役调用全是 0,留语义是为 `feed-scroll-card-floor` 类上游算好地板的场景不被静默吞)。

## Risks / Trade-offs

- [吞吐下降] 平均每条 ~12s → ~25–30s,单位时间浏览条数降一半以上;60 动作预算会话拉长 2–3 倍或先撞时长上限 → 用户已知情确认;view 记账、配额逻辑不变,只是节奏变慢。
- [Reels 空转放大] 已知的云端「翻页未确认无上限重发」缺陷(backlog 簇 145.5,用户裁定缓修)在长 dwell 下单次空转周期变长 → 不恶化本质(重发不叠加停留,`ensureFeedDwell` 锚定 lastCardsAt);观察时注意区分。
- [边缘长尾超 90s] 云端 clamp 后边缘抖动可至 ~130s → 仍 ≪ 240s 看门狗轻推;spec 明确 10–90 指中心值。
- [三峰指纹] 混合分布理论上有段间密度落差 → 边缘 σ=0.2 lognormal 抖动 + tempo/fatigue 漂移足以抹平;且平台侧能观测的是「停留时长」单变量,三段混合远不如「恒定 11s」可识别。

## Migration Plan

纯云端行为改动,无迁移、无协议变更、无配置变更。部署 `aidcp-automation` 到 dev 即生效;回滚 = 回滚该服务部署。老边缘零感知兼容(继续消费 `dwellMs` 字段)。
