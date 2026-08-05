## 1. aidcp-edge — 面板空态占位（前置，已落地）

- [x] 1.1 没有过程条目时不让空的过程容器参与占位，空态说明直接接在面板标题之后，阶段预告不被裁切 <!-- aidcp-edge bdc652f 前置修复，先于本 change 立项落地 -->

## 2. aidcp-edge — 活动流接入内容工作区

- [x] 2.1 内容工作区新增按环境的活动缓冲与 `pushActivity(entry)` / `setActivities(list)` 接口，条数有界，切换环境时清理非当前环境的展示状态 <!-- aidcp-edge 553d6b2 上限 12 条；换账号即丢弃上一账号记录 -->
- [x] 2.2 `renderer.js` 在 `routeActivity` 单点转发活动条目给内容工作区（保持 envId 归属判断在原处，不新增第二个订阅点） <!-- aidcp-edge 553d6b2 -->
- [x] 2.3 切换到小红书环境时把该环境已有缓冲整体补发给内容工作区，避免刚切过去时面板空白而运行面板有内容 <!-- aidcp-edge 553d6b2 syncContentWorkspaceActivities -->

## 3. aidcp-edge — 面板取数模型与三态

- [x] 3.1 面板取数模型新增 `kind: 'activity'` 分支：创作任务投影优先，无任务时用活动记录，条目只携带真实 `ts` 与句子 <!-- aidcp-edge 553d6b2 -->
- [x] 3.2 三态判定改按来源状态（创作队列 / 待审稿的读取状态），不再以数据是否为空作唯一依据 <!-- aidcp-edge 553d6b2 workSourceFailure -->
- [x] 3.3 读取失败时面板呈现「暂时读不到当前进度」并提供重试入口，不再显示「当前没有正在进行的任务」 <!-- aidcp-edge 553d6b2 过程区空态文案同步改口，不再讲「任务开始后会展示」 -->
- [x] 3.4 左栏文案按九档运行态取值：仅浏览循环已跑起来时才可讲成正在浏览，其余档位沿用既有诚实文案 <!-- aidcp-edge 553d6b2 复用既有 browseActivity 判据 -->

## 4. aidcp-edge — 活动记录的呈现约束

- [x] 4.1 活动条目渲染为「相对时间 + 句子」，不显示阶段名、不显示完成勾，使用中性标记 <!-- aidcp-edge 553d6b2 -->
- [x] 4.2 仅在浏览循环已跑起来时，最新一条带进行中标记与逐字效果；其余档位全部按历史呈现且无动效 <!-- aidcp-edge 553d6b2 -->
- [x] 4.3 相对时间按原始 `ts` 重算，重渲染不得把旧条目改写为刚刚发生 <!-- aidcp-edge 553d6b2 复用 uiLogic.relTime，缺席时不显示时间而非编造 -->
- [x] 4.4 面板高度与横向溢出不回归：条目多时由过程区自身滚动承载，面板总高仍不超过 255px <!-- aidcp-edge 553d6b2 沿用既有 overflow:auto，未改高度 -->

## 5. aidcp-edge — 测试

- [x] 5.1 用例：无创作任务 + 浏览已跑起来 + 有活动记录 → 面板展示活动条目，且不出现「当前没有正在进行的任务」 <!-- aidcp-edge 553d6b2 -->
- [x] 5.2 用例：环境已暂停 / 已停止但有活动记录 → 条目按历史呈现，最新一条不带进行中语义与动效 <!-- aidcp-edge 553d6b2 -->
- [x] 5.3 用例：创作队列读取失败 → 面板显示「暂时读不到当前进度」并可重试，不宣布没有任务 <!-- aidcp-edge 553d6b2 重试断言真的再读一次，不只换文案 -->
- [x] 5.4 用例：创作任务存在时仍优先展示任务投影，活动记录不覆盖阶段链 <!-- aidcp-edge 553d6b2 -->
- [x] 5.5 用例：活动记录不产生阶段名 / 完成勾 / 完成度 <!-- aidcp-edge 553d6b2 并入 5.1 用例断言 -->
- [x] 5.6 回归：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿 <!-- aidcp-edge 553d6b2 验收 39/39、全量 3158/3158、typecheck 干净 -->

## 6. 收尾

- [x] 6.1 提交并推送 aidcp-edge（默认分支 master），把 commit-sha 回写本 change 的 tasks.md <!-- aidcp-edge 553d6b2 已推 origin/master -->
- [x] 6.2 `openspec validate surface-browse-activity-in-work-card --strict` 通过
- [x] 6.3 真机验收项（面板在真实浏览会话下的条目密度与可读性）登记到 `docs/real-machine-acceptance-backlog.md` <!-- 簇 140 -->

## 7. 同批修复（用户当场报出，不属本 change 的 spec delta）

- [x] 7.1 排期页「打开浏览器 / 启动当前环境」按钮不随真实运行态更新：浏览器判据比对了投影里不存在的档位 `open`（恒为假），生命周期判据把「已启动」误判成「正在跑」 <!-- aidcp-edge 52f87c3 测试曾用同一个不存在的值断言，故长期全绿 -->
- [x] 7.2 工作面板身份行去掉并列的产品助手名：它来自对设计稿的误读（那是另一个账号名，不是助手身份） <!-- aidcp-edge 553d6b2 -->
- [x] 7.3 「最值得看的灵感」空态里的同名活动文案一并去掉 <!-- aidcp-edge 553d6b2 -->

