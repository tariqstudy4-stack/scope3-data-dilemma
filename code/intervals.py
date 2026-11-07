"""Interval helpers shared by the experiment scripts.

Two conventions for the lognormal widening of a secondary factor s with geometric
standard deviation GSD (sigma = ln GSD):

  median-preserving (the convention used in the submitted manuscript and in common LCA
      practice, where the stored value is the geometric mean): s * exp(sigma * z).
      The mean of the multiplier is exp(sigma^2 / 2), i.e. 1.27 at GSD 2.0.
  mean-preserving: s * exp(sigma * z - sigma^2 / 2). The mean of the multiplier is 1.

The cascade is affine in the secondary-factor draws (a participant reports e + R A, a
non-participant reports its draw), so the mean-preserving draws follow from the
median-preserving draws and one cascade with all secondary factors set to zero:

    draws_mean = d0 + exp(-sigma^2 / 2) * (draws_median - d0)

code/check_affine_noise.py verifies this against a direct computation.
"""
import numpy as np


def mean_preserving(draws, d0, sigma):
    """Draws for the mean-preserving convention from median-preserving draws."""
    return d0 + np.exp(-sigma ** 2 / 2.0) * (draws - d0)


def coverage_width(draws, m, tidx, nominal=95):
    """Coverage (%) of the true values by the central interval, and median relative width.

    A relative tolerance of 1e-9 on the comparison keeps the result defined when the
    interval collapses to a point (full participation), where floating-point equality
    would otherwise fail.
    """
    lo = np.percentile(draws, (100 - nominal) / 2, axis=0)
    hi = np.percentile(draws, 100 - (100 - nominal) / 2, axis=0)
    tol = 1e-9 * np.maximum(m[tidx], 1e-30)
    cov = float(np.mean((m[tidx] >= lo[tidx] - tol) & (m[tidx] <= hi[tidx] + tol)) * 100)
    width = float(np.median((hi[tidx] - lo[tidx]) / np.maximum(m[tidx], 1e-30)))
    return cov, width
