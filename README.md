# Black-Scholes Model — Coffee Options

Prices a six-month European call and put on coffee, computes the five standard Greeks, and verifies the result against put-call parity.

## The model

```
C  = S0·N(d1) − X·e^(−rT)·N(d2)
P  = X·e^(−rT)·N(−d2) − S0·N(−d1)

d1 = [ ln(S0/X) + (r + σ²/2)·T ] / (σ·√T)
d2 = d1 − σ·√T
```

| Symbol | Meaning | Value used | Where it comes from |
|---|---|---|---|
| `S0` | Spot price, USD/lb | 1.20 | Same source as the cost of carry project |
| `X` | Strike | 1.25 | A listed ICE "C" contract strike, slightly OTM |
| `r` | Risk-free rate | 2.00% | 6-month US T-bill (FRED `DGS6MO`) |
| `T` | Time to maturity | 0.5 years | Six months |
| `σ` | Volatility | 25% p.a. | Realised vol of daily log returns, annualised by √252 |

Reading the formula: `S0·N(d1)` is the expected value of receiving the coffee given exercise, `X·e^(−rT)·N(d2)` is the present value of paying the strike given exercise, and `N(d2)` alone is the risk-neutral probability of finishing in the money.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python black_scholes.py
pytest -q
```

## Expected output

```
d1 = -0.085967     d2 = -0.262744
CALL price           = $0.068358 / lb
PUT  price           = $0.105920 / lb
P(finish ITM) = N(d2) = 39.64%

  delta = +0.465746
  gamma = +1.873695
  vega  = +0.003373
  theta = -0.000258
  rho   = +0.002453

Put-call parity gap  = 1.67e-16
```

and `15 passed` from pytest.

**If your numbers are off, debug in this order:**

1. Put-call parity gap not ~0 (`1e-16` or smaller) — you have a sign error in the call or the put. Nothing else matters until this is clean.
2. Call price is `$0.0684` but delta is wrong — check the Greek scaling (`/100` for vega and rho, `/365` for theta).
3. `d1` has the wrong sign — you probably wrote `(r − σ²/2)` instead of `(r + σ²/2)`. That is the drift used in the *real-world* GBM exponent, not in `d1`.

## What the tests check

15 tests, each one a property Black-Scholes must satisfy:

- **put-call parity** holds exactly, across a 27-point grid of spot/strike/vol
- no-arbitrage bounds: `max(S − X·e^(−rT), 0) ≤ C ≤ S`
- calls fall as strike rises; puts rise
- both calls and puts increase with volatility (vega positive on both)
- deep-ITM call with near-zero vol converges to intrinsic value
- deep-OTM call is worthless
- **analytic delta equals the numerical derivative** `dC/dS` by central difference
- **analytic vega equals the numerical derivative** `dC/dσ`
- gamma and vega positive, theta negative for a long call

The finite-difference tests are the ones worth pointing at in an interview: they prove the Greeks are the actual derivatives of your pricing function, not formulas copied out of a textbook.

## Notes and limitations

- **Black-Scholes vs Black-76.** This prices an option on the *spot*. Coffee options on ICE are options on the *futures*, which is properly the Black-76 model: replace `S0` with `F·e^(−rT)`, which drops the `r` out of `d1`. Worth knowing the distinction — it is a common interview follow-up, and it connects this project directly to the cost of carry one.
- **Constant volatility is the big assumption.** Real coffee options trade with a pronounced skew: out-of-the-money calls carry extra vol because a Brazilian frost is a one-sided risk. A flat 25% across all strikes is exactly what the market does not do.
- **European exercise.** ICE coffee options are American-style, so this slightly understates the put in particular.
- **Volatility input.** 25% is the guide's assumption. Realised vol on Arabica is often materially higher; computing it from actual price history is the obvious next commit.
