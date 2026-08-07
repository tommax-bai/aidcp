# 交接 · 命令词汇改造（批 1–5 + 7 已落，批 6 是下一棒）（2026-08-07）

> **给接手 session**：本文只承载会随会话消失的东西。上一份交接
> （`handoff-2026-08-07-vocabulary-batch4-done.md`）的批 5 开工须知已执行完毕并有一处关键修正，**以本文为准**。
> ⚠️ 凡本文写「已核」的只代表 2026-08-07。fleet 高度活跃，接手第一件事自己重核。

## 0. 一句话现状

批 5（互动对象化，change `objectify-interaction-vocabulary`）与批 7（非平台域词汇，change
`normalize-nonplatform-vocabulary`）**同日全链落地并归档**（协议 103 → 107；批 7 计数不变、5 条改名）。
两批并行开发、串行集成（批 5 先落）实证可行。**下一棒 = 批 6（IM 族 + 发布平台段化 + 收尾清账）**。
出包窗口照旧：dev 云端已说批 1–5+7 全部新名，**车队浏览停摆至装机**（真机簇 148/149/152/153 同一个包）。

## 1. 权威产物指针

| 产物 | 位置 |
| --- | --- |
| 蓝图（批 5/7 行已标 ✅ 含落地名表） | `docs/edge-command-grammar.md` §6.2 / §6.3 |
| 批 5 归档（关联键决策全记录） | `openspec/changes/archive/2026-08-07-objectify-interaction-vocabulary/` |
| 批 7 归档（应答族约定 + kernel 类型面教训） | `openspec/changes/archive/2026-08-07-normalize-nonplatform-vocabulary/` |
| **新机器闸** `scripts/action-key-parity` | 关联键三表跨仓对账（键集 ⊆ / 同键同值 / 不对称须显式豁免）；已入集成复验序列 |
| 真机簇 153 | `docs/real-machine-acceptance-backlog.md`（与 148/149/152 同一次出包） |

当前总账：**107 消息 / 56 条云端可下发命令**（以两份 protocol.ts 穷举为准）。kernel 现版 **v0.1.3**。
落点：edge master `88e8a51` / automation master `5992b36`（+ lock 对齐 `2f42f46`）/ kernel `7bcfdef`+tag v0.1.3。
dev 已部署（备份 `automation.bak.20260807-142737.vocab-batch5-7.tar.gz`，healthcheck 全过）。

## 2. 本轮最重要的裁定与修正（批 6 直接受用）

1. **关联键值＝风控动作名命名空间，永久冻结**（推翻上一份交接「批 5 必须动值」的预判）：
   值与 `RISK_ACTIONS` 逐字同名**是设计**（kernel 枚举 + 9 张 DB CHECK + ~120 消费点钉死）。
   改协议名的批次**只换三张映射表的键、值永远不动**；多个新名映回同一个值完全合法
   （`facebook.video.like`→`like`）。批 6 照此办理。
2. **video 对象两个位置都合法**：0.25 概率赞的对象是 **feed 里的视频帖**不是 Reels；引擎对象核对
   唯一不可能组合＝「note 对象 × Reels 面」（`object_mismatch_observed_reels`）。设计时「按对象拆
   不按位置拆」的字面义要认真对待——对象≠面。
3. **应答族约定已定案**：请求＝祈使动词，edge→cloud 应答/自发事实上报＝过去分词事实形
   （observed/acquired/released/detected/cleared）。豁免：ping/pong、`.result`/`.ack` 族（批 6 IM 域
   定夺）、`captcha.assist.*` 子族。新增消息对照此约定。
4. **「kernel 不需要出版本」这类前置结论要查两面**：批 7 前置只查了传输豁免名单、漏了类型面
   （`IdentityCaptureCommand` 字面量），实装期才发现 → kernel v0.1.3。**批 6 已知必命中 kernel 两面**：
   豁免名单点名 `edge.task.acquire/release`（改 `task.*` 时）+ 类型面待查。
5. **npm 会把 git pin 改写成 `github:` 形**（`npm install <pkg>@<spec>` 后要手工恢复 `git+ssh://` 形，
   lock 内层 dependencies 镜像也会残留旧形——本轮在 canonical 补了一刀 `2f42f46`）。

## 3. 工序增量（批 4 工序仍有效，本轮新增）

- 集成复验序列现在是**四道**：protocol-parity + operation-registry-parity + **action-key-parity** + typecheck。
- `action-key-parity` 的 `EDGE_ONLY_EXEMPT` 名单是显式豁免制——词汇批改到 identity/session 类命令名时
  **名单要同步改**（批 7 已把 `identity.read_current` 改成 `identity.read_current_page`）。
- 并行批次的 digest 会撞：两批都动 manifest 时，后落批 rebase 后**必须第三次重算重钉**五位点
  （本轮实测：批 5 `b5da30fb` → 批 7 rebase 后 `42c5a2b7`）。
- cargo 用 `~/.rustup/toolchains/1.97.1-aarch64-apple-darwin/bin`（stable 1.87 会被 crate 拒）。
- 机械 spec delta 的标题含旧名时用 `## RENAMED Requirements`（FROM/TO）+ MODIFIED 新标题双段
  （本轮两例：comment-interaction、browser-cold-standby）。

## 4. 批 6 开工须知

**范围**（蓝图 §6.2 批 6 行）：IM 族 10 条 → `wechat.inbox.*`（「interaction」一词整体退役）·
发布平台段化（`{p}.publish.command`，原子 kind 表分平台，**删载荷 `platform?` 字段**——全协议唯一
「平台维进载荷」处，缺省静默当小红书）· `navigation.back` 与 `note.close` 定分工后平台段化
（`note.close` 云端零发送点）· `edge.task.*` → `task.*`。

**已知前置**：
1. kernel 必出新版本（豁免名单 `edge.task.acquire/release` + 类型面全查）。
2. IM 族改名连带 `.result`/`.ack` 应答约定裁决（§2 第 3 条豁免的到期日）。
3. `publish.approval_action` 家族按信封 id 关联、不进主动命令白名单（CLAUDE.md §2 注）——发布段化时别误加。
4. 发布链是 content 仓域（生成/发布管线）——批 6 可能第一次把词汇批的改动面扩到 automation 之外，
   `aidcp-content` 仓的协议副本与 kernel pin 落后问题（api `v0.1.1`、content `v0.1.0`）届时一并核。

## 5. 未收口线头（沿上一份，更新后）

1. **出包（唯一挡路项，用户开口才打）**：积压批 1–5+7 + 身份闸换血 + 问现状。簇 148/149/152/153 全等它。
2. api / content 两仓 kernel pin 落后（v0.1.1 / v0.1.0，现最新 v0.1.3）；不推浏览命令、非阻塞。
3. `state.read`（应答已改名 `state.observed`）仍零触发方——阶段四开篇，无人接。
4. `interaction.reply.send` 不受页面身份闸约束的棘轮——批 6 改 `wechat.inbox.*` 时这条豁免集合要跟着改名，
   别静默扩。
5. 阶段三（动作/检查拆分）排在词汇批后。
