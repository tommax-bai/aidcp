<!-- 状态注记（2026-07-02）：
  - CONSOLE 已提交推送：aidcp-console b9512a3（我的两文件 AccountsTable/AccountsPage，clean vs HEAD=e25e22e，build 绿）。
    注：thinking 的 console 部分已由并行方先提交（e25e22e），故我的 console 无交织、干净落地。
  - CLOUD 暂不提交、暂不部署：cloud 工作树处于**多 change 并行 live 编辑**状态——panel/types.ts、panel-server.ts、
    server.ts 现同时含我的 group-label + `role-thinking-mode-config`（thinking）+ `alert-resolution-by-id`（alertStore）
    三个 change 的 hunk，且文件在我操作期间被并行方持续改动（多次收到外部修改通知）。git 按整文件提交、本环境无交互式
    add -p，故无法只切出我的部分而不连带并行方**未完成/未提交**的 hunk。强行 revert/reapply 会与 live 并行方相撞、
    有 clobber 风险。→ 安全路径：等并行方的 cloud 改动先 commit（届时这 3 文件 diff 只剩我的 hunk，可干净提交），
    或由用户给我 cloud 独占访问（暂停其它 agent）后我一次修绿+提交。绝不把他人未完成 WIP 混进我的 commit。
  - 唯一 cloud 阻塞绿的是 `role-config-store.test.ts` 一个断言（thinking 归属、非本改动），属并行方修绿范畴。 -->

## 1. aidcp-cloud — 账号存储单写方法

- [x] 1.1 `AccountStore` 接口新增可选 `setGroupLabel(accountId, label): Promise<SetGroupLabelResult>`；新增导出判别联合类型 `SetGroupLabelResult`（`{ok:true,groupLabel}` / `{ok:false,reason:'account_not_found'|'retired_account'}`）<!-- aidcp-cloud 未提交 src/account-store.ts（clean-mine，无 WIP 交织） -->
- [x] 1.2 `PgAccountStore.setGroupLabel` 实现：`UPDATE accounts SET group_label=$2 WHERE account_id=$1 RETURNING group_label`；入参 `trim`（trim 后空 → 写 NULL）；0 行 → `{ok:false,account_not_found}`（不 seed 造行）；拒退役 `RETIRED_ACCOUNT_ID` → `{ok:false,retired_account}`（不落库）；防御性 64 长度上限 <!-- aidcp-cloud 未提交 src/account-store.ts -->
- [x] 1.3 单测（account-store）：写值 trim 后回读一致 + UPDATE-only（断言不含 INSERT）；空/空白/null → NULL 清空；不存在 → account_not_found 可区分；`default` → retired_account 且零 SQL <!-- aidcp-cloud 未提交 test/account-store.test.ts（4 用例全过） -->

## 2. aidcp-cloud — 面板 API 写路由

- [x] 2.1 `PanelDeps`（`src/panel/types.ts`）新增可选 `accountAttr.setGroupLabel`，注释说明经账号存储单写、不碰风控/协议/边缘 <!-- aidcp-cloud 未提交 src/panel/types.ts（**与 thinking WIP 交织**） -->
- [x] 2.2 `panel-server.ts` 新增 `PUT /api/accounts/:id/group-label`：JWT 已覆盖；body `{groupLabel}`（''/null/缺省=清空、非 string/null → 400 invalid_group_label）；未注入 dep → 503；成功回真态 `{accountId,groupLabel}`；not-found → 404；retired → 400 reason <!-- aidcp-cloud 未提交 src/panel/panel-server.ts（**与 thinking WIP 交织**） -->
- [x] 2.3 `src/server.ts` 注入 `accountAttr`（守卫：仅 `accountStore.setGroupLabel` 存在时注入，否则路由 503） <!-- aidcp-cloud 未提交 src/server.ts（**与 thinking WIP 交织**） -->
- [x] 2.4 单测（panel-server）：未注入→503；成功回真态；清空；not-found→404；`default`→400 retired_account；坏类型→400；缺 JWT→401 <!-- aidcp-cloud 未提交 test/panel-server.test.ts（用例全过） -->

## 3. aidcp-console — 前端可编辑「分组」列

- [x] 3.1 `AccountsTable.tsx`：「分组」列传 `onEditGroup` 时改为点击即编辑单元格（复用 `.editable-cell`「点击编辑」+ AntD `Input`，回车/失焦 `commit`、editingId 守卫幂等）；新增**可选** `onEditGroup?(accountId, label|null)` prop——不传退回纯文本 <!-- aidcp-console b9512a3 -->
- [x] 3.2 `AccountsPage.tsx`：新增 `useMutation` 打 `apiPut('/api/accounts/:id/group-label')`；**非乐观**——`onSuccess` 后 `invalidateQueries(['accounts'])` + 诚实 toast（设置/清除可辨）；经 `onEditGroup` 传入 `AccountsTable` <!-- aidcp-console b9512a3 -->
- [x] 3.3 `DashboardPage.tsx` 只读账号表**不传** `onEditGroup` → 保持纯文本、零回归（已核对：其调用仅 `accounts/loading/severitySorted`） <!-- 无需改动，现状即满足 -->
- [x] 3.4 复用 `styles/app.css` 既有 `.editable-cell`（悬停高亮 + pointer）；空值仍渲染破折号占位、单元格 `title="点击编辑"` <!-- 无需改样式，既有类满足 -->

## 4. 校验 / 回归 / 部署

- [x] 4.1 cloud：`npm run typecheck` 全绿；我的用例 targeted 全过（account-store 4 + panel-server group-label 1，合 22/22）。全量 `npm test` = 1048 tests / 1047 pass / **1 fail**，唯一失败在 `role-config-store.test.ts`（thinkingMode）——**并行 WIP，非本改动** <!-- 本改动零回归；红线 AC-* 全过 -->
- [x] 4.2 console：`tsc --noEmit` 对我的两文件零错误；`npm run build` 当前被 `RolesPage.tsx`（thinking WIP，未用变量 + 类型不符）阻断——**并行 WIP，非本改动** <!-- 我的文件 clean，构建阻断待 WIP 收尾 -->
- [x] 4.3 `openspec validate editable-account-group-label --strict` 通过
- [ ] 4.4 手动 / 端到端验证：后台点击「分组」→ 输入 → 保存 → 刷新后持久显示；清空 → 显示破折号；对已退役账号无编辑入口 / 被拒 <!-- 待部署后真机验证；本地未起 cloud（部署铁律） -->
- [ ] 4.5 提交 + 部署：**阻塞中**——需先解与 `role-thinking-mode-config` WIP 的文件交织（见顶部注记），且部署安全序列①「测试通过」当前因并行 WIP 未满足。按安全序列部署 cloud 面板层（备份→rsync→restart→healthcheck）+ console 构建产物按既有 nginx root 发布（不 --delete）；绝不碰 isales
