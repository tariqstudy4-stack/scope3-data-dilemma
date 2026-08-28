"""
Build EU-27 technosphere and environmental extension from Eurostat open data.

Datasets (Eurostat dissemination API, no license required):
  naio_10_cp1750  - EU-27 symmetric input-output table (industry by industry),
                    64-industry NACE Rev.2, reference year 2022, current prices
  env_ac_ainah_r2 - Air emissions accounts by NACE Rev.2 activity, 2022

Outputs (saved to ./data/):
  matrices.npz : A (64x64 technosphere), E (4x64 extension, per MEUR output),
                 x (industry output, MEUR), Z (intermediate use, MEUR),
                 F (emissions by industry, thousand tonnes)
  industries.csv, checks.json
"""
import json
import os
import urllib.request
from collections import OrderedDict

import numpy as np

BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
YEAR = "2022"
GEO = "EU27_2020"

# Eurostat A*64 industry classification (64 industries).
IND64 = [
    "A01", "A02", "A03", "B", "C10-12", "C13-15", "C16", "C17", "C18", "C19",
    "C20", "C21", "C22", "C23", "C24", "C25", "C26", "C27", "C28", "C29",
    "C30", "C31_32", "C33", "D", "E36", "E37-39", "F", "G45", "G46", "G47",
    "H49", "H50", "H51", "H52", "H53", "I", "J58", "J59_60", "J61", "J62_63",
    "K64", "K65", "K66", "L68A", "L68B", "M69_70", "M71", "M72", "M73",
    "M74_75", "N77", "N78", "N79", "N80-82", "O", "P", "Q86", "Q87_88",
    "R90-92", "R93", "S94", "S95", "S96", "T",
]
MANUF = [c for c in IND64 if c.startswith("C")]  # 19 manufacturing targets

AIRPOL = OrderedDict([
    ("GHG", "GHG (CO2e)"),
    ("ACG", "Acid gases (SO2e)"),
    ("O3PR", "Ozone precursors (NMVOCe)"),
    ("PM2_5", "Primary PM2.5"),
])


def fetch(dataset: str, **params) -> dict:
    parts = []
    for k, v in params.items():
        vals = v if isinstance(v, (list, tuple)) else [v]
        parts += [f"{k}={vi}" for vi in vals]
    q = "&".join(parts)
    url = f"{BASE}/{dataset}?format=JSON&lang=EN&{q}"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                raise
            print(f"  retry {attempt + 1} after {e}")
    raise RuntimeError


def jsonstat_to_dict(d: dict) -> dict:
    """Map {(cat1, cat2, ...): value} from a JSON-stat 2.0 response."""
    dims = d["id"]
    sizes = d["size"]
    cats = [list(d["dimension"][k]["category"]["index"]) for k in dims]
    out = {}
    for lin, val in d["value"].items():
        lin = int(lin)
        key = []
        rem = lin
        for s, cat in zip(reversed(sizes), reversed(cats)):
            key.append(cat[rem % s])
            rem //= s
        out[tuple(reversed(key))] = val
    return out, dims


# SIOT A*64 code -> air-emissions-accounts NACE code
EMISSION_CODE = {
    "C10-12": "C10-C12", "C13-15": "C13-C15", "C31_32": "C31_C32",
    "E37-39": "E37-E39", "J59_60": "J59_J60", "J62_63": "J62_J63",
    "M69_70": "M69_M70", "M74_75": "M74_M75", "N80-82": "N80-N82",
    "Q87_88": "Q87_Q88", "R90-92": "R90-R92",
    # emissions accounts publish L68A and section L; real-estate-excl-rents
    # emissions are taken as L minus L68A (handled below)
    "L68B": "__L_MINUS_L68A__",
}


def main() -> None:
    os.makedirs("data", exist_ok=True)
    n = len(IND64)
    assert n == 64, f"expected 64 industries, got {n}"

    # ---- 1. Symmetric IO table -------------------------------------------
    print("Fetching naio_10_cp1750 ...")
    siot_raw = fetch("naio_10_cp1750", time=YEAR, geo=GEO,
                     unit="MIO_EUR", stk_flow="TOTAL")
    vals, dims = jsonstat_to_dict(siot_raw)
    print(f"  {len(vals)} cells, dims={dims}")

    def cell(row: str, col: str) -> float:
        # dims order: freq, unit, ind_ava, ind_use, stk_flow, geo, time
        v = vals.get(("A", "MIO_EUR", row, col, "TOTAL", GEO, YEAR))
        return float(v) if v is not None else 0.0

    Z = np.array([[cell(r, c) for c in IND64] for r in IND64])
    x = np.array([cell("P1", c) for c in IND64])

    zero_out = [IND64[j] for j in range(n) if x[j] <= 0]
    if zero_out:
        print(f"  WARNING zero-output industries: {zero_out}")
    xs = np.where(x > 0, x, 1.0)
    A = Z / xs  # column-wise: input per unit (MEUR) of output

    # ---- 2. Air emissions accounts ---------------------------------------
    print("Fetching env_ac_ainah_r2 ...")
    F = np.zeros((len(AIRPOL), n))
    em_raw = fetch("env_ac_ainah_r2", time=YEAR, geo=GEO, unit="THS_T",
                   airpol=list(AIRPOL))
    evals, edims = jsonstat_to_dict(em_raw)
    nace_codes = set(em_raw["dimension"]["nace_r2"]["category"]["index"])

    def emis(pol: str, code: str) -> float:
        v = evals.get(("A", pol, code, "THS_T", GEO, YEAR))
        return float(v) if v is not None else 0.0

    missing = [c for c in IND64
               if EMISSION_CODE.get(c, c) not in nace_codes
               and EMISSION_CODE.get(c) != "__L_MINUS_L68A__"]
    print(f"  emission NACE codes: {len(nace_codes)}; unmatched IND64: {missing}")

    for k, pol in enumerate(AIRPOL):
        for j, ind in enumerate(IND64):
            src = EMISSION_CODE.get(ind, ind)
            if src == "__L_MINUS_L68A__":
                F[k, j] = max(emis(pol, "L") - emis(pol, "L68A"), 0.0)
            else:
                F[k, j] = emis(pol, src)

    E = F / xs  # thousand tonnes per MEUR output

    # ---- 3. Ground-truth cradle-to-gate intensities -----------------------
    L = np.linalg.inv(np.eye(n) - A)
    M = E @ L  # (4 x 64) true total intensity per MEUR of final output

    # ---- 4. Build checks ---------------------------------------------------
    checks = {}
    # spectral radius of A must be < 1 for the Leontief series to converge
    checks["spectral_radius_A"] = float(max(abs(np.linalg.eigvals(A))))
    # mapped GHG total vs Eurostat published industry total (TOTAL row incl.
    # all NACE, excl. household rows if present under separate codes)
    # TOTAL in env_ac_ainah_r2 = all NACE industry activities (households
    # are reported separately under HH codes)
    industry_total = emis("GHG", "TOTAL")
    mapped = float(F[0].sum())
    if industry_total > 0:
        checks["ghg_mapped_vs_published_pct"] = 100 * (mapped / industry_total - 1)
        checks["ghg_published_industry_total_THS_T"] = industry_total
        checks["ghg_mapped_total_THS_T"] = mapped
    checks["zero_output_industries"] = zero_out
    checks["n_industries"] = n
    checks["n_manufacturing_targets"] = len(MANUF)

    np.savez_compressed(
        "data/matrices.npz", A=A, E=E, Z=Z, x=x, F=F, M_true=M,
        industries=np.array(IND64), manuf=np.array(MANUF),
        airpol=np.array(list(AIRPOL)),
    )
    with open("data/checks.json", "w") as f:
        json.dump(checks, f, indent=2)
    with open("data/industries.csv", "w") as f:
        f.write("code,output_MEUR,ghg_THS_T,true_GHG_intensity\n")
        for j, c in enumerate(IND64):
            f.write(f"{c},{x[j]:.1f},{F[0, j]:.1f},{M[0, j]:.6f}\n")

  
    print(json.dumps(checks, indent=2))
    print("Saved data/matrices.npz")


if __name__ == "__main__":
    main()
