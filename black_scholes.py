"""
Black-Scholes Model — Coffee Option Pricing
============================================

Prices a European call (and put) on coffee, plus the option Greeks.

THE MODEL
---------
Under Black-Scholes, the price of a European call on a non-dividend-paying
underlying is:

    C = S0 * N(d1) - X * exp(-r*T) * N(d2)

    d1 = [ ln(S0 / X) + (r + sigma^2 / 2) * T ] / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)

    S0    : spot price today
    X     : strike price
    r     : risk-free rate (continuously compounded, annualised)
    T     : time to maturity in years
    sigma : annualised volatility of log returns
    N(.)  : standard normal CDF  -> scipy.stats.norm.cdf

INTUITION
---------
    S0 * N(d1)             the expected value of receiving the asset, given exercise
    X * exp(-rT) * N(d2)   the present value of paying the strike, given exercise
    N(d2)                  risk-neutral probability the option finishes in the money

The put price follows from PUT-CALL PARITY, which is a no-arbitrage identity and
must hold exactly:

    C - P = S0 - X * exp(-r*T)

HOW TO USE THIS FILE
--------------------
Fill in every block marked "TODO". Then run:

    python black_scholes.py

and check your output against the target in README.md.
"""

import numpy as np
from scipy.stats import norm

# ---------------------------------------------------------------------------
# INPUTS  (hardcoded — see README for where each number comes from)
# ---------------------------------------------------------------------------

SPOT_PRICE = 1.20          # S0    : USD per pound
STRIKE_PRICE = 1.25        # X     : slightly out of the money
RISK_FREE_RATE = 0.02      # r     : 2%
TIME_TO_MATURITY = 0.5     # T     : six months
VOLATILITY = 0.25          # sigma : 25% annualised


# ---------------------------------------------------------------------------
# BUILDING BLOCKS
# ---------------------------------------------------------------------------

def d1_d2(spot, strike, rate, maturity, sigma):
    """Return the (d1, d2) pair used throughout Black-Scholes.

    Computing these once and reusing them keeps the pricing and Greeks
    functions short, and means a mistake here fails every test at once rather
    than hiding in one place.
    """
    d1 = (np.log(spot / strike) + (rate + sigma ** 2 / 2) * maturity) / (sigma * np.sqrt(maturity))
    d2 = d1 - sigma * np.sqrt(maturity)
    return d1, d2


# ---------------------------------------------------------------------------
# PRICING
# ---------------------------------------------------------------------------

def call_price(spot, strike, rate, maturity, sigma):
    """Black-Scholes price of a European CALL."""
    d1, d2 = d1_d2(spot, strike, rate, maturity, sigma)

    return spot * norm.cdf(d1) - strike * np.exp(-rate * maturity) * norm.cdf(d2)


def put_price(spot, strike, rate, maturity, sigma):
    """Black-Scholes price of a European PUT.

    P = X * exp(-r*T) * N(-d2) - S0 * N(-d1)

    Note the symmetry with the call: the same two terms, with the signs inside
    the normal CDF flipped and the order swapped.
    """
    d1, d2 = d1_d2(spot, strike, rate, maturity, sigma)

    return strike * np.exp(-rate * maturity) * norm.cdf(-d2) - spot * norm.cdf(-d1)


# ---------------------------------------------------------------------------
# THE GREEKS  (the risk sensitivities a desk actually trades on)
# ---------------------------------------------------------------------------

def greeks(spot, strike, rate, maturity, sigma):
    """Return a dict of the five standard Greeks for a CALL.

        delta : dC/dS      how much the option moves per $1 move in coffee
        gamma : d2C/dS2    how fast delta itself changes (your hedging cost)
        vega  : dC/dsigma  per 1 percentage point change in vol
        theta : dC/dT      time decay, per calendar day
        rho   : dC/dr      per 1 percentage point change in rates

    Formulas (call):
        delta = N(d1)
        gamma = n(d1) / (S * sigma * sqrt(T))
        vega  = S * n(d1) * sqrt(T)
        theta = -S * n(d1) * sigma / (2 * sqrt(T)) - r * X * exp(-r*T) * N(d2)
        rho   = X * T * exp(-r*T) * N(d2)

    where n(.) is the standard normal PDF -> norm.pdf
    """
    d1, d2 = d1_d2(spot, strike, rate, maturity, sigma)
    pdf_d1 = norm.pdf(d1)

    delta = norm.cdf(d1)
    gamma = pdf_d1 / (spot * sigma * np.sqrt(maturity))
    vega = spot * pdf_d1 * np.sqrt(maturity)
    theta = (-spot * pdf_d1 * sigma / (2 * np.sqrt(maturity))
             - rate * strike * np.exp(-rate * maturity) * norm.cdf(d2))
    rho = strike * maturity * np.exp(-rate * maturity) * norm.cdf(d2)

    return {
        "delta": delta,                          # raw, no scaling
        "gamma": gamma,                          # raw, no scaling
        "vega":  vega / 100,                     # per 1 vol point
        "theta": theta / 365,                    # per calendar day
        "rho":   rho / 100,                      # per 1 rate point
    }


# ---------------------------------------------------------------------------
# CHECKS
# ---------------------------------------------------------------------------

def put_call_parity_gap(spot, strike, rate, maturity, sigma):
    """Return  (C - P) - (S0 - X*exp(-r*T)).

    This is an identity, not an approximation. If your call and put are both
    right, this returns ~0 (within floating point noise, so ~1e-16). It is the
    single fastest way to catch a sign error.
    """
    c = call_price(spot, strike, rate, maturity, sigma)
    p = put_price(spot, strike, rate, maturity, sigma)
    return (c - p) - (spot - strike * np.exp(-rate * maturity))


def moneyness_table(spot, rate, maturity, sigma, strikes):
    """Return a list of (strike, call, put, delta) across a strike grid.

    Shows the volatility smile's absence in flat-vol Black-Scholes, and gives
    you a table to eyeball: calls must fall as strike rises, puts must rise.
    """
    return [
        (
            strike,
            call_price(spot, strike, rate, maturity, sigma),
            put_price(spot, strike, rate, maturity, sigma),
            greeks(spot, strike, rate, maturity, sigma)["delta"],
        )
        for strike in strikes
    ]


# ---------------------------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------------------------

def main():
    args = (SPOT_PRICE, STRIKE_PRICE, RISK_FREE_RATE, TIME_TO_MATURITY, VOLATILITY)
    d1, d2 = d1_d2(*args)
    c = call_price(*args)
    p = put_price(*args)
    g = greeks(*args)

    print("=" * 62)
    print("BLACK-SCHOLES — 6M EUROPEAN OPTION ON COFFEE")
    print("=" * 62)
    print(f"Spot           S0    = ${SPOT_PRICE:.4f} / lb")
    print(f"Strike         X     = ${STRIKE_PRICE:.4f} / lb")
    print(f"Risk-free rate r     = {RISK_FREE_RATE:.2%}")
    print(f"Maturity       T     = {TIME_TO_MATURITY} years")
    print(f"Volatility     sigma = {VOLATILITY:.2%}")
    print("-" * 62)
    print(f"d1 = {d1:+.6f}     d2 = {d2:+.6f}")
    print(f"N(d1) = {norm.cdf(d1):.6f}   N(d2) = {norm.cdf(d2):.6f}")
    print()
    print(f"CALL price           = ${c:.6f} / lb")
    print(f"PUT  price           = ${p:.6f} / lb")
    print(f"Call, per contract   = ${c * 37_500:,.2f}   (37,500 lb)")
    print(f"P(finish ITM) = N(d2) = {norm.cdf(d2):.2%}")
    print()

    print("Greeks (call)")
    print("-" * 62)
    print(f"  delta = {g['delta']:+.6f}   per $1 move in coffee")
    print(f"  gamma = {g['gamma']:+.6f}   change in delta per $1 move")
    print(f"  vega  = {g['vega']:+.6f}   per +1 vol point")
    print(f"  theta = {g['theta']:+.6f}   per calendar day")
    print(f"  rho   = {g['rho']:+.6f}   per +1 rate point")
    print()

    gap = put_call_parity_gap(*args)
    print(f"Put-call parity gap  = {gap:.2e}   (must be ~0)")
    print()

    print("Across strikes")
    print("-" * 62)
    print(f"  {'Strike':>8} {'Call':>10} {'Put':>10} {'Delta':>10}")
    for k, cc, pp, dd in moneyness_table(
        SPOT_PRICE, RISK_FREE_RATE, TIME_TO_MATURITY, VOLATILITY,
        [1.00, 1.10, 1.20, 1.25, 1.30, 1.40],
    ):
        tag = "  <-- base" if abs(k - STRIKE_PRICE) < 1e-9 else ""
        print(f"  {k:>8.2f} {cc:>10.5f} {pp:>10.5f} {dd:>10.5f}{tag}")
    print("=" * 62)


if __name__ == "__main__":
    main()
