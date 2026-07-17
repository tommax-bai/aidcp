# tasks — wechat-inbox-im-drilldown

> 全部改动落 `aidcp-edge`（`src/electron/renderer/`）。控制仓只回写本文件。
> 台账格式：`<!-- <repo> <commit-sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`。

## 1. aidcp-edge — 骨架与样式

- [ ] 1.1 `index.html`：收件箱骨架保留 `#iw-tabs` / `.iw-inbox` / `#iw-list` / `#iw-detail` 静态节点不变（锚定与覆盖层都依赖它们跨重绘存活），按需为详情面板加具名容器类
- [ ] 1.2 `styles.css`：`.iw-inbox` 加 `position: relative`；单栏态下详情面板 `position: absolute; inset: 0` 铺满收件箱区并加轻投影
- [ ] 1.3 `styles.css`：**红线**——显式写 `.pane[hidden] { display: none }`（或等价具名隐藏类），确保隐藏声明压过面板容器的 `display: flex`；否则 `hidden` 静默失效、覆盖层永久遮挡列表
- [ ] 1.4 `styles.css`：`.iw-tabs` 加 `scroll-margin-top`；新增 `.iw-iconbtn` 图标按钮样式（含 hover 与 `:focus-visible`）
- [ ] 1.5 `styles.css`：移除/停用列表条目的消息预览行样式（`.iw-item-preview`），确认无其他调用点

## 2. aidcp-edge — 列表级

- [ ] 2.1 `interaction-workspace.js` `renderList()`：条目模板去掉预览行，只留头像、昵称、时间、渠道来源、状态徽章；昵称占位与未读标记保持既有诚实语义
- [ ] 2.2 初始状态与切标签后 `selectedThreadId` 置空、不预取详情；确认 `renderTabs()` / 标签点击链路不再自动选中第一条
- [ ] 2.3 确认覆盖层打开期间列表 DOM 不卸载，关闭后滚动位置保留（列表重绘不做暂停，见 design 决策 6）

## 3. aidcp-edge — 详情级与退回路径

- [ ] 3.1 `renderDetail()`：列表级下**不渲染**详情内容（不只是样式隐藏），与 1.3 构成双保险
- [ ] 3.2 「刷新状态」改图标按钮，保持既有 `data-iw-action="refresh-detail"` 语义与真态呈现不变；注意冲突分支里第二处「重新加载详情」按钮沿用文字形态即可
- [ ] 3.3 新增关闭图标与左上角返回箭头，均带 `aria-label` 与可见焦点态；两者与 `Esc` 收敛到同一「清除选中 + 回列表级 + 锚定」动作
- [ ] 3.4 `Esc` 键处理挂载与卸载配对，避免切换工作区后残留监听

## 4. aidcp-edge — 锚定

- [ ] 4.1 打开与关闭详情时把 `#iw-tabs` 用 `scrollIntoView({ block: 'start' })` 锚到视口顶部
- [ ] 4.2 读 `prefers-reduced-motion`：开启时 `behavior: 'auto'` 直接定位，不播平滑滚动

## 5. 验证与集成

- [ ] 5.1 `cd ../aidcp-edge && npm run typecheck`
- [ ] 5.2 `cd ../aidcp-edge && npm run test:acceptance` 再全量 `npm test`（呈现层重构，重点回归 `edge-companion-ui` 既有的空态区分、未读标记与去重通知、非发送动作不被 send capability 拦截）
- [ ] 5.3 本地 `electron:dev` 实跑视频号工作区：列表级每条可点、点开遮挡、关闭回列表且滚动位置保留、锚定生效、三条退回路径均可用
- [ ] 5.4 提交并推送 edge `master`；无需出安装包（打包属用户显式触发）
- [ ] 5.5 回写本文件台账 sha（必须取自已推送提交）

## 6. 收口

- [ ] 6.1 真机验收项登记 `docs/real-machine-acceptance-backlog.md`（该渲染层无 DOM 测试基建，两级导航与锚定依赖真机手测）
- [ ] 6.2 `openspec validate wechat-inbox-im-drilldown --strict`
- [ ] 6.3 客户真机观感后定两个 open question：返回箭头是否与关闭叉并存、列表重绘是否需暂停
- [ ] 6.4 archive change
