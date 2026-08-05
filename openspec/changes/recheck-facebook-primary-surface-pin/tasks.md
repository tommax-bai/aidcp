## 1. aidcp-cloud — 钉定值带上来源

- [ ] 1.1 开工前先读代码复核缺陷仍在：确认 `src/orchestrator/role-dispatcher.ts` 的会话浏览面钉定仍是「缺面值即 `?? 'feed'`」且不记原因，并确认两份账号运营裁决实现（`src/server.ts` 与派生自动化组装处）的每一条早退都已带具名 blocker；任何一条没带的，在本任务里就地补名并记进本文件。
- [ ] 1.2 把会话级浏览面字段从二值枚举换成「面值 + 解析来源（authoritative/unresolved）+ 具名原因」的私有结构，并加一个取用方法回答「本场是不是 Reels 主入口」。
- [ ] 1.3 repoint 全部读取点到该取用方法（统一重驱、主入口推进、首页降级授权、任何按面值分支的判断），`npm run typecheck` 必须零残留旧字段引用。
- [ ] 1.4 钉定处改为：裁决对象带 `primarySurface` ⇒ authoritative（**含 `mode:'blocked'` 但带面值的情形**）；缺 `primarySurface` ⇒ unresolved + 面值取 `feed` + 原因取同一对象上的 blocker；blocker 也为空 ⇒ 记显式未识别值，MUST NOT 折进任何已有名字。

## 2. aidcp-cloud — 具名回执

- [ ] 2.1 unresolved 钉定时输出一条具名回执（账号 + 已知环境 + blocker 原值），authoritative 钉定不输出。
- [ ] 2.2 按「每场每个不同 blocker 至多一条」去重；blocker 值发生迁移时允许再出一条；到顶的终态回执不受去重影响、必出。
- [ ] 2.3 确认回执落点符合本仓既有做法（具名日志行优先）；是否升格告警按该 blocker 是否代表「整批新账号都会中」判断，判断结论写进本文件。

## 3. aidcp-cloud — 有界复判通道

- [ ] 3.1 新增独立于启动闸复判的复判状态（自己的定时器、退避步进、跳数计数），退避表照抄 `[2s, 5s, 10s, 30s, 60s]`；定时器 unref。
- [ ] 3.2 仅在钉定为 unresolved 时武装，且必须在会话置为活跃**之后**武装；authoritative 钉定绝不武装。
- [ ] 3.3 每跳：先判会话仍活跃（否则解除），再重问裁决口；仍 unresolved ⇒ 静默排下一跳（不打日志、不发命令）；到顶 ⇒ 记一条终态回执、解除通道、会话继续在 Feed 上跑。
- [ ] 3.4 问到基线 ⇒ 就地改钉为 authoritative + 权威面值，解除通道；纠正面与当前浏览面相同则不发任何命令，不同则经既有统一重驱出口发一条 `resume_redrive{targetSurface:<权威面>}`。
- [ ] 3.5 重驱被既有闸（风控/配额/软暂停）抑制时：MUST NOT 回滚已改的钉定、MUST NOT 消耗复判预算；靠后续自然重驱收敛。
- [ ] 3.6 会话结束（正常收尾 / 断连拆除 / 重启新场）一律解除通道并清零步进，确保没有跳打在已结束的会话上。

## 4. aidcp-cloud — 验证

- [ ] 4.1 补验收用例（少而承重，逐条对应 design §D6）：①缺面值+带 blocker ⇒ 钉 unresolved、回执具名、通道武装；②带面值但 `mode:'blocked'` ⇒ authoritative、不武装、无回执；③复判转好为 reels ⇒ 改钉 + 恰好一条重驱 + 解除；④复判转好为 feed ⇒ 改钉 + 零重驱；⑤到顶 ⇒ 一条终态回执 + 无后续跳；⑥缺面值且 blocker 为空 ⇒ 显式未识别值。
- [ ] 4.2 保住既有反向断言：会话中途改配置不影响 authoritative 会话的钉定（既有场景用例逐字保留、必须仍绿）。
- [ ] 4.3 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全过；`AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 红线全绿。

## 5. 派生仓同步与部署

- [ ] 5.1 `scripts/sync-split-repos --repo aidcp-automation` 先无参 dry-run 对账，确认改动面只含本次文件，再 `--apply`；组装根 `src/server.ts` / `src/index.ts` 不自动同步，若确需改动手写并在本文件说明。
- [ ] 5.2 派生仓 `aidcp-automation` 跑 `npm run typecheck` 与测试，确认无组装根缺参导致的能力静默消失。
- [ ] 5.3 按安全序列部署 dev：`scripts/deploy-target dev --check` → 备份 → rsync → 重启 → healthcheck（服务 active、8787 监听、PG 可达）；绝不碰同机 isales。

## 6. 收口

- [ ] 6.1 真机验收项登记 `docs/real-machine-acceptance-backlog.md`：新建 FB 账号首次真实握手的那一场即进 Reels（对照今日 11/11 停在 Feed 的实测）；以及首次故障复现时回执能当场说出具名原因。
- [ ] 6.2 回写本文件各 task 的 `<!-- <repo> <commit-sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`；sha 必须取自已推送的提交。
- [ ] 6.3 `openspec validate recheck-facebook-primary-surface-pin --strict` 通过后归档。
