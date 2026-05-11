# Feature: Test Canon-Frozen Fixture

> **Doc ID:** test-canon-frozen
> **Date:** 2026-05-11
> **DRI:** Test
> **Type:** Feature LLD
> **Status:** Implemented
> **Iteration:** 1

## Problem Statement

Test fixture for T-INT-010 integration test (LLD-010 r4 A13). Drives end-to-end LLD-008 + LLD-009 + LLD-010 path: canon-frozen body edit attempted via raw commit (no Addresses: lines) must be rejected by L2-finalize through framework hook.

## Success Criteria

- Fixture parsed as canon-frozen (Status: Implemented).
- L2 path triggers.

## Scope

In scope: fixture role only.

## Design

n/a.

## Edge Cases

n/a.

## Security

n/a.

## Testing

T-INT-010 only.

## Related Documents

- LLD-010 r4 A13.

## Changelog

| Date | Change |
|---|---|
| 2026-05-11 | Initial. |
