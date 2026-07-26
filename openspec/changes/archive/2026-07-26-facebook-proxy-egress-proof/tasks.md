## 1. Cloud 出口回显

- [x] 1.1 在 `aidcp-cloud` Client Auth 服务实现公开只读 `/egress` route，返回规范化来源 IP、服务端时间和请求标识，并设置 CORS 与 `no-store`
  <!-- aidcp-cloud 97b4b0e + b82d707: public stateless route; the deployed nginx `$proxy_add_x_forwarded_for` chain is resolved from the rightmost valid hop so a client-supplied left prefix cannot become evidence; no database change. -->
- [x] 1.2 为转发头、socket 回退、OPTIONS/CORS、无鉴权和不可缓存行为补充聚焦测试
  <!-- aidcp-cloud b82d707: focused client-auth suite 42/42, including rightmost forwarded-hop selection. -->

## 2. Edge 浏览器出口与流量观测

- [x] 2.1 为 AdsPower Facebook CDP 会话启用 Network domain，并实现只累计 `loadingFinished.encodedDataLength` 的浏览器代际接收流量观测器
  <!-- aidcp-edge b9835d2: Network domain is opt-in for AdsPower Facebook only. -->
- [x] 2.2 经当前 page 的 CDP 网络上下文执行无凭据出口探测，同时执行 Node 直连探测，诚实生成已验证、疑似直连、待验证和无法确认状态
  <!-- aidcp-edge b9835d2: browser loadNetworkResource and Node direct evidence are compared; browser failure never falls back to verified. -->
- [x] 2.3 在浏览器新启动和冷待机唤醒时重置代际证据，在普通 CDP 重连时保持累计，并以节流结构化事件投影状态
  <!-- aidcp-edge b9835d2: cold standby invalidates evidence; wake starts a new generation; CdpClient listener survives reconnect. -->
- [x] 2.4 为状态判断、字节累计、代际重置、失败降级和敏感数据边界补充聚焦单元测试
  <!-- aidcp-edge b9835d2: proxy observer and projection tests pass. -->

## 3. Electron 运行页呈现

- [x] 3.1 将核心代理运行事件接入每环境 fleet 状态，并从 AdsPower 环境读回数据提取非密配置摘要且不传代理密码
  <!-- aidcp-edge b9835d2: fleet projection uses a strict allowlist; IP-bearing event logs are redacted before persistence. -->
- [x] 3.2 在选中 Facebook 账号顶栏增加紧凑代理状态与“本次会话接收流量”，详情分开展示配置、浏览器出口、本机出口、检测时间和统计口径
  <!-- aidcp-edge b9835d2: Facebook-only titlebar chip and evidence popover. -->
- [x] 3.3 为非 Facebook 隐藏、配置与验证分离、异常文案、字节格式化和详情脱敏补充 renderer/main 聚焦测试
  <!-- aidcp-edge b9835d2: focused renderer/fleet suite 129/129 and proxy contract tests pass. -->

## 4. 验证、集成与交付

- [x] 4.1 在 `aidcp-cloud` 和 `aidcp-edge` 分别运行聚焦测试、完整测试与 typecheck，并修复回归
  <!-- Edge: npm test 1917/1917, typecheck pass. Cloud: npm test 2602 pass, 8 gated skip, typecheck pass. -->
- [x] 4.2 更新本清单的 repo、commit SHA、验证、部署与偏差注记并通过 `openspec validate facebook-proxy-egress-proof --strict`
  <!-- Control repo validation rerun after this checklist update. No product deviation; first release intentionally has no manual/periodic recheck and no hard gate. -->
- [x] 4.3 将 Cloud/Edge 变更按规范集成并推送默认分支；不构建 Edge 安装包
  <!-- Pushed aidcp-edge master b9835d2 and aidcp-cloud master b82d707. Edge installer intentionally not built. -->
- [x] 4.4 按部署规范将 Cloud runtime 变更部署到 `dev`，验证服务、listener、health 与公网 `/capi/egress`，如失败则回滚
  <!-- Deployed aidcp-cloud b82d707 to dev on 2026-07-20 from the clean master checkout. Backup: /opt/aidcp/backups/cloud-20260720-104209-facebook-proxy-egress-proof. aidcp-cloud.service active; listeners 8787/8090/8091/5432 present; panel and client-auth health returned {ok:true}; PostgreSQL accepted connections; Feishu bot identity remained Dev.A. Public GET /capi/egress returned 200 with matching evidence headers, CORS `*`, and `no-store`; OPTIONS returned 204; a client-supplied leftmost X-Forwarded-For value was rejected in favor of nginx's nearest hop. Source hash matched local b82d707. Validation boundary: no real AdsPower/Facebook account was opened, so browser-via-proxy evidence remains covered by automated tests and will be observed when a Facebook environment next runs. -->
