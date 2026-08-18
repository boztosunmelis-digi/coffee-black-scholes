"""Sanity checks for the Black-Scholes implementation.

Run with:  pytest -q

Each test is a property the model must satisfy. Put-call parity and the
no-arbitrage bounds in particular will catch almost any sign or scaling error.
"""

import numpy as np
import pytest

from black_scholes import (
    d1_d2,
    call_price,
    put_price,
    greeks,
    put_call_parity_gap,
    moneyness_table,
)

BASE = (1.20, 1.25, 0.02, 0.5, 0.25)  # S0, X, r, T, sigma


def test_put_call_parity_holds_exactly():
    """C - P = S - X*exp(-rT). An identity, so the gap is floating-point dust."""
    assert put_call_parity_gap(*BASE) == pytest.approx(0.0, abs=1e-12)


def test_parity_holds_across_many_parameter_sets():
    for s in (0.8, 1.2, 2.0):
        for k in (0.9, 1.25, 1.8):
            for sig in (0.1, 0.25, 0.6):
                gap = put_call_parity_gap(s, k, 0.02, 0.5, sig)
                assert gap == pytest.approx(0.0, abs=1e-12)


def test_no_arbitrage_bounds():
    """max(S - X*exp(-rT), 0) <= C <= S. Violating this is free money."""
    s, k, r, t, sig = BASE
    c = call_price(*BASE)
    lower = max(s - k * np.exp(-r * t), 0.0)
    assert lower <= c <= s


def test_prices_are_positive():
    assert call_price(*BASE) > 0
    assert put_price(*BASE) > 0


def test_call_falls_as_strike_rises():
    """The right to buy at a higher price is worth less."""
    cheap_strike = call_price(1.20, 1.00, 0.02, 0.5, 0.25)
    dear_strike = call_price(1.20, 1.50, 0.02, 0.5, 0.25)
    assert cheap_strike > dear_strike


def test_both_options_rise_with_volatility():
    """Vega is positive for calls AND puts — more uncertainty, more optionality."""
    low_c = call_price(1.20, 1.25, 0.02, 0.5, 0.10)
    high_c = call_price(1.20, 1.25, 0.02, 0.5, 0.50)
    low_p = put_price(1.20, 1.25, 0.02, 0.5, 0.10)
    high_p = put_price(1.20, 1.25, 0.02, 0.5, 0.50)
    assert high_c > low_c
    assert high_p > low_p


def test_deep_itm_call_approaches_intrinsic_value():
    """With a tiny vol and a strike far below spot, C -> S - X*exp(-rT)."""
    s, k, r, t = 2.00, 0.50, 0.02, 0.5
    c = call_price(s, k, r, t, 0.0001)
    assert c == pytest.approx(s - k * np.exp(-r * t), abs=1e-6)


def test_deep_otm_call_is_worthless():
    assert call_price(1.20, 10.0, 0.02, 0.5, 0.25) == pytest.approx(0.0, abs=1e-9)


def test_delta_is_between_zero_and_one():
    g = greeks(*BASE)
    assert 0.0 < g["delta"] < 1.0


def test_delta_matches_numerical_derivative():
    """The analytic delta must equal dC/dS computed by finite difference."""
    s, k, r, t, sig = BASE
    h = 1e-5
    numeric = (call_price(s + h, k, r, t, sig) - call_price(s - h, k, r, t, sig)) / (2 * h)
    assert greeks(*BASE)["delta"] == pytest.approx(numeric, rel=1e-6)


def test_vega_matches_numerical_derivative():
    """Vega is scaled per 1 vol point, so multiply the raw derivative by 100."""
    s, k, r, t, sig = BASE
    h = 1e-6
    numeric = (call_price(s, k, r, t, sig + h) - call_price(s, k, r, t, sig - h)) / (2 * h)
    assert greeks(*BASE)["vega"] * 100 == pytest.approx(numeric, rel=1e-5)


def test_gamma_is_positive_and_vega_is_positive():
    g = greeks(*BASE)
    assert g["gamma"] > 0
    assert g["vega"] > 0


def test_theta_is_negative_for_a_long_call():
    """A long option bleeds value as expiry approaches."""
    assert greeks(*BASE)["theta"] < 0


def test_moneyness_table_is_monotonic():
    strikes = [1.00, 1.10, 1.20, 1.30, 1.40]
    rows = moneyness_table(1.20, 0.02, 0.5, 0.25, strikes)
    assert len(rows) == len(strikes)
    calls = [c for _, c, _, _ in rows]
    puts = [p for _, _, p, _ in rows]
    assert calls == sorted(calls, reverse=True)  # falling in strike
    assert puts == sorted(puts)                  # rising in strike


def test_d2_is_below_d1():
    d1, d2 = d1_d2(*BASE)
    assert d2 < d1
