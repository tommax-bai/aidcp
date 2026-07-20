## ADDED Requirements

### Requirement: 外部占用拒启后的本机关闭不得触碰或假称关闭占用端

当 AdsPower `browser-profile/start` 因其他设备或窗口占用而在取得本机浏览器句柄前拒绝启动，且操作者随后关闭本机自动化时，监督器 SHALL 将该环境的本机自动化意图收敛为停止、清除本轮终态失败并取消本机排队/重试。监督器 MUST NOT 对该 profile 发送 stop、强杀或调试附着，MUST NOT 要求恢复接管外部会话后再关闭，也 MUST NOT 宣称占用端浏览器已被本机关闭。

#### Scenario: 占用终态关闭只收敛本机意图

- **GIVEN** 本轮 `browser-profile/start` 已被明确分类为外部占用拒绝，且本机从未取得浏览器句柄
- **WHEN** 操作者点击“关闭自动化”
- **THEN** 监督器 SHALL 将本机自动化意图置为停止、取消本机重试与排队并清除该轮错误
- **AND** SHALL 如实说明本机自动化已关闭、占用端会话未受影响

#### Scenario: 占用终态关闭不执行浏览器关闭确认

- **GIVEN** 本轮启动在 provider 分配本机浏览器句柄前已被外部占用拒绝
- **WHEN** 监督器执行无子进程关闭收敛
- **THEN** MUST NOT 调用本机 profile active/stop 路径来推断或关闭占用端浏览器
- **AND** MUST NOT 将外部仍 active 重新投影为“需恢复接管后再关”的本机失败

#### Scenario: 非占用异常继续诚实确认遗留浏览器

- **GIVEN** 自动化因非占用异常终止，且本机浏览器是否遗留无法从退出事实确定
- **WHEN** 操作者关闭自动化
- **THEN** 监督器 SHALL 继续执行既有本机浏览器关闭确认
- **AND** 只有取得确认后才 SHALL 宣称关闭完成，无法确认时 MUST 保留可操作失败
