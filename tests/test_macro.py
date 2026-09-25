"""Tests for the macro toolkit (M02): cfmat.analytics.rates, cfmat.analytics.macro,
stats.event_day_effect and data.macro_calendar."""

import numpy as np
import pandas as pd
import pytest

from cfmat import data
from cfmat.analytics import macro, rates, stats

MATURITIES = np.array(data.MACRO_MATURITIES)


@pytest.fixture(scope="module")
def economy():
    return data.macro_calendar(seed=7)


# --- rates -----------------------------------------------------------------------------------

@pytest.mark.parametrize("params", [(7.2, -0.8, -1.0, 1.8), (6.8, 0.6, 1.2, 2.5), (7.5, -2.0, 0.5, 0.8)])
def test_nelson_siegel_fit_recovers_known_parameters(params):
    exact = rates.nelson_siegel_fit(MATURITIES, rates.nelson_siegel(MATURITIES, *params))
    assert (exact.beta0, exact.beta1, exact.beta2, exact.tau) == pytest.approx(params, abs=1e-5)
    assert exact.rmse < 1e-8
    noisy = rates.nelson_siegel(MATURITIES, *params) + np.random.default_rng(0).normal(0, 0.02, len(MATURITIES))
    fit = rates.nelson_siegel_fit(MATURITIES, noisy)
    assert fit.beta0 == pytest.approx(params[0], abs=0.1)
    assert fit.short_rate == pytest.approx(params[0] + params[1], abs=0.1)
    assert fit.rmse < 0.03


def test_nelson_siegel_panel_with_fixed_tau_matches_single_fits_and_tau_is_recovered():
    rng = np.random.default_rng(1)
    betas = np.column_stack([rng.uniform(6, 8, 30), rng.uniform(-3, 1, 30), rng.uniform(-1, 1, 30)])
    clean = np.array([rates.nelson_siegel(MATURITIES, *b, 1.5) for b in betas])
    curves = pd.DataFrame(clean + rng.normal(0, 0.01, clean.shape), columns=MATURITIES)
    assert rates.nelson_siegel_tau(curves) == pytest.approx(1.5, rel=0.05)
    panel = rates.nelson_siegel_panel(curves, tau=1.5)
    single = rates.nelson_siegel_fit(MATURITIES, curves.iloc[3], tau=1.5)
    assert panel.loc[3, ["beta0", "beta1", "beta2"]].tolist() == pytest.approx([single.beta0, single.beta1, single.beta2])
    assert np.abs(panel[["beta0", "beta1", "beta2"]].to_numpy() - betas).max() < 0.1


def test_nelson_siegel_fit_needs_four_maturities():
    with pytest.raises(ValueError):
        rates.nelson_siegel_fit([1, 2, 3], [6.0, 6.2, 6.3])


def test_bond_price_duration_and_convexity():
    assert rates.bond_price(7.0, 7.0, 10) == pytest.approx(100.0)
    assert rates.bond_price(8.0, 7.0, 10) < 100 < rates.bond_price(6.0, 7.0, 10)
    risk = rates.bond_risk(7.0, 7.0, 10)
    bump = 0.01
    up, down = rates.bond_price(7.0 + bump, 7.0, 10), rates.bond_price(7.0 - bump, 7.0, 10)
    assert risk["modified"] == pytest.approx((down - up) / (2 * bump / 100) / risk["price"], rel=1e-4)
    assert risk["convexity"] == pytest.approx((up + down - 2 * risk["price"]) / (bump / 100) ** 2 / risk["price"], rel=1e-3)
    assert risk["dv01"] == pytest.approx(risk["modified"] * risk["price"] * 1e-4)
    zero = rates.bond_risk(7.0, 0.0, 5)
    assert zero["macaulay"] == pytest.approx(5.0)


def test_inversion_episodes_merge_short_gaps_and_drop_short_runs():
    values = [1] * 5 + [-1] * 10 + [1] * 2 + [-1] * 8 + [1] * 20 + [-1] * 3 + [1] * 5
    spread = pd.Series(values, index=pd.bdate_range("2024-01-01", periods=len(values)), dtype=float)
    episodes = rates.inversion_episodes(spread, min_days=5, merge_gap=3)
    assert len(episodes) == 1
    assert episodes.loc[0, "days"] == 20
    assert episodes.loc[0, "start"] == spread.index[5]
    assert rates.inversion_episodes(spread, min_days=5, merge_gap=0)["days"].tolist() == [10, 8]


# --- macro -----------------------------------------------------------------------------------

def test_release_sessions_respect_the_close_weekends_and_the_calendar_end():
    days = pd.bdate_range("2026-01-05", "2026-01-16")
    stamps = pd.to_datetime(["2026-01-05 10:00", "2026-01-05 15:30", "2026-01-05 16:00",
                             "2026-01-09 23:30", "2026-01-10 11:00", "2026-01-16 16:00"])
    sessions = macro.release_sessions(stamps, days)
    expected = pd.to_datetime(["2026-01-05", "2026-01-06", "2026-01-06", "2026-01-12", "2026-01-12", None])
    assert sessions.tolist()[:5] == list(expected[:5])
    assert pd.isna(sessions.iloc[5])


def _toy_releases():
    rows = []
    for k, month in enumerate(pd.period_range("2025-01", "2025-08", freq="M")):
        first = pd.Timestamp(month.year, month.month, 1) + pd.DateOffset(months=1, days=11) + pd.Timedelta("16:00:00")
        rows.append({"series": "X", "reference": month, "release_ts": first, "vintage": "first", "value": float(k)})
        rows.append({"series": "X", "reference": month, "release_ts": first + pd.DateOffset(months=1),
                     "vintage": "revised", "value": float(k) + 10})
    return pd.DataFrame(rows)


def test_latest_known_uses_each_vintage_only_after_it_is_published():
    releases, days = _toy_releases(), pd.bdate_range("2025-02-03", "2025-06-30")
    known = macro.latest_known(releases, days, "X", change_periods=1)
    # CPI-style release on 12 March 16:00 (February's first print, January's revision) → known from 13 March
    assert known.loc["2025-03-12", "reference"] == pd.Period("2025-01", "M")
    assert known.loc["2025-03-12", "value"] == 0.0
    assert known.loc["2025-03-13", "reference"] == pd.Period("2025-02", "M")
    assert known.loc["2025-03-13", "value"] == 1.0
    assert known.loc["2025-03-13", "change"] == pytest.approx(1.0 - 10.0)   # January is now its revised 10
    first = macro.latest_known(releases, days, "X", change_periods=1, vintage="first")
    assert first.loc["2025-03-13", "change"] == pytest.approx(1.0)
    assert known.loc[:"2025-02-12"].isna().all().all()


def test_regime_labels_are_causal_under_truncation(economy):
    days, releases = economy.market.index, economy.releases
    full = macro.growth_inflation_regimes(releases, days)
    for cutoff in days[[400, 1300, 2200]]:
        cut = macro.growth_inflation_regimes(releases[releases["release_ts"] <= cutoff + pd.Timedelta("23:59:59")],
                                             days[days <= cutoff])
        pd.testing.assert_frame_equal(cut, full.loc[:cutoff])
    hindsight = macro.growth_inflation_regimes(releases, days, timing="reference")
    cutoff = days[1300]
    cut = macro.growth_inflation_regimes(releases[releases["release_ts"] <= cutoff + pd.Timedelta("23:59:59")],
                                         days[days <= cutoff], timing="reference")
    assert (cut["regime"].fillna("") != hindsight.loc[:cutoff, "regime"].fillna("")).any()


def test_hindsight_labels_match_the_true_regime_and_causal_labels_lag(economy):
    days, truth = economy.market.index, economy.truth
    hindsight = macro.growth_inflation_regimes(economy.releases, days, timing="reference")["regime"]
    causal = macro.growth_inflation_regimes(economy.releases, days)["regime"]
    assert (hindsight == truth["daily_regime"]).mean() > 0.9
    assert 0.3 < (causal == truth["daily_regime"]).mean() < (hindsight == truth["daily_regime"]).mean()
    assert set(causal.dropna()) <= set(macro.REGIMES.values())
    with pytest.raises(ValueError):
        macro.growth_inflation_regimes(economy.releases, days, timing="tomorrow")


# --- stats.event_day_effect --------------------------------------------------------------------

def test_event_day_effect_finds_higher_volatility():
    rng = np.random.default_rng(3)
    idx = pd.bdate_range("2020-01-01", periods=1500)
    events = pd.Series(False, index=idx)
    events.iloc[rng.choice(1500, 60, replace=False)] = True
    returns = pd.Series(rng.normal(0, 0.01, 1500) * np.where(events, 2.0, 1.0), index=idx)
    out = stats.event_day_effect(returns.abs(), events, n_perm=500)
    assert out["events"] == 60
    assert out["ratio"] == pytest.approx(2.0, rel=0.25)
    assert out["p_value"] < 0.01 and out["t_hac"] > 3


def test_event_day_effect_keeps_its_size_when_event_days_are_more_volatile():
    idx = pd.bdate_range("2020-01-01", periods=1000)
    events = pd.Series(np.arange(1000) % 100 == 7, index=idx)                        # 10 events, 3x volatility
    rejections = 0
    for seed in range(60):
        noise = np.random.default_rng(seed).normal(0, 0.01, 1000) * np.where(events, 3.0, 1.0)
        rejections += stats.event_day_effect(pd.Series(noise, index=idx), events, n_perm=300, seed=seed)["p_value"] < 0.05
    assert rejections / 60 < 0.15


# --- data.macro_calendar ---------------------------------------------------------------------

def test_macro_calendar_events_times_and_sessions(economy):
    calendar, truth = economy.calendar, economy.truth
    counts = calendar["event"].value_counts()
    assert counts["RBI policy"] == 60 and counts["CPI"] == 120 and counts["Union Budget"] == 10
    times = calendar.groupby("event")["release_ts"].apply(lambda s: set(s.dt.strftime("%H:%M")))
    assert times["RBI policy"] == {"10:00"} and times["CPI"] == {"16:00"} and times["FOMC"] == {"23:30"}
    rbi = calendar["event"] == "RBI policy"
    assert (truth["sessions"][rbi] == calendar.loc[rbi, "release_ts"].dt.normalize()).all()
    cpi = calendar["event"] == "CPI"
    assert (truth["sessions"][cpi] > calendar.loc[cpi, "release_ts"]).all()
    data_rows = calendar["event"].isin(["CPI", "IIP", "GDP", "RBI policy"])
    assert np.allclose(calendar.loc[data_rows, "actual"] - calendar.loc[data_rows, "consensus"],
                       calendar.loc[data_rows, "surprise"], atol=1e-9)
    assert np.allclose(calendar.loc[rbi, "actual"] % 0.25, 0)
    assert set(calendar.loc[rbi, "surprise"].round(2)) <= {-0.25, 0.0, 0.25}


def test_macro_calendar_vintages_and_planted_truth(economy):
    releases, truth = economy.releases, economy.truth
    cpi = releases[releases["series"] == "CPI"].astype({"reference": "period[M]"})
    revised = cpi[cpi["vintage"] == "revised"].set_index("reference")["value"]
    assert np.allclose(revised, truth["monthly"]["inflation"].reindex(revised.index).round(2))
    both = (releases[releases["series"] == "IIP"].astype({"reference": "period[M]"})
            .pivot_table(index="reference", columns="vintage", values="value").dropna())
    assert 0.4 < (both["revised"] - both["first"]).std() < 1.2
    iip = releases[releases["series"] == "IIP"].astype({"reference": "period[M]"})
    first_ts = iip[iip["vintage"] == "first"].set_index("reference")["release_ts"]
    revised_ts = iip[iip["vintage"] == "revised"].set_index("reference")["release_ts"]
    assert (revised_ts > first_ts.reindex(revised_ts.index)).all()
    factors = truth["factors"]
    rebuilt = np.array([rates.nelson_siegel(MATURITIES, *row[:3], row[3]) for row in factors.to_numpy()[::50]])
    assert (economy.curves.to_numpy()[::50] - rebuilt).std() == pytest.approx(truth["params"]["yield_noise"], rel=0.2)
    again = data.macro_calendar(seed=7)
    pd.testing.assert_frame_equal(again.curves, economy.curves)
    pd.testing.assert_frame_equal(again.calendar, economy.calendar)
