## Context

Facebook 个人时间线发帖序列由 cloud 逐条下发 `navigate_entry → select_mode → upload_image → fill_field → submit_publish → capture_postId`。`select_mode` 在 edge `FacebookPublishExecutor.openComposer()` 中实现，但当前只在导航后固定等待 2 秒、做一次入口快照：入口未渲染即 `no_target`。dev 的草稿 110 / 119 / 120 均在取得租约后 3–4 秒以 `seq=1 select_mode no_target` 结束；同账号草稿 111 / 125 又能在 60 秒以上的完整窗口内成功，证明这是页面落地/渐进渲染竞态，而不是账号、平台路由或越南语词表失效。

竞态同时带出一个更高优先级的安全边界：发帖前浏览器常停在 `/groups/...` 或帖子详情页，而 Facebook 小组页也可能出现 `write something`。当前 `navigate()` 只校验 hostname，旧页与首页同属 `facebook.com`，导航尚未落地时会被误报成功。若只把入口快照改成轮询，可能把“安全失败”放大成点击小组 composer，最终发错位置。

已有 `fb-publish-fill-deadline` 已把 `PublishCommandPayload.timeoutMs` 用作 edge 自我掐表、cloud 等待 `timeoutMs + resultSlackMs` 的通用机制。本变更复用该字段，不新增协议消息。已有 `facebook-consent-structural-detect` 单独负责 consent 自动处置；本变更只做只读页面分类和阻断，不复制或放宽 consent 点击策略。

## Goals / Non-Goals

**Goals:**

- 导航必须确认真的落到 Facebook 个人首页语境，旧小组/详情页不得因同域名被判成功。
- `select_mode` 在 cloud 下发的 40 秒预算内有界等待渐进渲染的入口与编辑器，并由 edge 先于 cloud 收敛。
- 首页语境未确认、存在阻断弹层、入口或编辑器超时时诚实失败，绝不猜测目标、绝不假成功。
- 目标类型护栏读取生产真实下发的 `optionKind` / `optionValue`，测试使用相同形状。
- 增加不含正文、cookie、token 的阶段日志，使导航未落地、入口超时、编辑器超时可区分。

**Non-Goals:**

- 不把所有 `failed_before_submit` 改为 cloud 自动重投；整序列重投策略另开 change。
- 不自动复活历史 `failed` 草稿 119 / 120，不直接修改线上 DB 状态。
- 不改变提交点击、`submitDispatched`、`submitted_unconfirmed` 或熔断语义。
- 不新增 consent 语言词表、不自动点击未被 consent 模块正向识别的弹层按钮。
- 不新增协议消息、角色、风险状态或数据库字段；`failedAt` 落库与委托失败卡展示由独立 change 处理。

## Decisions

### D1：导航成功采用“首页路由 + 页面主结构 + 阻断态排除”，不是 hostname

`navigate_entry` 发送 `Page.navigate('https://www.facebook.com/')` 后，在严格小于 cloud 默认 30 秒单指令窗口的 20 秒内轮询只读页面状态。成功至少要求：

1. hostname 为 Facebook 正式域名；
2. pathname 为个人首页形态（`/` 或 `/home.php`），明确排除 `/groups/...`、permalink、profile、login、checkpoint 等其他同域页面；
3. 页面不再是 `loading`，且存在可见主区域或已存在可复用的 composer 编辑器；
4. 不存在不属于 composer 的可见阻断 dialog / modal，也不存在凭据输入或 checkpoint/login URL。

轮询结束仍未满足时，按最后一次只读分类返回 `home_not_reached`、`login_required`、`checkpoint_detected` 或 `blocked_dialog`。页面探测异常返回 `nav_error`。日志只记录 pathname、分类、耗时和轮询次数，不记录 query、正文或账号秘密。

**否决：只看 pathname。** SPA 可先改 URL、后渲染主区域，仍会把竞态推给下一步。

**否决：把 composer 入口本身当导航成功的唯一判据。** 这会把导航和 `select_mode` 两步重新耦合，并无法区分“已到首页但入口晚渲染”与“仍在旧页面”。

### D2：`select_mode` 使用单个总 deadline，入口阶段最多占 20 秒

cloud 仅为 Facebook `select_mode` 下发 `timeoutMs=40_000`。edge 以该值为整个 `openComposer()` 的总预算：

- 已有可见 composer 编辑器时幂等成功；
- 否则先再次确认首页语境，再以 400ms 左右间隔只读轮询入口，入口阶段最多占 20 秒；
- 入口出现后计算坐标并只点击一次，再用总 deadline 的剩余预算等待可见编辑器；
- 入口阶段耗尽返回 `no_target`（日志分类为 `composer_trigger_timeout`）；点击后编辑器未出现返回 `post_validate_failed`（日志分类为 `composer_open_timeout`）。

边缘未收到 `timeoutMs` 时沿用小于 cloud 30 秒默认窗口的兼容兜底，不得让 edge 在 cloud 已判超时后继续操作。cloud 的等待仍由既有 `cmd.timeoutMs + resultSlackMs` 计算，因此 Facebook 此步为 48 秒；小红书不带该预算，行为逐字节不变。

**否决：固定增加 `sleep(7s)`。** 固定睡眠既拖慢热页面，也无法覆盖更慢渲染；deadline 轮询才能“出现即继续、到点诚实失败”。

**否决：重复点击入口。** 本事故发生在点击前；重复点击会扩大遮罩/重复 dialog 风险。首版只读轮询、确认目标后单击，后置验证不通过即诚实失败。

### D3：首页门必须在点击前再次校验

`navigate_entry` 与 `select_mode` 是两条独立网络指令，中间可能发生页面跳转或渲染变化。因此 `openComposer()` 不能只信任上一条命令的成功回执；每轮寻找入口时都必须同时读取首页语境。只要 pathname 离开首页或出现阻断 dialog，就停止并返回诚实失败，绝不在小组/详情页消费同文案入口。

### D4：目标护栏只信生产规范字段

cloud 真实下发形状为 `{ optionKind:'target', optionValue:'facebook_personal_timeline' }`。edge 必须读取 `params.optionKind` / `params.optionValue`：

- `optionKind` 缺省或为 `target` 且 `optionValue` 为 `facebook_personal_timeline` 时允许继续；
- 任何显式的其他目标值返回 `unsupported_target`；
- 不再以 `params.value` 作为目标授权来源，避免测试构造与生产形状漂移。

### D5：本 change 不扩 cloud 自动重投

edge 内的入口轮询只是重复只读探测，尚未点击，不会重复发布；cloud 重投则会重新运行导航、上传和填写，安全边界不同。持续 40 秒仍未找到入口说明可能是登录、检查点、布局漂移或真实不可用，继续由现有 fail-closed + 熔断保护收敛。若未来要保稿重投，必须用独立 `retryable_before_submit` 结果、明确副作用证据、次数上限和退避另行设计。

## Risks / Trade-offs

- **[首页 DOM 结构漂移导致保守失败]** → 路由是硬门，主结构只使用稳定 role/可见性信号；失败带分类日志，绝不退化为点击其他页面的相似文案。
- **[阻断 dialog 误把正常页面判不可用]** → 只在点击 composer 前阻断；已有 composer 编辑器的 dialog 明确豁免。宁可诚实失败，也不穿透遮罩盲点。
- **[新 cloud 配旧 edge 仍会单次快照失败]** → 分阶段部署不会产生错误发布，只是修复尚未生效；真机验收必须确认运行的是更新后的 edge。
- **[新 edge 配旧 cloud 的兼容窗口]** → edge 无 `timeoutMs` 时使用小于 30 秒的既有兼容兜底，保证先于 cloud 返回。
- **[与 `fb-publish-fill-deadline` 并发冲突]** → `platform-profile.ts` 与同 capability 归档串行；实现前从最新 master 建 worktree，归档按实际落地顺序处理 delta。

## Migration Plan

1. 先在 edge/cloud 匹配 worktree 完成单测、acceptance、full tests 和 typecheck。
2. edge 与 cloud 提交并推送默认分支；cloud 只从干净 `master` 走 dev 安全部署。
3. edge 默认不制作安装包；真机验收使用明确更新后的 edge 运行时。若需要桌面安装包，必须另获显式发布授权。
4. dev 用新且不重复的已授权 Facebook 草稿，在浏览闭环停留于小组/详情页的前置场景下验收：只允许导航到个人首页后打开 composer，且最终最多发布一次。
5. 回滚时 cloud 回退 `select_mode` 预算改动，edge 回退页面门与轮询；历史 `failed` 草稿不做 DB 回写。

## Open Questions

- 无阻塞问题。真机页面结构如与单测假设不同，只允许收紧/校准首页稳定信号，不得放宽为同域名或相似文案猜测。
