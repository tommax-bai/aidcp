#!/usr/bin/env bash
# SessionStart guard (companion to .git/hooks/post-checkout): warn if the
# CANONICAL aidcp checkout has drifted off `main`. Silent when on main, or when
# the canonical path is absent (other machines) so this stays safe to commit.
# Rationale + restore steps: CLAUDE.md §7 / AGENTS.md §8.
d=/Users/baitianxing/codes/aidcp
git -C "$d" rev-parse --git-dir >/dev/null 2>&1 || exit 0   # not this machine's layout -> silent
b="$(git -C "$d" branch --show-current 2>/dev/null)"
[ "$b" = "main" ] && exit 0                                  # on main -> silent
msg="WORKING-DIR DRIFT: the canonical aidcp control-repo checkout ${d} is on branch '${b}', not main. This violates the CLAUDE.md §7 canonical-checkout-stays-on-main invariant. Do control-repo change work in a worktree, not here. To restore WHEN SAFE: git -C ${d} checkout main && git -C ${d} merge --ff-only origin/main. If a concurrent session has uncommitted WIP there, coordinate first and never use -f."
# jq guarantees valid JSON escaping for the branch name and message.
jq -n --arg b "$b" --arg m "$msg" \
  '{systemMessage: ("⚠ aidcp 主 checkout 不在 main（当前分支: " + $b + "）——见 CLAUDE.md §7 铁律。"),
    hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $m}}'
