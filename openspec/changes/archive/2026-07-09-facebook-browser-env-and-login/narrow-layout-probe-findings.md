# Facebook Narrow Layout Probe Findings

Date: 2026-07-06

Probe environment:

- AdsPower profile: `k1ebny3j`
- State: logged-in candidate after manual challenge handling
- Probe artifacts: `/tmp/aidcp-fb-narrow-layout-probe-2026-07-06T07-05-14-770Z`
- Viewports:
  - `430x932`
  - `768x900`
- Probe mode: DOM inspection plus Page permalink focus/type/clear; no submit

No comments were submitted. No credentials, cookies, tokens, storage values, user names, search result text, or post body text were saved.

## Summary

The narrow layout probe did not invalidate the first implementation strategy.

Across both narrow viewports:

- login/challenge classification remained clean:
  - no `/login/`
  - no `/checkpoint/`
  - no `/two_step_verification/`
  - no `fbsbx.com/captcha`
  - no `google.com/recaptcha`
  - no email/password login form
- Page permalink editor remained available as `contenteditable` textbox.
- Page permalink focus/type/clear passed without submitting.
- URL-first Group entry, Group post, Group search, and search-result post access remained usable.
- Group pages/posts still showed `加入` / `加入小组`, so Group comment submit remains blocked by membership/permission gating.

## Page Permalink Editor

Target:

```text
https://www.facebook.com/Meta/posts/meta-ai-is-built-into-all-our-apps-and-new-tech-meta-leads-the-way-on-social-and/833823022640243/
```

Both viewports produced:

- one visible editor
- `contenteditable="true"`
- `role="textbox"`
- comment controls including `发表评论`
- post-submit control appearing after typing: `发布评论`
- marker accepted by the controlled editor
- keyboard clear left the editor empty

This confirms the Page permalink editor locator can be designed around semantic attributes rather than desktop-only geometry.

## Group and Search

The following URL-first flows worked at both `430x932` and `768x900`:

```text
https://www.facebook.com/groups/facepagerusers
https://www.facebook.com/groups/facepagerusers/posts/1038125326805326/
https://www.facebook.com/groups/facepagerusers/search/?q=links
https://www.facebook.com/groups/facepagerusers/posts/1399888000629055/
```

Observed stable signals:

- Group landing exposed `加入小组` and `在小组内搜索`.
- Group post exposed one visible editor-like textbox plus `加入`.
- Group search exposed result articles and post permalink samples.
- Search-result post permalink opened directly.

Membership caveat:

- `加入` / `加入小组` appeared in narrow layouts too.
- `已加入` and `待批准` were not observed in this profile.
- Group submit must remain disabled until membership classifier proves the account can interact.

## Layout Implications

The first implementation should avoid desktop geometry assumptions:

- Do not depend on fixed x/y positions.
- Do not require the wide top nav to exist.
- Prefer direct URLs for search and permalink access.
- Locate comment editors by `role`, `contenteditable`, and comment-like aria labels.
- Locate Group search by direct route first, not by clicking the visible search box.
- Treat visible editor-like Group textboxes as insufficient without membership permission.

## Remaining Narrow Risks

The narrow probe used desktop user-agent behavior with device metrics override. It did not test `m.facebook.com` or a mobile user-agent surface. That is acceptable for the first AdsPower desktop implementation if startup pins a desktop browser/UA.

If future runtime allows mobile UA or opens `m.facebook.com`, a separate mobile-surface probe is required.
