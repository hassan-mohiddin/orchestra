# Runbook: [Alert / Symptom / Operational Task]

> **Doc ID:** RUNBOOK-kebab-name
> **Date:** YYYY-MM-DD (last updated)
> **DRI:** [Owning team or on-call rotation]
> **Status:** Current | Outdated | Deprecated
> **Severity:** What page priority does this runbook handle? P1 | P2 | P3

Runbook for an operational scenario. Written for the on-call engineer at 3am — assume tired, rushed, low context. Lead with the action, not the explanation.

## When This Fires

Specific trigger condition. Alert name, log signature, customer report shape.

- **Alert:** [Exact alert name in the monitoring system]
- **Symptom:** [What the user / on-call observes]
- **Page priority:** [P1 / P2 / P3]

## Quick Reference

One-line summary of what to do. The 3am-friendly version.

> **TL;DR:** [Action — e.g. "Check `<dashboard-url>`, if queue depth > 10000, scale workers via `<command>`. If not, escalate to <team>."]

## Diagnosis

Step-by-step. Each step has a command or link.

1. **Check [specific dashboard / log query]:**

   ```bash
   <command>
   ```

   Expected output: [what healthy looks like]
   If output shows X → go to Mitigation step 1
   If output shows Y → go to Mitigation step 2
   If unclear → go to Escalation

2. **Check [next signal]:**

   ```bash
   <command>
   ```

3. [Continue until root cause is identified]

## Mitigation

Ordered by safety / blast radius — try least risky first.

### Step 1 — [Lowest-risk mitigation]

```bash
<exact command>
```

Verify recovery: [how to confirm it worked — specific signal]

### Step 2 — [Next mitigation if step 1 fails]

```bash
<exact command>
```

### Step 3 — [Last-resort mitigation]

[Describe + warnings — e.g. "This drops in-flight requests. Only run if step 1 + 2 failed and customer impact > 5min."]

## Verification

How do you confirm the incident is over?

- [ ] Alert clears in monitoring
- [ ] Error rate returns to baseline (cite specific metric + threshold)
- [ ] Customer-facing health check green
- [ ] Sample real traffic / synthetic check passes

## Escalation

When to page someone else, and who.

| Trigger | Escalate to | Channel |
|---------|-------------|---------|
| Mitigation steps 1-3 fail | [Team / individual] | [Slack channel / pagerduty] |
| Data loss suspected | [Data team] | [channel] |
| Security implications | [Security on-call] | [channel] |

## Background (Optional)

Context for understanding *why* this fires + why the mitigation works. Read this when not paging.

- **System:** [What component / service]
- **Why this happens:** [Underlying cause pattern]
- **Why this mitigation works:** [What invariant it restores]

## Related Documents

- Design Doc: [Affected component]
- Postmortem: [Postmortem doc that drove this runbook's creation, if any]
- ADR: [Decision that defines the SLO / threshold]

## Changelog

Append-only. Update when steps change, escalation paths change, or after a postmortem reveals a gap.

| Date | Change |
|------|--------|
| YYYY-MM-DD | Initial draft |
