## ADDED Requirements

### Requirement: Provider-neutral DevTools handles SHALL terminate at Native for Xiaohongshu

For an admitted Xiaohongshu executor, the selected browser provider SHALL continue to own browser startup, readiness, stop, and confirmed-dead semantics and SHALL expose only its loopback DevTools host/port through the unified handle. Edge SHALL pass that handle to Native, and Native SHALL own all downstream Xiaohongshu target discovery and CDP page operations without branching on provider kind.

#### Scenario: AdsPower supplies a dynamic port
- **WHEN** the AdsPower provider returns a ready dynamic DevTools port for the admitted profile
- **THEN** Edge passes the loopback handle to Native and Native uses its common target/CDP path

#### Scenario: Self provider supplies a port
- **WHEN** the self provider returns its ready DevTools handle
- **THEN** Native uses the same Xiaohongshu target/CDP path without provider-specific page rules

### Requirement: Browser and Native recovery ownership MUST remain distinct

Native MAY reconnect its page CDP WebSocket and refresh targets while the provider's DevTools endpoint remains healthy. If the endpoint itself is unhealthy or browser lifecycle action is required, Native SHALL report that condition to Edge; Edge/provider remain the only browser lifecycle writers. Native MUST NOT start, stop, or kill provider processes.

#### Scenario: Page WebSocket closes but endpoint is alive
- **WHEN** the selected page connection closes and the provider endpoint still answers
- **THEN** Native performs bounded target refresh/reconnect without asking the provider to restart the browser

#### Scenario: Provider endpoint is dead
- **WHEN** Native cannot reach the admitted loopback DevTools endpoint
- **THEN** it returns an executor-health failure to Edge and does not call AdsPower/self lifecycle APIs directly
