# Tasks — edge-fleet-rail-env-management

> 全落 `aidcp-edge` renderer（`index.html` / `renderer.js` / `styles.css`）。云端 / console 零改。
> **实装 sha**：`2f68469`（rail 环境管理 + 人设浮层 + 精简设置）、`833a4ee`（浮层可见性 + 收起态布局修复）。

## 1. 环境管理搬进左栏

- [x] 1.1 左栏栏头「＋ 添加环境」+ 收起态栏尾「＋」拉起独立浮层；两页签「加入现有环境」（多选 AdsPower 环境）/「新建环境」（模板 + 平台创建）；手动分身 ID 折叠在加入页内 <!-- aidcp-edge 2f68469 env-add-panel + openEnvAddPanel/switchEnvTab -->
- [x] 1.2 加入/新建即时落盘（`saveSettings` 带 `environments`）→ main 建 handle → 左栏立即出现该环境离线行（根治「点了显示已加入但左栏看不到」）<!-- aidcp-edge 2f68469 persistRoster()，selectProfile/removeFromRoster/ads-manual-add/adsCreate 触发 -->
- [x] 1.3 左栏对齐 v2.3 稿：环境计数 + 运行/需处理/离线汇总 chip + 按紧迫度分组（需要处理/运行中/暂停·离线）+ 每行头像 + 昵称 + 状态点/文案 <!-- aidcp-edge 2f68469 renderRail 分组 + RAIL_GROUPS + rail-sum -->

## 2. 每环境人设浮层

- [x] 2.1 每行昵称后人设图标（未设置淡描边 / 已设置品牌色）；点击选中该环境并弹独立人设浮层，envId 路由 generate/persist（绝不跨账号） <!-- aidcp-edge 2f68469 rail-persona + openPersonaPop + persona-pop（向导从抽屉搬入） -->

## 3. 精简设置抽屉

- [x] 3.1 设置抽屉精简为 浏览器引擎（AdsPower API Key/地址收进其高级折叠）+ 窗口停放 + 显示开发者开关；环境列表 / 创建 / 人设向导均移出抽屉 <!-- aidcp-edge 2f68469 index.html drawer 精简 + ads-advanced2 -->
- [x] 3.2 待配置主动步骤改为直达左栏「添加环境」面板（不再开设置抽屉）<!-- aidcp-edge 2f68469 promptMissingAdsProfile / noticeAction → openEnvAddPanel -->

## 4. 真机反馈修复 + 回归 + 归档

- [x] 4.1 浮层只见遮罩不见内容（`.hidden` 为 `!important`，open 只加 `.open` 没去 `hidden`）→ open 移除 hidden、close 复加 <!-- aidcp-edge 833a4ee open/closeEnvAddPanel + openPersonaPop/closePersonaPop -->
- [x] 4.2 收起态头像比行大 / 名字块重叠 → 收起态行固定 44×40 居中格、名字块 `display:none !important`、头像缩 28px + 紧色环；展开态 216→168px <!-- aidcp-edge 833a4ee styles.css 收起态 + 宽度 -->
- [x] 4.3 回归断言：加入即落盘（`saveSettings` 带 environments）、「＋」开面板且移除 hidden、设置抽屉不含环境列表/人设向导、人设图标点击开浮层并选中该环境 <!-- aidcp-edge 2f68469/833a4ee fleet-console.test.ts 新增 4 条 + companion-ui/renderer-smoke 随迁更新；791 test 全绿 -->
- [x] 4.4 真机视觉验收登记 backlog 簇 24；`openspec validate --strict` → archive <!-- 控制仓：backlog 簇 24 已登记（3fe243e）；本回写 + archive -->

## 5. 说明

- 纯 renderer 视觉 / 交互重排，无 spec 红线（诚实 / 身份 / 隔离）变动；envId 路由 persist 沿用 `edge-multi-environment-fleet` 的 per-env 路由，人设不跨账号不变。
- 桩层 jsdom 测结构 + 逻辑；像素级视觉照 v2.3 稿 CSS 移植，真机核。
