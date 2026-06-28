# Tasks — weekly-active-window

## 1. 安全限额层：类型 + 纯函数 + 提供者口（aidcp-cloud `risk/session-limits.ts`）
- [x] 1.1 常量 `WEEK_ACTIVE_MASK_LEN=168`；纯函数 `isValidWeekActiveMask`（168 长 0/1）、`mondayBasedDayIndex`（周一=0…周日=6）、`isWeekActiveAt(mask, Date)`（缺/非法→true 全天活跃）
- [x] 1.2 `SessionLimitProvider` 接口加 `weekActiveMask(): string | null`

## 2. 全局配置存储（`config/session-config-store.ts` + migration）
- [x] 2.1 `SessionConfigRow` / `SessionConfigPatch` 加 `activeWeekMask`
- [x] 2.2 建表 SQL + 自愈 ALTER 加列 `active_week_mask TEXT`；reload SELECT / rowFromDb / upsert(INSERT…ON CONFLICT…RETURNING) 全带新列
- [x] 2.3 提供者口 `weekActiveMask()`：缺行 / 非法 → null（回落全天活跃）
- [x] 2.4 `migrations/0024_weekly_active_window.sql`（幂等 ADD COLUMN IF NOT EXISTS，与 store 自愈同源）

## 3. 面板外观 + 契约 + 接口（facade / panel）
- [x] 3.1 `session-config-facade.ts`：buildView 回显 `activeWeekMask`；set 校验（传则必须 168 长 0/1，非法整块拒；仅传掩码也算有效字段）
- [x] 3.2 `panel/types.ts`：`SessionLimitView` + `SessionLimitPatchInput` 加 `activeWeekMask`
- [x] 3.3 `panel/panel-server.ts`：PUT /api/session-limits 解析字符串字段（非 string→400），余校验在 facade

## 4. 三处闸（`role-dispatcher.ts` + `session-monitor-role.ts`）
- [x] 4.1 调度器私有口 `isWithinActiveWeek(now)`（读提供者掩码 + 纯函数）
- [x] 4.2 启动收口：`restartSession()` 顶部加闸（统一覆盖 边端 hello / 绑人设自启 / 续场 / 面板手动）
- [x] 4.3 续场闸：`canAutoResume()` 加「可活跃时间」一道（与日窗口 / 每日上限 / 风控并列）
- [x] 4.4 运行中跨入即结束：监测体加 `getActiveWindowOpen?` 注入口，`checkSession` 现读（巡视暂停期不打断）；调度器注入 `() => isWithinActiveWeek(clock())`
- [x] 4.5 **窗口唤醒**：纯函数 `msUntilNextActive`（下一活跃整点毫秒；缺/非法/已活跃/全休眠→null）；调度器 `wakeTimer`+`armWakeTimerIfWindowed`（叠1min抖动、与续场同特性闸）+`onWakeElapsed`（账号/活跃二次校验→doAutoResume）；接入 restartSession 被拦处、doAutoResume 拒签处；start/restart/endSession 清计时器

## 5. 管理后台「安全」页（aidcp-console）
- [x] 5.1 `types/api.ts`：`SessionLimitView.activeWeekMask` 手动对齐
- [x] 5.2 `QuotasPage.tsx`：新卡片「可活跃时间（全局）」+ 只读预览网格 + 来源/活跃小时数
- [x] 5.3 编辑弹窗：7×24 网格点选（格/天/列）+ 预设（全活跃/全休眠/工作时间/反选）+ 保存（PUT /api/session-limits）+ 热加载提示

## 6. 测试
- [x] 6.1 纯函数单测（掩码合法性 / 周一起头索引 / 按格查 / 缺失非法回落全天活跃）`test/weekly-active-window.test.ts`
- [x] 6.2 store 取值 / 写 / 部分写保持 / 脏掩码回落 null（修既有 fakePool 位序陈旧致 updated_by 错位的红用例）
- [x] 6.3 facade 校验（合法落库 / 非法整块拒 / 仅传掩码非 no_valid_fields）
- [x] 6.4 调度器闸（全休眠不开/不续、全活跃正常、缺掩码零回归）+ 既有 SessionLimitProvider 桩补字段
- [x] 6.4b 窗口唤醒：`msUntilNextActive` 纯函数（缺/非法/已活跃/全休眠→null、本日稍后、跨天）+ 调度器（窗口外排唤醒计时器→到点窗口开主动起会话 / 全休眠不排）
- [x] 6.5 cloud `typecheck` 全树 0 错；console `typecheck` + `vitest` 绿

## 7. 部署 + 真机（待用户放行生产 SSH）
- [ ] 7.1 部署 ECS：committed-only（git archive）绕开同机并发 WIP；备份 → tar-over-ssh 覆盖 src → restart → healthcheck；自愈 ALTER 补列、`\d session_config_global` 实测 active_week_mask 在
- [ ] 7.2 控制台 dist 覆盖（备份 console.bak.*，免重启）
- [ ] 7.3 真机标定：配一段窄窗口，验「窗外不开/不续、运行中跨入即结束、窗内正常」，回写本 tasks
