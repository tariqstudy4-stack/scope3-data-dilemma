"""
PCF cascade model: PACT/Catena-X-style tier-by-tier chaining of product
carbon footprints over the EU-27 technosphere.

Model
-----
True cradle-to-gate intensity (ground truth):  m = E (I - A)^-1
Each industry j, when asked for its PCF per unit output, reports
    r_j = e_j + sum_i A_ij * rhat_i          if j participates (primary)
    r_j = s_j                                 if j does not (secondary)
where rhat_i is what j's supplier i hands over: supplier i's own report if
i participates, else the secondary factor s_i (database sector average).

Tier depth T = number of primary hand-offs up the chain. T=1 reproduces the
PACT baseline "primary direct + secondary upstream"; T->inf is the fixed
point of full cascade chaining. The assessed target always knows its own
direct emissions (e_j) and its direct purchase vector A[:, j].

Estimated target PCF:  p_j = e_j + sum_i A_ij * rhat_i(T)
"""
import numpy as np



# Eurostat's own coarser NACE Rev.2 aggregation (the standard "A*10"/"A*3"
# grouping used in national-accounts and structural-business-statistics
# publications) gives every one-letter section a non-empty sibling set at
# some level of the hierarchy. Seven sections in the 64-industry table used
# here have exactly one member (B, D, F, I, O, P, T), so they have no
# within-section sibling at all; falling back straight to an economy-wide
# average for those seven, as an earlier version of this model did, mixes
# in industries with completely unrelated production recipes (e.g. an
# electricity-sector target inheriting a footprint pulled down by
# low-intensity services). Instead, each singleton section borrows the
# finest Eurostat-standard supersection that does contain other members:
#   B, D           -> "B-E" (Industry, incl. energy)
#   F              -> "B-F" (Industry, incl. construction; needed because
#                     F stands alone even within B-E)
#   I              -> "G-I" (Trade, transport, accommodation and food)
#   O, P           -> "O-Q" (Public administration, education, health)
#   T              -> "R-U" (Arts, entertainment and other services)
_SUPERSECTION = {
    "B": "B-E", "D": "B-E",
    "F": "B-F",
    "I": "G-I",
    "O": "O-Q", "P": "O-Q",
    "T": "R-U",
}
_SUPERSECTION_MEMBERS = {
    "B-E": set("BCDE"),
    "B-F": set("BCDEF"),
    "G-I": set("GHI"),
    "O-Q": set("OPQ"),
    "R-U": set("RSTU"),
}


def secondary_factors(M_true, industries, level="section"):
    """Database-style sector-average cradle-to-gate factors.

    level='section': average of true intensities over the NACE section
    siblings (A, B, C, D, ...), mimicking an emission-factor database that
    is correct on sector average but blind to within-sector variation.
    Sections with no within-section sibling fall back to the coarser
    Eurostat-standard supersection (see `_SUPERSECTION` above) rather than
    an economy-wide average.
    """
    sections = np.array([c[0] for c in industries])
    S = np.zeros_like(M_true)
    for sec in np.unique(sections):
        idx = np.where(sections == sec)[0]
        for j in idx:
            sib = [i for i in idx if i != j]
            if sib:  # leave-one-out sibling average (database built
                     # from other companies, never from the target itself)
                S[:, j] = M_true[:, sib].mean(axis=1)
            else:    # singleton section: leave-one-out average over the
                     # coarser Eurostat supersection containing it
                super_members = _SUPERSECTION_MEMBERS[_SUPERSECTION[sec]]
                sib2 = [i for i in range(len(industries))
                        if sections[i] in super_members and i != j]
                S[:, j] = M_true[:, sib2].mean(axis=1)
    return S


def cascade_reports(A, E_row, s_row, participants, tiers):
    """Reported per-unit PCF vector r after `tiers` primary hand-offs.

    A            : (n,n) technosphere (column = buyer)
    E_row        : (n,) direct intensity for one indicator
    s_row        : (n,) secondary factors for one indicator
    participants : (n,) bool
    tiers        : int >= 1, or None for fixed point (converged)
    """
    P = participants
    r = s_row.copy()          # tier 0: everyone looks like a database average
    if tiers is None:
        for _ in range(200):  # fixed point; rho(A) < 1 guarantees convergence
            r_new = np.where(P, E_row + r @ A, s_row)
            if np.max(np.abs(r_new - r)) < 1e-12:
                r = r_new
                break
            r = r_new
    else:
        for _ in range(tiers):
            r = np.where(P, E_row + r @ A, s_row)
    return r


def target_pcf(A, E_row, reports):
    """What an assessor computes for every target with primary own-data."""
    return E_row + reports @ A


def true_pcf(A, E):
    n = A.shape[0]
    return E @ np.linalg.inv(np.eye(n) - A)


# ---------------------------------------------------------------- metrics
def mape(est, truth, targets):
    t = truth[targets]
    return float(np.median(np.abs((est[targets] - t) / t)) * 100)


def ape_per_target(est, truth, targets):
    """Absolute percentage error for every target individually (not
    aggregated) -- used to report tail behaviour (p90 / max) alongside the
    median, since the median alone hides which single product is badly
    mis-estimated."""
    t = truth[targets]
    return np.abs((est[targets] - t) / t) * 100


def ranking_flips(est, truth, targets, material=0.05):
    """Fraction of material pairwise comparisons whose ordering reverses."""
    t = truth[targets]
    e = est[targets]
    n = len(t)
    flips = total = 0
    for a in range(n):
        for b in range(a + 1, n):
            denom = min(t[a], t[b])
            if denom <= 0 or abs(t[a] - t[b]) / denom < material:
                continue
            total += 1
            if (t[a] - t[b]) * (e[a] - e[b]) < 0:
                flips += 1
    return 100 * flips / total if total else np.nan, total
