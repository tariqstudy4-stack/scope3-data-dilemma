"""Participation patterns: who in the supply network provides primary PCFs.

Each pattern produces a single deterministic-per-seed ONORDERING of all n
industries (`*_order`). Participation at any rate is then the prefix of
that order of length round(rate*n). This makes participation NESTED across
rates (the 20% participants are a subset of the 40% participants, etc.),
which is what "onboarding" is supposed to mean, and makes every rate along
one (pattern, seed) draw share the same underlying recruitment sequence.

The order itself does not depend on which pollutant is being assessed or
on the chaining depth, so the same participant set is reused across all
four indicators and all four tier depths for a given (pattern, seed). This
removes the confound where different indicators or depths were silently
compared across different participant draws.
"""
import numpy as np


def _weighted_order(n, rng, weight):
    """Full ordering of 0..n-1 by weighted sampling without replacement."""
    order = []
    remaining = list(range(n))
    w = np.asarray(weight, dtype=float)
    for _ in range(n):
        ws = w[remaining]
        s = ws.sum()
        ws = (ws / s) if s > 0 else np.full(len(remaining), 1.0 / len(remaining))
        pick = rng.choice(len(remaining), p=ws)
        order.append(remaining.pop(pick))
    return order


def random_order(n, rng, **_):
    """No particular onboarding strategy: a uniformly random sequence."""
    order = list(range(n))
    rng.shuffle(order)
    return order


def flow_order(n, rng, supply, **_):
    """Largest-suppliers-tend-to-join-first: weighted without replacement,
    probability proportional to total intermediate supply."""
    return _weighted_order(n, rng, supply)


def cluster_order(n, rng, sections, **_):
    """Whole NACE sections onboard together (industry consortia): sections
    arrive in random order, and within a section members are onboarded in
    a fixed random order, so partial-section participation is handled by
    simple prefix-truncation instead of a separate trimming step."""
    secs = list(np.unique(sections))
    rng.shuffle(secs)
    order = []
    for sec in secs:
        members = np.where(sections == sec)[0].tolist()
        rng.shuffle(members)
        order.extend(members)
    return order


def strategic_order(n, rng, advantage, **_):
    """Self-selected (MNAR) disclosure: suppliers whose true intensity
    looks BETTER than the sector-average default they would otherwise be
    assigned are more likely to volunteer first, mirroring a supplier that
    discloses because the number is flattering rather than because it is
    representative. `advantage` is a composite, indicator-averaged
    standardized score (positive = looks better than the database
    default); weighting is exp(advantage / std(advantage))."""
    scale = np.std(advantage) + 1e-9
    w = np.exp(advantage / scale)
    return _weighted_order(n, rng, w)


PATTERNS = ("random", "flow", "cluster", "strategic")

_ORDER_FN = {
    "random": random_order,
    "flow": flow_order,
    "cluster": cluster_order,
    "strategic": strategic_order,
}


def full_order(pattern, n, rng, supply=None, sections=None, advantage=None):
    return _ORDER_FN[pattern](n, rng, supply=supply, sections=sections,
                               advantage=advantage)


def sample_from_order(order, n, rate):
    k = int(round(rate * n))
    p = np.zeros(n, bool)
    if k:
        p[order[:k]] = True
    return p


def sample(pattern, n, rate, rng, supply=None, sections=None, advantage=None):
    """Back-compat single-call entry point (builds a fresh order each time;
    prefer full_order + sample_from_order when reusing across rates)."""
    order = full_order(pattern, n, rng, supply=supply, sections=sections,
                        advantage=advantage)
    return sample_from_order(order, n, rate)
