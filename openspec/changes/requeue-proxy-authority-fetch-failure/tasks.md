# Tasks — requeue-proxy-authority-fetch-failure

## 1. aidcp-edge — 原因拆名与分流接线

- [x] 1.1 `readAuthoritativeProfileProxy`：HTTP 请求未送达（status 0 + error）返回独立原因 `proxy_authority_unreachable`；「未配置 base」（status 0 无 error）保持配置类
- [x] 1.2 `proxyPreflightFailureText` 加新原因文案「暂时联系不上云端，代理配置读取不到」
- [x] 1.3 `startEdge` 起核心前网络准备晚验改走 `handleProxyPreflightFailure` 分流（带 generation），移除绕过分流的直接终结
- [x] 1.4 `proxy-preflight.cjs` 不可恢复清单加「unreachable 刻意不在此列」注释（清单本身不改，未列入即可恢复）
- [x] 1.5 测试：`proxy-preflight.test.ts` 可恢复清单补 `proxy_authority_unreachable`；`proxy-preflight-requeue-contract.test.ts` 补拆名断言与晚验分流断言（含 doesNotMatch 旧直接终结）
- [x] 1.6 验证：`node --check` 两个 cjs、`npm run typecheck`、全量 `npm test` 全绿

## 2. 收尾

- [x] 2.1 edge master 提交并推送 <!-- aidcp-edge db511a2 全量 3242 测试绿 + typecheck 绿 -->
- [ ] 2.2 重打桌面安装包并装机（打包按约定须用户显式要求；装机前运营机行为不变）
- [ ] 2.3 真机验收：断网场景下环境显示「暂时联系不上云端…后重新排队重试（第 N/2 次）」而非当场异常；预算耗尽后文案为「代理重试预算耗尽」
