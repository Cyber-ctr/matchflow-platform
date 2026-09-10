# MatchFlow Monetization Foundation

The employer billing page includes three hypothesis-driven plans:

- Starter — 15,000 FCFA/month
- Growth — 35,000 FCFA/month
- Scale — 75,000 FCFA/month

These are placeholders for market testing, not validated market prices.

The `payments` table and `PaymentService` provide a provider-neutral foundation. Before charging real money, integrate the selected Mobile Money provider(s), verify callbacks/webhooks, implement idempotency, reconciliation, refunds and fraud controls, then activate subscriptions only after confirmed payment.
