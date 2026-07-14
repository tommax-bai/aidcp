# Tasks — edge-rail-fixed-height-scroll

## 1. aidcp-edge — 环境栏固定高度 + 栏内滚动（styles.css）

- [x] 1.1 `.env-rail` 由 `min-height: calc(100vh - 46px)` 改为固定高度 + `position: sticky; top: 46px`，并 `align-self: flex-start` <!-- aidcp-edge f34af1b 对抗评审校订：真正的承重项是 height（定高后 stretch 本就不生效），align-self 只是护栏、非必需——注释已写明，防后人删 height 留 align-self 而静默失效 -->
- [x] 1.2 只有 `#rail-list` 滚动：`overflow-y: auto` + `overflow-x: hidden` + `overscroll-behavior: contain`；栏头 / 汇总 chip / 栏尾动作区一律 `flex-shrink: 0` <!-- aidcp-edge f34af1b 红线：`.rail-list` 的 `min-height` 必须留 0——评审揪出「给列表设 min-height 下限」会把栏尾挤到 sticky 栏底边以下，那片区域滚多少页都够不着（「全部启动」永久失联），比列表被压扁严重得多 -->
- [x] 1.3 分组标题 `.rail-group` 在滚动区内吸顶（仅展开态；收起态该元素是 1px 分隔线，显式 `position: static` 复位） <!-- aidcp-edge f34af1b 吸顶头自带不透明底色 #f8fafd（列表无自身背景，否则行从字底透出） -->
- [x] 1.4 细滚动条（webkit）：静息隐形、指针进栏显形；收起态窄条不留滚动条槽 <!-- aidcp-edge f34af1b 评审揪出：Chromium 样式化滚动条是「经典条」实占 6px 布局宽，栏内容宽 43→37px 会裁掉行右侧状态色环（收起态唯一状态信号）→ 收起态 scrollbar 宽 0 + 行宽 44→42px；绝不改 width:auto（margin auto 会禁掉 flex 拉伸、行塌成 28px 头像宽） -->
- [x] 1.5 核对不引入新裁剪 <!-- aidcp-edge f34af1b 审计结论：所有浮层（人设 / 添加环境 / 代理 / 健康 / 抽屉 / 遮罩）都是 body 级 position:fixed 兄弟节点，行内悬停提示是原生 title → 新滚动容器当前裁不到任何东西。红线记在 CSS 注释：`.rail-list` 现在两轴都裁，将来任何放在行内的自定义悬停卡 / 右键菜单必须 portal 到 body；且绝不给 `.env-rail` / `.fleet-row` 加 overflow / transform / filter / contain -->

## 2. aidcp-edge — 滚动位置稳定性（renderer.js）

- [x] 2.1 `renderRail()` 全量重建前后保持 `#rail-list` 的 `scrollTop` <!-- aidcp-edge f34af1b -->
- [x] 2.2 选中环境变化时把选中行滚入视野；选中未变的普通刷新不改滚动位置 <!-- aidcp-edge f34af1b 用 scrollTop 算术自实现 scrollRailRowIntoView，绝不用 element.scrollIntoView：① 它会连带滚动所有可滚祖先（文档跟着抖）；② jsdom 里根本没有该方法，裸调会在渲染层抛异常、连带打死 4 个测试文件共 111 个用例。另在引导流 showGuideStep 补一次幂等滚动（selectEnv 对「已是选中项」早退，不补则正在引导的行可能停在视野外） -->
- [x] 2.3 空名册 / 收起⇄展开切换时的滚动位置行为不出异常 <!-- aidcp-edge f34af1b 收↔展换的是行高体系、旧滚动位无意义 → 那一次不还原，改为把选中行滚进视野；空态直接 return（无可滚内容） -->

## 3. aidcp-edge — 回归测试

- [x] 3.1 CSS 契约断言（定高 / sticky / 列表内滚 / overscroll 隔离 / min-height:0 红线） <!-- aidcp-edge f34af1b 把真实 styles.css 注入成 <style>，jsdom 会解析级联 → 断言的是「规则真的命中了这个元素」，而非既有测试那种「文件里有这段文本」 -->
- [x] 3.2 行为断言：重建后 `scrollTop` 保持；栏头栏尾不落进滚动容器；签名未变不动滚动位 <!-- aidcp-edge f34af1b 4 个新用例（fleet-console.test.ts）。jsdom 无布局、scrollTop 永不被夹回 0 → 补一条「清空即夹回 0」的 stub，否则「重建后仍是 120」在零实现时也假绿；已实测判别性：撤掉实现 2 个新用例真会红 -->
- [x] 3.3 `npm test` + `npm run typecheck` 全绿 <!-- aidcp-edge f34af1b 1163 tests pass / acceptance 19 pass / typecheck 干净 -->

## 4. 收尾

- [x] 4.1 land 到 `aidcp-edge` master <!-- aidcp-edge f34af1b ff-push origin/master，主 checkout 已同步；edge-only，无 ECS 部署 -->
- [x] 4.2 真机验收项登记 `docs/real-machine-acceptance-backlog.md` <!-- 簇 62 -->
- [x] 4.3 `openspec validate edge-rail-fixed-height-scroll --strict` → archive
