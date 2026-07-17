# Tasks — cooldown-as-backstop-not-quota

## 1. aidcp-cloud — 冷却值与语义

- [ ] 1.1 `src/risk/action-cooldown.ts`：`COOLDOWN_MS` 四值统一 `15_000`；文件头注释从「压稀节奏、更拟人、延缓配额触顶」**改写为兜底定位 + 不变量 + 15 的推导**（`60 ÷ MINUTE_BURST_CAP.like`）
- [ ] 1.2 `src/server.ts:2547`：`AIDCP_RESTART_QUIET_MS` 默认 `180_000 → 15_000`（两处：读默认 + 非法回落）；注释同步改写（原立论已被 PG 持久化配额抽空）
- [ ] 1.3 单测：现有写死 2/5/10/30 的断言全改；**新增不变量回归**——对四动作断言 `COOLDOWN_MS[a] <= 60_000 / MINUTE_BURST_CAP[a]` 且 `<= 3_600_000 / HOUR_BURST_CAP[a]`。**这条测试就是不变量本身**（typecheck 抓不到，只能靠它）
- [ ] 1.4 `npm run test:acceptance` → `npm test` → `npm run typecheck`
      🔴 红线：`typecheck` 不要接 `| tail`，退出码会变成 tail 的、假绿

## 2. aidcp-cloud — 主闸取值路径夹 cap（不变量 → 算术）

- [ ] 2.1 `src/config/quota-config-store.ts` 的 `windowQuotasFor`：`perMinute` 夹 `MINUTE_BURST_CAP[action]`。**单点夹**（`canDo` 与面板 catalog 读同一函数 ⇒ 显示＝生效，且覆盖已落库老行）
      🔴 **红线：只夹 `perMinute`，MUST NOT 夹 `perHour` / `daily`**——浏览行 `perHour=80` > `HOUR_BURST_CAP.view=60` **正在生效**，夹了当场把浏览量从 80 砍到 60
- [ ] 2.2 单测：`perMinute` 超 cap 被夹且 catalog 回读一致；`perHour=80` / `daily=300` 原样不被夹（防回归）
- [ ] 2.3 **部署前先探 dev 库**：`select tier,action,daily,per_minute,per_hour from quota_config;` 确认四个冷却动作无覆盖行、且无 `per_minute` 超 cap 的行 ⇒ 本 task 零行为变化。**若有超 cap 行，停手报用户**（夹了会当场改变生效配额）

## 3. aidcp（本仓）— spec 与台账

- [ ] 3.1 `interaction-cooldown` spec delta（MODIFIED ×3 + ADDED ×2）——含首次填写 Purpose（自归档日起逐字停留在 `TBD`）
- [ ] 3.2 `comment-interaction` spec delta（`:61` 例外理由句同源化；`:81` Scenario 不动）
- [ ] 3.3 `interaction-appraisal` `:153` / `:156-157`（「跳过点赞冷却」）—— **核对后确认无需改**（无秒数硬编码、无与新语义冲突的理由句），在此显式记一笔，别让下一个人以为漏了
- [ ] 3.4 `openspec validate cooldown-as-backstop-not-quota --strict`
- [ ] 3.5 tasks.md 回写 sha（**sha 必须取自已推送提交**，判据 `git merge-base --is-ancestor`）

## 4. 部署与验收

- [ ] 4.1 部署 dev（安全序列：`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck → 失败即回滚）
- [ ] 4.2 dev 跑一天，三个验收信号（**这是本 change 唯一能证伪自己的东西**）：
  - `journalctl | grep 'skip reason=cooldown'` 对四动作应**趋零**。仍有命中 ⇒ 15s 竟还在 binding ⇒ 配置或算术有出入，回头查（**别当没看见**）
  - 每日实收 点赞/收藏/评论/关注 总量 vs 面板日额：预期「**向上限靠、但不越过**」
  - `pacing_saturation` 告警（撞分钟/小时窗发 P2）频次应**上升**——那是**主闸重新掌权的正信号**，不是故障，**别误当回归**
- [ ] 4.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md`

## 5. 登记 backlog（本 change 不做，但已挖出、必须留痕）

- [ ] 5.1 静默期拒绝时日志打印「还需 0s」，与真冷却在日志里无法区分
- [ ] 5.2 like/collect 失败的原地重试旁路不过主闸、也不过冷却（`role-dispatcher.ts:2637-2652`）
- [ ] 5.3 「收藏了但没点赞」：like 被拦时 collect 仍会发（循环对每个 action 独立判闸、无联动）
- [ ] 5.4 save/like 比例统一 15s 后会向上漂，系统内**无任何闸**在管这个比
- [ ] 5.5 若未来要删 mandatory 冷却例外，**前置条件是冷却改成排队而非丢弃**
- [ ] 5.6 **激进档浏览 `perHour=24` 疑似把 240 打错**（按公式本该 60，且比正常档 80 还慢 3.3 倍）——与本 change 正交，但同属「面板数字没人对过账」，请运营核实
