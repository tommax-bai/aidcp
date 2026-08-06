# 交接 · 命令词汇改造（语法已立，批 1–3 已落，批 4 起接力）（2026-08-06）

> **给接手 session**：本文只承载**会随会话消失的东西**——裁定、工序、坑、待决。
> 已成规格与文档的只给指针，不重抄。上一份交接（`handoff-2026-08-06-edge-addressing-layers.md`）
> 的六步计划已被本轮大幅推进与重排，以本文为准。
>
> ⚠️ 凡本文写「已核」的只代表 2026-08-06 晚。fleet 高度活跃，接手第一件事自己重核。

---

## 0. 一句话现状

命令语言的**宪法**（六条语法规则）与**改造清单**（46 条蓝图、六批）已归档成规格；
**批 1（删死命令）、批 2（改类根治）、批 3（问现状探针）已全链落地**（master + dev 部署 + 归档）。
协议 96 → 95（净 -3 死命令 +2 观察命令）。**下一步＝批 4：浏览词汇平台化（最大改名批）。**

---

## 1. 权威产物指针（先读这些，不读旧对话）

| 产物 | 位置 |
| --- | --- |
| **命令语法 + 46 条蓝图（含批次状态）** | `docs/edge-command-grammar.md`（§6.2 逐条处置、§6.3 批次表——批 1 行已标 ✅ 与 plan.response 结论） |
| 语法规格（7 要求） | `openspec/specs/edge-command-grammar/spec.md` |
| 问现状规格 | `openspec/specs/edge-state-observation/spec.md` |
| 编址分层尺子 | `docs/edge-addressing-layers.md` |
| 四个归档 change（实装细节全在各自 tasks.md 的实录节） | `openspec/changes/archive/2026-08-06-{establish-edge-command-grammar, drop-dead-cloud-edge-commands, recategorize-nonpage-commands, add-state-observation-command}/` |
| 说明书收口（落地未归档，见 §5） | `openspec/changes/close-account-layer-operation-manual/` |
| 审阅页（用户看过的汇总） | claude.ai artifact `948f1572-46bb-475f-b68c-d081b3061014` |

---

## 2. 用户裁定（全部定案，MUST NOT 重议；完整记录在语法 change 的 design 修订史）

1. **核心目标＝CLI 层功能清晰**；OpenCLI 非常值得借鉴、充分参考（借四不借一，见语法文档 §5）。
2. **平台进命令名（编法 A）**：`平台.面/对象.能力`；宿主/环境/翻译/编排域**不带**平台段。
   我方曾推荐说明书加平台支持集维（编法 B），被裁定否；勿再提 B。
3. **迁移＝直接切换**：不考虑老客户端、无双名并行、无别名映射、无墓碑。旧名从两份协议穷举表直接删，
   typecheck 即守卫。出包不是障碍（例行动作）、升级不原子可接受——**别再拿这两条当设计理由**（有记忆条目）。
4. **「确认不了」→ 当发了**（业务处置口径；报告仍三态诚实；「确认未发生」可预算内重试）。
   阶段三的产品前置**已全部齐**。
5. 后续新增浏览器操作必须先过六条语法（记忆 `edge-command-grammar-ruler`）。

---

## 3. 本轮建立的工序（接手照用，别重新发明）

- **双仓锁步落地**：改协议/登记表的批都同时动 edge + automation 同一受比对文件，`land-change`
  单仓串行模型在中间态必红。流程＝各 worktree rebase → 全量测试 + gate:native → **成对 ff push**
  （`git push origin <branch>:master` ×2，中间不跑闸）→ 立即 `scripts/protocol-parity` +
  `scripts/operation-registry-parity` 复验全绿 → 部署 → 清 worktree。
- **变异验证 MUST 先 commit 再变异**（本轮同坑两踩，记忆 `mutation-restore-needs-committed-baseline`）：
  实装 → 全绿 → commit → 变异 → 红 → `git checkout --` 复原 → **复跑确认回绿**。
- **删/改协议命令的引擎连锁**（批 1 实测趟出的完整清单，批 4 改名会全部再遇到）：
  ① TS 侧穷举表逐个点名残留（修到绿）；② `native/page-engine/command-manifest.json`（TS 可达面）删条 ⇒
  receipts 契约测试；③ `command-postconditions.json` 是**引擎侧**盘点（Rust 没删就不能删条目）；
  ④ Rust 词表闸：变体必须在清单**或** `MANIFEST_EXCLUDED_COMMAND_KINDS` 排除表（带理由）；
  ⑤ 改了 manifest/Rust 后 `node scripts/build-native-page-engine.mjs` 重钉产物摘要；
  ⑥ 测试夹具硬编码旧 capabilityDigest 的两个文件：`test/electron/native-page-engine-artifact.test.ts`、
  `test/electron/macos-signed-artifact.test.ts`。
- **云端事实源已翻转**（invert-split-fact-source cutover）：aidcp-cloud src 冻结，协议/自动化侧一律落
  `../aidcp-automation`。两道 parity 闸已由本轮加了翻转感知（读 `scripts/fact-source.json`）；
  该 change 6.2 剩余 7 个脚本改指仍归它。
- 部署 dev＝`aidcp-automation` 派生服务（备份 `automation.bak.<ts>.<tag>.tar.gz` → rsync → restart →
  healthcheck：active / NRestarts=0 / 8787 / 日志零 error）。**绝不碰 aidcp-cloud 单体与 isales。**

---

## 4. 批 4 开工须知（下一棒的活）

**范围**（蓝图 §6.2「浏览词汇平台化 + 拆分（14 条 → 批 4）」）：页面手势/导航/面命令全部加平台段
（`note.open` → `xiaohongshu.note.open` / `facebook.note.open`…）；`page.scroll` 同批按面拆
（从调用点与 `reason` 取值枚举实际在用的面；已坐实 feed/search，群组与 Reels 待核）；
`group.join` → `facebook.group.join`；notification 五条支持平台待核（通知巡视今天只在小红书跑）。

**已就位的依赖**：
- **平台段闸两端已休眠待命**（批 2）：edge `edge-client.ts` 入口 + automation `ws-server.ts` 出口，
  枚举 `PLATFORM_SEGMENTS = {xiaohongshu, facebook, wechat_channels}` 两处同值——批 4 改名后自动生效，
  第一条真实平台段命令会被校验。
- 语法规格第 6 要求管迁移形态（直接切换、批次串行、蓝图为准）。

**注意**：
- 这是**协议热区最大批**：两份 protocol.ts + 三份登记表 + edge-client 白名单 + `command-bridge.ts` 映射
  + **动作关联键**（协议第 5 处同步点：两侧 21 条动作名映射表，批 5 更重但批 4 也会碰）+ 引擎 manifest 的
  `routeKey/edgeType` + 云端所有下发点。§3 的引擎连锁清单全程适用。
- Rust 侧遗留可顺手清：`browse_next`/`browse_scroll` 变体 + postconditions 两条 + 排除表两条
  （批 1 留的过渡态，批 4 动引擎时一并删）。
- 改名后 AC-PROTO-02 计数不变（改名非增删）；protocol.md §2 表与载荷节要同步改名。

**批 5/6 排在批 4 后**（互动对象化 5 条；IM 族 `wechat.inbox.*` 10 条 + publish 平台段 +
`navigation.back` vs `note.close` 分工坐实）。

---

## 5. 未收口的线头（按急缓）

1. **close-account-layer-operation-manual 不能归档**：前置＝`align-cloud-edge-operation-registries`
   的 delta 措辞对账（其 8.1/8.2——主 spec 最终措辞必须是「全部描述符字段」不是「四个字段」）。
   那条 change 自身卡在出包验收（4.5/6.5）。
2. **出包一次**（用户显式触发才做）：累积的边缘 TS 改动（说明书收口、批 1–3、身份闸换血、问现状）
   全部要出包才到运营机。挂着的真机簇：148（身份闸换血观察）、149（问现状六项）+ 更早的 121/141。
3. **state.read 零触发方**：通道已通（`RoleDispatcher.askEdgeState()`），何时问/问完怎么改航向
   ＝**阶段四（观测决策上移）的开篇**。真机验收前需临时脚本手动调用。
4. **阶段三（动作/检查拆分）**产品前置已齐（§2 裁定 4），排在词汇批后：可重放侧（回执不言成功）+
   不可逆侧（检查命令从动作里拆出 + 当发了处置 + 占比告警 + 回填通道两条 MUST）。
5. **已钉成棘轮的已知缺口**：`interaction.reply.send` 留痕却不受页面身份闸约束（API 路径）——
   测试写死豁免集合「恰好这一条」；要不要给 API 写路径设独立身份闸＝产品裁决，别静默扩豁免。
6. kernel 传输闸类别词汇（`TransportControlCategory`）没有新两类——两处调用点按映射处理中；
   真扩要动 aidcp-kernel + 三仓 pin，值得独立小 change。

---

## 6. 本轮弯路（别重走）

- ~~「出包才生效所以不批量改名」~~、~~「升级不原子所以双名并行」~~——都被裁定推翻，词汇批直接切换。
- ~~「命令名+回执是云端的全部输入」~~——撤回过又从对照表漏回来一次；写对照/摘要时对照语法文档 §7 作废清单自查。
- agent 并行时两套 `page_observation` 定义各自生长——集成时合一取批 2 的；**并行批注定撞登记表，
  预先在 tasks 头部写清「后到者 rebase、类别词汇以先落地者为准」**（本轮这么做了，有效）。
- 批 3 曾按 tasks 里「反向断言自动覆盖新命令」直接信——agent 核实**不成立**（过滤器只认 page_automation），
  已修。台账里的「自动」都要实测。

## 7. 接手起手式

```bash
git -C /Users/baitianxing/codes/aidcp branch --show-current   # main
scripts/task-preflight                                         # 四 canonical 全默认分支（含翻转冻结校验）
openspec list                                                  # 活跃 change 现状
python3 scripts/protocol-parity && python3 scripts/operation-registry-parity   # 两闸绿（44 条）
git -C ../aidcp-edge log --oneline -3; git -C ../aidcp-automation log --oneline -3
```

开批 4：`openspec new change` 照批 1–3 的 change 形态（proposal/design/specs/tasks + 实录节），
工序照 §3。用户已授权「继续吧 尽量并行」——批 4 是协议热区串行批，**不建议**与批 5/6 并行（同热区），
可并行的是阶段四的设计前期或出包后的真机验收。
