"""orchestra Claude Code hook handlers (LLD-012 §Hook architecture).

Three handlers emit JSON consumed by Claude Code:
- session_start_inject: SessionStart event — emits TLDR + structured violations
- pre_compact_instruct: PreCompact event — emits compact_instructions preserving TLDR
- user_prompt_reinject: UserPromptSubmit event — Nth-turn TLDR re-injection

All output uses hookSpecificOutput.additionalContext with [ORCHESTRA TLDR]
prefix marker (literal opening line, before the <system-reminder> wrap)
for cross-plugin disambiguation per LLD-012 §Edge Cases.
"""
