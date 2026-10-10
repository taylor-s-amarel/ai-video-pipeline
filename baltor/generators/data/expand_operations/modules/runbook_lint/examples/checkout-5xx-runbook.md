---
title: Checkout 5xx error rate high
owner: team-payments
last_reviewed: 2026-09-01
alerts: [CheckoutHighErrorRate, SLOBurnRate_checkout_availability_1h]
---

# Summary
Use when checkout returns 5xx above 2% for 5 minutes. Customer impact: card payments fail.
Dashboard: https://grafana.example.com/d/checkout-red/checkout

## Symptoms
- Alert `CheckoutHighErrorRate` (page) or the 1h SLO burn-rate alert.
- Support reports "payment failed" spikes.

## Diagnosis
1. Check whether a deploy happened in the last hour:
   ```bash
   kubectl -n shop rollout history deployment/checkout
   ```
   Expected: the newest revision's timestamp. A revision within the last hour makes a rollback the first move.
2. Check the dependency status for the payment provider (their status page) and our egress errors:
   ```bash
   kubectl -n shop logs deploy/checkout --since=15m | grep -c '"level":"ERROR"'
   ```
   Expected: under 50 lines in 15 minutes when healthy.

## Mitigation
- Recent deploy: roll back (see Rollback) and confirm the error rate falls within 10 minutes on the dashboard.
- Provider outage: enable the queued-payments flag `checkout.defer_capture` and post a status update.

## Rollback
```bash
kubectl -n shop rollout undo deployment/checkout
kubectl -n shop rollout status deployment/checkout --timeout=5m
```
Verify: `rollout status` reports success and 5xx ratio returns below 0.5%.

## Escalation
- After 15 minutes without improvement, page the payments secondary and the incident commander.
- Provider issue: open a priority ticket with the provider and record the ticket id in the incident channel.
