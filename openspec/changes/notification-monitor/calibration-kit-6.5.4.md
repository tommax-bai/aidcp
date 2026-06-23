Both confirmed. The `await evalRawFn<boolean>(...)` return value at line 1465 is indeed discarded, and line 1471 unconditionally reports `ok:true`. unreadNear at 1390 uses the condemned broad selector. Data is accurate. I have enough verified ground truth to synthesize.

# notification-monitor 6.5.4 上真机前校准审计

> 本报告是给你在真机驱动账号时执行的「校准包」。下列真机步骤与 CDP 探针**均未执行**，待你在活页面跑。已核对的代码事实标注 `文件:行`。

---

## 1. 现状速览（4 项校准 + CDP 断连疑点）

- **(a) 三类列表选择器** — 进入「评论和@」靠遍历 `[role=tab],[class*=tab],a,span,div` 全文匹配点击，无切换后校验、仅固定 `sleep(800)`（`aidcp-edge/src/browse/browse-session.ts:1416,1418`）；列表行选择器是三段 class 猜测并集（`browse-session.ts:1425`）；正文/用户名/笔记标题/itemKey 全是 best-effort 子选择器，正文缺失时**回退整行 textContent**（`browse-session.ts:1433,1439`）。代码自带注释「选择器待真机校准」（`browse-session.ts:1374,1400,1449`）。

- **(b) 多类型优先级** — 云端硬编码 `PRIORITY = ['comments','likes','follows']`，`counts[cat]>0 && !已处理` 时选中、**选中即记账**（`aidcp-cloud/src/agents/notification-triage.ts:18,49-56`；`session-context.ts:90-92`），保证每类至多一轮、≤3 轮收敛。但优先级的**唯一输入**是边缘 `notification.home` 快照，而快照的 `unreadNear()` 用的是被 6.5.3 否定的宽选择器（见下）。

- **(c) 看一眼是否真清未读** — `viewNotificationCategory` 点完分类 tab、`sleep(800)` 后**无条件**报 `ok:true reason:'viewed'`，从不回探红点是否真消失（`browse-session.ts:1469-1471`，已核对）。兄弟动作（点赞/收藏/评论）都做了 `state_unchanged` 后置校验（`browse-session.ts:936-943,1012-1019,1120-1127`），通知 view 是唯一例外。权威未读探针 `buildNotificationBadgeJs`（6.5.3 修正后的结构判据）存在但 view 路径从不调用（`notification-monitor.ts:29-51`）。

- **(d) 评论@发飞书质量** — 飞书唯一成形处是 `notifyComments` 闭包逐条渲染 `• {fromUser||某用户}（{@你|评论}）：{content} · 《{noteTitle}》`（`aidcp-cloud/src/server.ts:532-537`）；唯一内容过滤是 `content.trim().length>0`，无 LLM、无去噪、无长度/乱码检查（`notification-classifier.ts:43-47`）。所有内容缺陷源头在边缘抽取（`browse-session.ts:1423-1449`）。

- **CDP 断连疑点（"CDP 未连接"）** — 重连已内化进共享 `CdpClient`，有界退避后或恢复或诚实 `cdp.unrecoverable`（`aidcp-edge/src/cdp/client.ts:128-166,248-283`）。但**通知 excursion 的五个 handler 各自用宽 try/catch 吞掉一切错误**（含 `CdpDisconnectedError`），断连时上报假「无未读/空 items/viewed」而非冒泡到循环重连路径（`browse-session.ts:1401-1404,1450-1453,1472-1475`，已核对）。

---

## 2. 上真机前必须先修的 bug（仅 confirmed-real，按严重度）

### 🔴 P0 — CDP-NOTIF-1：通知 handler 吞 `CdpDisconnectedError` → 静默假「无未读/空 items」(high)
`browse-session.ts:1401-1404,1450-1453,1472-1475`。三个 handler 的顶层 catch 不区分错误类型；`CdpDisconnectedError extends Error`（`client.ts:47-50`），断连时被这里截获并上报 `notification.home{0,0,0}` / `notification.items{[]}` / `ok:true viewed`，**永远到不了循环 476-485 的重连路由**（`executeCommand` 在 try 内、但内层已吞）。这是对核心红线「MUST NOT 静默假成功」的直接违反，且让 cdp-reconnect 对整段 excursion 形同死代码。
**修**：每个 catch 首行 `if (err instanceof CdpDisconnectedError) throw err;`（import 已在 `browse-session.ts:55`），只对真业务/选择器失败发兜底；并补 `resumeAfterReconnect`（`browse-session.ts:350-360` 当前只重报 feed）发一个 `reason:'cdp_reconnect_aborted'` 的 excursion-aborted 信号，否则重连后该步无回执、云端干等。加单测：注入 send 必 reject `CdpDisconnectedError`，断言不发假回执且 await 重连。

### 🔴 P0 — NB-1：`unreadNear` 重用 6.5.3 刚删的假阳性选择器 → 永久伪造每类未读 (medium)
`browse-session.ts:1390`（已核对）。`[class*="badge"],[class*="dot"],[class*="count"],[class*="red"]` 正是 6.5.3 在 `notification-monitor.ts:23-24` 点名否定的宽模式——小红书=「RED」、设计系统类名前缀 `reds-`，`[class*="red"]` 命中常驻 `reds-icon`、`[class*="badge"]` 命中常驻 `badge-container`；命中后 `isNaN(n)?1:n`（行 1391）把任何无数字命中变成「未读 1」。**这里没有 svg-skip、没有 reds-icon 排除、没有可见性闸**——比已修的入口探针更裸。这快照是 triage 优先级的唯一输入（`notification-triage.ts:41-55` 直接吃 `counts[cat]>0`），phantom 计数 → 无谓进各子分类、优先级无意义、且上报了不存在的未读 = 伪造状态。
**这正是 6.5.3 reds-/badge 假阳性的原样复发，只是搬到了首页 per-tab 探针、6.5.3 没扫到。**
**修**：从 `notification-monitor.ts` 导出一个共享结构判据 `realBadge(container)`（svg-skip + `/reds-icon/` 排除 + 可见性），两处复用，杜绝再漂移；真机 DOM 校准前宁可返回 0（诚实无未读）也不靠 class 猜 1。

### 🔴 P0 — NB-2：标签门在整页 `a/span/div` 首个文本命中即返回 → 从无关元素读 badge (high)
`browse-session.ts:1386-1391`。`unreadNear` 全文档扫 `[role=tab],[class*=tab],a,span,div`、对第一个短文本命中且**含 badge 后代**的元素返回。`赞/收藏/关注/评论` 在页面 chrome（点赞/收藏/关注按钮、侧栏导航）里高频出现，命中的可能根本不是通知 tab；叠加 NB-1 的宽 badge 选择器，命中的 `reds-` 图标返回 1。与 NB-1 同根，建议**一起修**：先锚定真实通知分类 tab 容器（真机 DOM dump 后确定 `role=tablist`/稳定 `[class*=tab]`），只扫这些节点、标签匹配只看 tab 自身短文本，再套 NB-1 的结构 badge 判据。

### 🟠 P1 — NM-C-1：`viewNotificationCategory` 没点到 tab 也报 `ok:true viewed`（no_target 被掩盖）(high)
`browse-session.ts:1465-1471`（已核对）。`await evalRawFn<boolean>(...)` 的返回值被丢弃；in-page 函数无命中时干净返回 `false`，`evalRaw` 只在 in-page 异常时抛（`cdp-util.ts:74-84`），故 `false` 到不了 catch，行 1471 无条件报 viewed。选择器漂移/页面未渲染/单合并 tab → 空点击却报成功 = 静默假成功，且掩盖了 6.5.4 本要暴露的选择器漂移。
**修**：`const clicked = await evalRawFn<boolean>(...)`；`if(!clicked){ report ok:false reason:'no_target'; return; }`。云端 `excursion-resumer.ts:42-46` 已是 `ok:false` 的幂等消费者，安全。

### 🟠 P1 — CDP-NOTIF-2：`cdp.unrecoverable` 后通知 watcher 仍轮询死 client（僵尸定时器）(high)
`browse-session.ts:333-335`；`main.ts:299-312,321`；`background-watcher.ts:101-108`。只有 BrowseSession 订阅 `cdp.unrecoverable`，`WatcherSupervisor.stopAll` 仅在 SIGINT 调（`main.ts:321`）。session 诚实停了，watcher 仍每 `pollMs` 打 `[notification] 探测失败(保持上一状态)` 直到永远。
**修**：`main.ts` 里把 `WatcherSupervisor` 订阅到 `cdp.unrecoverable→stopAll()`、`cdp.reconnected→startAll()`（恢复的 session 否则盲跑）。

### 🟡 P2 — NCQ-1：正文回退整行 textContent → 飞书收到拼接 blob (medium)
`browse-session.ts:1439`（`(contentEl||txt)`，txt=整行）→ `server.ts:534` 逐字渲染。正文子选择器在 `reds-` 命名下漏掉时，飞书显示「用户名+时间+回复/赞标签+标题」糊成一条，云端唯一过滤（非空）拦不住。
**修**：边缘正文缺失时设 `content=''`（云端非空过滤会丢弃），**绝不**回退整行；云端加防御性过滤（`content===fromUser` 或含 `回复/赞了/关注了` 即拒）。校准正文选择器为 6.5.4(a) 一部分。

### 🟡 P2 — NCQ-3：itemKey 缺失时去重键含相对时间 → 重复飞书 (medium)
`notification-deduper.ts:20`（`it.itemKey || ${fromUser}|${content}`）。`itemKey` 为 `undefined`（无 `a[href]`）时回退用含「N分钟前」的 blob 内容，跨 excursion 时间漂移 → 同条评论键变化 → 重复通知。
**修**：云端回退键先归一化剥时间 token（`刚刚|\d+(秒|分钟|小时|天)前|昨天|今天` 等）再拼；边缘尽量取稳定 permalink 做 itemKey。

### 🟡 P2 — NB-5：itemKey 取首个 `a[href]`（常是 per-user profile 链）→ 同人多评论被折叠静默丢 (medium)
`browse-session.ts:1435,1441` + `notification-deduper.ts:18-20`。truthy 但非 per-comment 唯一的 key 比 `undefined` 更坏（短路掉 `fromUser|content` 回退）。
**修**：边缘排除 `/user/profile/` href、优先 per-comment permalink，否则用 `hash(fromUser+content+noteTitle)`；云端去重键**始终**纳入 content（`${itemKey||''}|${fromUser}|hash(content)`）做纵深防御。

### 🟡 P2 — NM-C-3：首页 per-category 计数同样用宽选择器 (medium)
`browse-session.ts:1390` — 与 NB-1 同一行同一根因（`isNaN→1` phantom），随 NB-1 一并修。6.5.2 真机日志「评论1/赞1/关注1」三类全 1 正是 `isNaN→1` 兜底签名，值得真机复核。

### 🟡 P2 — NCQ-2：`.slice(0,200)` 按 UTF-16 截断可劈裂 emoji 代理对 → 飞书乱码尾 (medium)
`browse-session.ts:1439`（及 fromUser .slice(0,40)、noteTitle .slice(0,40)）。落界 emoji 留半个代理 → U+FFFD；无省略号、无截断提示。
**修**：CDP 注入 JS 内用 code-point 安全截断 `Array.from(s).slice(0,n).join('')` 并在截断时补 `…`，三字段同理。

> **被驳回、勿改**：NB-1（去重并集重复行，querySelectorAll 逗号并集本就去重）、NB-3（kind 误判——`/@\s*(我|你)/` 不匹配 `@张三`，且 kind 下游无消费）、NM-C-2（看一眼不回探——epoch 水位 + sticky 状态 + transition-only 已防震荡，非红线违反，回探仅是可选保真）、NB-ORDER-2/3、NCQ-4、CDP-NOTIF-3（navigateBack 无 try/catch、断连会冒泡到循环重连）。

---

## 3. 真机校准清单（你驱动账号时逐条跑）

**(a) 三类列表选择器**
1. 清空型账号（全部已读）→ 进通知首页 → 逐字跑探针 P-1，确认 `unreadNear` 三类是否仍非零（非零=NB-1/NB-2 现场坐实）。
2. 进入「评论和@」后跑 P-3，确认 active tab 文本 === `评论和@`（验证 tab 真切换、非默认 tab）。
3. 跑 P-2，看三段容器选择器各自命中数、并集 vs 去重数、首行 outerHTML 链——据此定真实行选择器。
4. 跑 P-2b 拿一条真实评论行 outerHTML + 各子选择器解析值——定 fromUser/content/noteTitle/itemKey 真选择器。

**(b) 优先级**
5. 给账号种入「评论+赞+关注」各 ≥1 未读 → 触发 excursion → ECS 上 `journalctl -u aidcp-cloud -f | grep -E '选中分类|分诊完成'` 确认顺序严格 comments→likes→follows，且每轮前有新 `notification.home.arrived`。
6. 单 epoch 内确认 `category_selected` ≤3 条后 `triage_done`（>3 = processedCategories 失效）。

**(c) 看一眼是否真清未读**
7. 已知有未读赞/关注时：进分类前跑 P-4（结构探针）记 `unread:true`，按 `viewNotificationCategory` 同样动作点击，再于 +0.5s/+1s/+2s/+3s 重跑 P-4，记录红点何时翻 false——**若点击单独从不清红点**，则「看一眼清未读」假设破产，须找别的清除触发（列表滚动/真看 item/导航）。
8. excursion 结束 `back_home` 后看 monitor 是否立即重燃（同 epoch 已记账不会重挑，但下一**探测周期**可能对仍亮的红点重触发 excursion——盯 `excursion.requested` 是否跨 epoch 背靠背）。

**(d) 评论@发飞书质量**
9. 真实评论/@落地后逐条肉眼检查飞书 bullet：`：` 后只能是评论正文，**不得**含重复用户名/`回复·赞`标签/相对时间/标题重复（出现=NCQ-1 触发）。
10. `（...）`内昵称为真实昵称、非「某用户」（否则 fromUser 选择器漏）。
11. 《标题》对应正确笔记或缺省，**绝不可挂错标题**。
12. 连跑两次 excursion（中间无新评论），第二次须静默（all_seen，无飞书）——重复=NB-5/NCQ-3。
13. 发一条 >200 字含落界 emoji 的测试评论，确认飞书尾部无 `?`/口字乱码、最好有省略号。
14. 若账号有官方/系统通知，确认它们不被当评论转发。

**CDP 断连**
15. excursion 进行中（entry leg）从另一 shell `lsof -ti :9222 | xargs kill -STOP`、~3s 后 `-CONT` 强制 ws close。期望-正确=`命令执行中 CDP 断连，等待有界重连` + `cdp.reconnected`；**当前-buggy**=`notification.open 失败（上报全 0…）` / `browse_comments 失败（上报空 items…）` 且**无重连日志**（坐实 CDP-NOTIF-1）。
16. 无 excursion（仅后台轮询）时同样断一下，期望几行 `探测失败(保持上一状态)` 后静默恢复（正向用例）。
17. 彻底关掉 RED tab、等 >90s/超 maxAttempts，期望 `CDP 重连不可恢复，停止浏览循环`；**bug 信号**=该行后 `探测失败(保持上一状态)` 仍每 ~1s 打不停（坐实 CDP-NOTIF-2 僵尸）。

---

## 4. 活页面 CDP 探针（粘贴到通知页 DevTools）

**P-1 — 复跑生产 homeJs，看 `notification.home` 真上报什么（NB-1/NB-2 假阳性证据）**
```js
(function(){function unreadNear(labelRe){var els=Array.from(document.querySelectorAll('[role="tab"], [class*="tab"], a, span, div'));for(var i=0;i<els.length;i++){var t=(els[i].textContent||'').trim();if(t.length>10||!labelRe.test(t))continue;var badge=els[i].querySelector('[class*="badge"],[class*="dot"],[class*="count"],[class*="red"]');if(badge){var n=parseInt((badge.textContent||'').replace(/[^0-9]/g,''),10);return JSON.stringify({hit:(els[i].tagName+'.'+((els[i].className||'')+'')).slice(0,40),label:t,badgeText:(badge.textContent||'').trim(),badgeVisible:(badge.offsetParent!==null),n:isNaN(n)?1:n});}}return JSON.stringify({hit:null,n:0});}return JSON.stringify({comments:unreadNear(/评论|@/),likes:unreadNear(/赞|收藏/),follows:unreadNear(/关注|粉丝/)});})()
```
看点：清空账号下任一类非 0 = NB-1 现场；`hit` 字段若是非-tab 元素（如点赞按钮）= NB-2 现场；`badgeText` 空但 n=1 = `isNaN→1` 伪造。

**P-2 — Dump 三段容器选择器命中/去重/容器链 + 一条样本行（定真行选择器，NB-1并集 + NCQ-1/NB-5 源头）**
```js
(function(){var sels=['[class*="notification"] [class*="item"]','[class*="comment"] [class*="item"]','[class*="tabs-content"] [class*="container"] > div'];var per=sels.map(function(s){return{sel:s,n:document.querySelectorAll(s).length};});var u=[];sels.forEach(function(s){u=u.concat(Array.from(document.querySelectorAll(s)));});var uniq=new Set(u);var it=u[0];function chain(e){var c=[];for(var n=e;n&&c.length<6;n=n.parentElement){c.push(n.tagName.toLowerCase()+(n.className?('.'+String(n.className).trim().replace(/\s+/g,'.')):''));}return c;}return JSON.stringify({per:per,unionLen:u.length,uniqueLen:uniq.size,sampleChain:it?chain(it):null,sampleHTML:it?it.outerHTML.slice(0,1500):null,sampleFullText:it?(it.textContent||'').trim().slice(0,300):null},null,2);})()
```
看点：union>unique 提示嵌套并集过捕；`sampleHTML` 给你真实 class 前缀（多半 `reds-`）；`sampleFullText` 就是 NCQ-1 回退会发给飞书的 blob。

**P-2b — 一条样本行各子选择器解析值（定 fromUser/content/noteTitle/itemKey）**
```js
(function(){var it=document.querySelector('[class*="notification"] [class*="item"], [class*="comment"] [class*="item"], [class*="tabs-content"] [class*="container"] > div');if(!it)return JSON.stringify({error:'no_row'});function tx(s){var e=it.querySelector(s);return e?(e.textContent||'').trim().slice(0,60):null;}var a=it.querySelector('a[href*="/user/profile/"]');var fa=it.querySelector('a[href]');return JSON.stringify({userEl_name:tx('[class*="name"]'),userEl_user:tx('[class*="user"]'),profileLink:a?{text:(a.textContent||'').trim().slice(0,40),href:a.getAttribute('href')}:null,contentEl:tx('[class*="content"], [class*="comment"], p'),noteEl:tx('[class*="note"] [class*="title"], [class*="extract"]'),firstHref:fa?fa.getAttribute('href'):null},null,2);})()
```
看点：`contentEl===null` → NCQ-1 必触发；`firstHref` 若是 `/user/profile/` → NB-5 必触发；`contentEl` 是否只含正文（非整行）。

**P-3 — 真实 tab 标签 + active 态（验证 tab 切换 + 优先级，NB-2）**
```js
(function(){var tabs=Array.from(document.querySelectorAll('[role="tab"],[class*="tab"]')).filter(function(e){var t=(e.textContent||'').trim();return t.length<=8&&t.length>0;});return JSON.stringify(tabs.map(function(e){return{text:(e.textContent||'').trim(),cls:String(e.className),role:e.getAttribute('role'),active:/active|selected|current/i.test(String(e.className))||e.getAttribute('aria-selected')==='true'};}),null,2);})()
```
看点：是否存在 `role=tablist/tab` 稳定容器供锚定；点击后哪个 `active:true`。

**P-4 — 结构未读探针（看一眼前后各跑一次，验证清未读，item c）**
```js
(function(){var entry=document.querySelector('a[href*="/notification"]')||document.querySelector('a[href*="/notice"]');if(!entry)return JSON.stringify({error:'no_entry'});var c=entry.querySelector('[class*="badge"]');if(!c)return JSON.stringify({unread:false,reason:'no_container'});var all=c.querySelectorAll('*');for(var i=0;i<all.length;i++){var el=all[i];if(el.closest&&el.closest('svg'))continue;var cls='';try{cls=String(el.className&&el.className.baseVal!=null?el.className.baseVal:(el.className||''));}catch(e){}if(/reds-icon/.test(cls))continue;var vis=el.offsetParent!==null||(el.getClientRects&&el.getClientRects().length>0);if(!vis)continue;var t=(el.textContent||'').trim();var n=parseInt(t.replace(/[^0-9]/g,''),10);return JSON.stringify({unread:true,count:isNaN(n)?0:n});}return JSON.stringify({unread:false,count:0});})()
```
看点：点击分类 tab 后此探针是否 `unread:true→false`；若永不翻 = item c 假设破产。这也是修 NB-1/NM-C-3 后 `unreadNear` 应改用的判据预览。

**P-5 — 同 tab 同时跑宽 vs 结构判据，直接对比 phantom（NB-1/NM-C-3 修前验证）**
```js
(function(){function pick(re){var els=Array.from(document.querySelectorAll('[role="tab"], [class*="tab"], a, span, div'));for(var i=0;i<els.length;i++){var t=(els[i].textContent||'').trim();if(t.length>10||!re.test(t))continue;var el=els[i];var broad=el.querySelector('[class*="badge"],[class*="dot"],[class*="count"],[class*="red"]');var structural=null;var cand=el.querySelectorAll('*');for(var j=0;j<cand.length;j++){var x=cand[j];if(x.closest&&x.closest('svg'))continue;var cl='';try{cl=String(x.className&&x.className.baseVal!=null?x.className.baseVal:(x.className||''));}catch(e){}if(/reds-icon/.test(cl))continue;var v=x.offsetParent!==null||(x.getClientRects&&x.getClientRects().length>0);if(v&&(x.textContent||'').trim()&&x!==el){structural=(x.textContent||'').trim();break;}}return{label:t,broadHit:!!broad,broadText:broad?(broad.textContent||'').trim():null,structural:structural};}return null;}return JSON.stringify({comments:pick(/评论|@/),likes:pick(/赞|收藏/),follows:pick(/关注|粉丝/)},null,2);})()
```
看点：`broadHit:true` 但 `structural:null` = 当前宽选择器假阳性、结构判据正确判无未读，直接证明 NB-1 修法有效。

> 飞书内容无 CDP 探针；对照标准消息形（`server.ts:532-537`）：好=`• 阿强（评论）：这条笔记好实用 · 《周末徒步装备清单》`；坏（NCQ-1）=`• 阿强（评论）：阿强 关注 这条笔记好实用回复赞3分钟前周末徒步装备清单`。ECS 日志定位：`journalctl -u aidcp-cloud -f | grep -E 'notification_(classifier|deduper|notifier)'`。

---

## 5. 判 6.5.4 可勾的退出条件

全部满足才标 `[x]`：

1. **(a) 选择器**：P-2/P-2b 在真机确定了真实行容器 + fromUser/content/noteTitle/itemKey 选择器，代码已据此替换三段猜测并集；P-3 确认进入「评论和@」后 active tab 文本 === `评论和@`。
2. **(b) 优先级**：种入三类未读跑通 excursion，云端日志确认顺序严格 comments→likes→follows，单 epoch `category_selected` ≤3 后 `triage_done`，每轮前有新 `notification.home.arrived`。
3. **(c) 清未读**：P-4 在真机确认「点击分类 tab 后入口红点确实翻 false」；若否，已找到真正清除触发并接入，且 `viewNotificationCategory` 不再无条件报 viewed。
4. **(d) 飞书质量**：真机 ≥3 条评论/@的飞书 bullet 经肉眼核验——正文干净（无 blob）、昵称真实、标题正确或缺省、连跑两次第二次静默、长评论+emoji 无乱码。
5. **NB-1/NB-2/NM-C-3 已修并回归**：`unreadNear` 改用共享结构判据（svg-skip + reds-icon 排除 + 可见性 + 锚定真实 tab），清空账号下 P-1/P-5 返回全 0；新增 jsdom 回归用例**用真实选择器**跑（持久 `reds-icon`→0、注入数字/红点 badge→count/0），而非 mock 探针结果（6.5.3 正是被 mock 蒙混过去的）。
6. **NM-C-1 已修**：捕获 `clicked` 布尔，未命中报 `ok:false reason:'no_target'`，回归断言不命中 DOM 不再产 `ok:true`。
7. **CDP-NOTIF-1 已修**：三 handler 的 catch 对 `CdpDisconnectedError` 重抛 + 补 excursion-aborted 信号；真机步骤 15 观察到断连时出现 `等待有界重连` 而非假全 0/空 items；新增「handler 内注入 CdpDisconnectedError」单测。
8. **CDP-NOTIF-2 已修**：`WatcherSupervisor` 订阅 `cdp.unrecoverable→stopAll`/`cdp.reconnected→startAll`；真机步骤 17 确认 unrecoverable 后 watcher 不再刷 `探测失败`。
9. **NCQ-1/2/3、NB-5 已修**：正文缺失发空（不发 blob）+ 云端防御过滤；code-point 安全截断 + 省略号；去重键归一化剥时间 + content 始终纳入键 + itemKey 排除 profile 链；各配单测。
10. `cd ../aidcp-edge && npm test && npm run test:acceptance && npm run typecheck` 与 cloud 同三件套全绿（含 `AC-PROTO-*` 两份 protocol.ts 不漂移）。

> **说人话总结**：这是给你上真机前的「先别急着信、先验再修」清单。最要命的两件事——一是**通知页一断网就假报"没有未读/没有消息"还绕过自动重连**（红线级，必须先修），二是**6.5.3 修掉的那个"把品牌红图标误当未读红点"的老毛病，原样又藏在通知首页的三类计数里**（会让系统没未读也乱跳通知页、优先级全是假的）。另有"点一下就算清了未读但其实没验证""飞书里把整行文字糊成一团"等若干内容质量问题。我已把每个真 bug 的确切位置和改法、以及你能直接粘到浏览器跑的探针都列好；按清单跑完真机、确认并修完 7 类问题、测试全绿，6.5.4 才能勾掉。