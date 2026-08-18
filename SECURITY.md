# Security Policy

## Scope

This repository contains an educational implementation of the Black-Scholes option pricing model. It has no network access, no authentication, no user input handling, and no persistent storage. The conventional software attack surface is close to nil.

The risks worth documenting here are **model risks**, not software vulnerabilities. In derivatives, a wrong model is the security problem.

## Model risk disclosure

This code is **not production trading software** and must not be used to price, hedge, or risk-manage real option positions. Specifically:

- **All inputs are hardcoded illustrative values.** Spot, strike, rate and volatility are assumptions from a teaching exercise, not market data.
- **Volatility is constant across strikes.** This is the model's largest and best-documented failure. Real coffee options trade with a pronounced skew, because a Brazilian frost is a one-sided risk and out-of-the-money calls price it in. Using a single flat 25% will systematically misprice wings in both directions.
- **This prices options on spot, not on futures.** Listed ICE coffee options are options on the futures contract, which is properly Black-76. Applying spot Black-Scholes to a futures option double-counts the cost of carry.
- **European exercise is assumed.** ICE coffee options are American-style. The early-exercise premium is ignored, which understates puts in particular.
- **No dividends, storage costs, or convenience yield** enter the model, all of which matter for a physical commodity.
- **Log-normal returns with no jumps.** Weather-driven commodity moves are discontinuous; the model assumes they are not.
- **No transaction costs, bid-ask spread, margin, or liquidity constraints.**

The Greeks are analytically correct derivatives of *this model*. They are only useful for hedging to the extent the model itself is right, which for a real coffee option it is not.

## What the tests do and do not prove

The test suite verifies internal consistency: put-call parity holds exactly, no-arbitrage bounds are respected, and the analytic Greeks match numerical derivatives of the pricing function. That is strong evidence the implementation matches the mathematics.

It is **no evidence at all** that the mathematics matches the market. Those are separate claims, and only the first one is tested here.

## Reporting an issue

Please open a GitHub issue describing:

1. What you expected the model to produce
2. What it actually produced
3. The inputs that reproduce it

Mathematical errors are the most valuable reports. If a test asserts something that is not actually a property of Black-Scholes, that is a bug in the test and worth reporting too.

## Supported versions

Only the `main` branch is maintained. There are no released versions and no backported fixes.
