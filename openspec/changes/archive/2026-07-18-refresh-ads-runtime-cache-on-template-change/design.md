## Context

Ads CLI 会把 `start` 子命令转成独立 daemon。当前 Edge 只保存 Local API base，不保存运行时生命周期句柄；真正退出时只等待各环境核心进程完成浏览器清理，因此 daemon 会跨 Edge 进程存活并被下次启动接管。

运行时模板在打包态从 `Resources/adspower-browser` 复制到用户可写目录；开发态则可能直接复用此前留下的用户目录副本。现有 `stage.json` 只有 Edge 版本与 Ads CLI 包版本，不能识别同版本兼容补丁变化。Windows 下旧 daemon 又可能占用待替换目录，因此刷新必须与 daemon 停止按顺序编排。

## Goals / Non-Goals

**Goals:**

- 同一 Ads CLI 包版本内的模板内容变化也能可靠失效用户目录副本。
- 开发态始终以当前 `build/ads-runtime` 为模板来源，不被历史副本遮蔽。
- 刷新前有界停止旧 daemon，替换失败时保留可恢复的旧副本并诚实报错。
- Edge 真正退出时停止本进程已接管/启动的 Ads CLI daemon；托盘常驻不触发停止。

**Non-Goals:**

- 不改变浏览器 profile、内核与 `~/.adspowerCli` 用户数据。
- 不引入 AdsPower 桌面端，也不改变 Ads CLI → SunBrowser 的运行链路。
- 不在本 change 改变各环境核心已有的浏览器停机语义。

## Decisions

1. **构建期生成模板内容身份，运行期只读取身份。** `stage-ads-runtime.mjs` 在所有兼容补丁完成后，对模板文件路径与内容做稳定 SHA-256，并写入模板清单。相比仅手工维护 patch 版本，这能避免漏增版本；相比每次启动遍历整棵运行时，打包态启动没有额外大目录哈希成本。为迁移既有开发态模板，清单缺失时允许运行期计算一次同算法身份。

2. **开发态也走用户目录暂存，但模板源改为当前 build 输出。** 这样既避免 daemon 锁住 `node_modules` / build 依赖树，又保证当前兼容补丁优先。打包态仍以 `Resources/adspower-browser` 为模板源。

3. **先复制候选副本，再停止 daemon，再交换目录。** 大文件复制不影响当前服务；候选完整后才执行有界 `ads stop`，然后在同一父目录用 rename 交换。若交换失败，回滚旧目录并返回失败，MUST NOT 静默继续使用版本身份不符的副本。

4. **保存本次已管理运行时的 CLI entry 与执行体。** `ensureRuntime` 成功后记录会话；`before-quit` 无论是否仍有环境核心，都统一进入有界退出流程：先停环境核心并等待其浏览器清理，再执行 Ads CLI `stop`，最后放行 Electron 退出。窗口关闭到托盘不触发 `before-quit`，保持现状。

5. **崩溃遗留允许接管，但内容不一致时必须先换新。** 正常同内容启动可接管仍在运行的 daemon；内容身份变化时，暂存编排先停旧 daemon 并换新，再由 `ensureRuntime` 启动当前模板。

## Risks / Trade-offs

- [Windows 文件占用导致目录交换失败] → 先执行有界 `ads stop`，交换使用备份目录；失败回滚并明确阻断启动。
- [真正退出耗时增加] → daemon 停止采用短时有界轮询；超时落日志后仍保证 Electron 有界退出，不无限挂起。
- [开发态旧模板没有内容清单] → 运行期仅在清单缺失时计算目录身份；下一次标准 staging 会生成清单。
- [异常崩溃无法执行 stop] → 下次启动可接管同内容 daemon，或在模板变化时先停止再替换。

## Migration Plan

首次运行新代码时，旧 `stage.json` 缺少模板内容身份，因此必定进入刷新：复制当前模板、停止旧 daemon、交换用户目录副本并写新 stamp。回滚到旧版本时，旧代码仍能读取同一用户目录；其旧 stamp 比较会触发一次旧模板重拷贝。

## Open Questions

无。
