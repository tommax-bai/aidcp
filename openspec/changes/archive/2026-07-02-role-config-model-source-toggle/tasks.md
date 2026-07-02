<!-- 状态注记（2026-07-02，已上线）：纯前端 change，仅 aidcp-console `src/pages/RolesPage.tsx`。
  两次提交（bd5320c 预填 + 52e1b2b 来源二态/思考自愈）已推 origin/master（52e1b2b 在并发方 0baf92e 之上 rebase 落地）；
  各自 build 后备份 + rsync（无 --delete、intro.* 保全）部署 /opt/aidcp/console 并验证 LIVE：
  首发 index-DzaRG0C0.js、终发 index-DoLWjLkV.js，8088 HTTP 200、/api 与 intro.html 200、cloud/isales 未受扰。
  cloud 侧零改动（后端契约原样复用）。tsc + build 全过；无自动化 UI 测试，逐态人工走查 + 一轮对抗性评审兜底。 -->

## 1. aidcp-console — 编辑弹窗预填当前生效值

- [x] 1.1 `openEdit` / `openCatEdit` 打开时把模型名带出**当前生效模型** `effectiveModel`（含继承值）、厂商带出 `effectiveProvider`，与列表「当前生效模型」列一致 <!-- aidcp-console bd5320c；后被 52e1b2b 并入二态实现 -->

## 2. aidcp-console — 显式「模型来源」二态（继承 / 自定义）

- [x] 2.1 新增 `modelMode` / `catModelMode` ∈ {`inherit`,`custom`}，`openEdit`/`openCatEdit` 按 `row.modelOverridden` 初始化 <!-- aidcp-console 52e1b2b -->
- [x] 2.2 角色 + 分类两个弹窗各加 AntD `Segmented`（继承 / 自定义）：继承态收起厂商/模型名输入、以 `Alert` 呈现当前生效值与「保存即取消本行覆盖」；自定义态展开输入并预填生效值 <!-- aidcp-console 52e1b2b -->
- [x] 2.3 `onOk` 按来源送 `model`：继承→`''`（后端清覆盖、分类经 mutationFn 归 `null`）；自定义→当前值（后端按厂商探活）。厂商 / 温度 / 思考照常随发 <!-- aidcp-console 52e1b2b -->
- [x] 2.4 诚实闸：自定义态空模型名 `message.warning` 拦下、不 mutate（无意义空覆盖不退化成静默回落）；「只改厂商不改模型」不再被静默丢弃 <!-- aidcp-console 52e1b2b -->
- [x] 2.5 「把继承值固定为覆盖」得证：继承行切自定义、保留预填值保存 = 建等值覆盖（冻结、不再随上层变动），此前不可能 <!-- aidcp-console 52e1b2b -->

## 3. aidcp-console — 思考「开启」自愈与同源判定

- [x] 3.1 思考「开启」可用性上提为组件级派生值 `roleThinkingOnOk`/`catThinkingOnOk`（自定义且填模型→前端镜像 `thinkingOnSupported`，与云端 `buildThinkingParams` 同源；否则用后端 `thinkingOnAvailable`），选择器 `disabled` 与之同源 <!-- aidcp-console 52e1b2b -->
- [x] 3.2 两个 `useEffect`：当「开启」变不可用且当前选中 `on` 时把 `thinkingInput`/`catThinkingInput` 收回 `default`，杜绝「禁用却仍选中 on」并防不支持组合被静默存成 `on` <!-- aidcp-console 52e1b2b -->

## 4. 校验 / 回归 / 部署

- [x] 4.1 console `tsc --noEmit` 净、`npm run build` 过；逐态人工走查（继承↔自定义、空自定义拦截、改厂商、思考自愈）<!-- 无 lint 脚本；无自动化 UI 测试 -->
- [x] 4.2 后端零改动核验：面板 API 契约与角色/分类模型解析、思考出口翻译均未动，前端如实复用 `model===''` 清覆盖 / 非空探活语义 <!-- cloud 未改一行 -->
- [x] 4.3 部署 console 到 ECS `/opt/aidcp/console`：build → 备份（index.html.bak + console.build.bak.tar.gz）→ rsync `dist/`（**无 --delete**）→ 验证 LIVE bundle 指向新 hash、8088/api/intro 均 200、isales 未受扰 <!-- 首发 index-DzaRG0C0.js、终发 index-DoLWjLkV.js；见 [[console-deploy-nginx-root]] -->
- [x] 4.4 并发工作树处理：推送遇非快进（并发方 0baf92e 改 AccountsTable），核对其脏文件已在远端后 rebase 落地、无冲突、绝不 force <!-- 见 [[concurrent-session-shares-subrepo-worktree]] -->
