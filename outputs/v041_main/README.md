# outputs/v041_main

All files in this folder are v0.4.1 data. The `*_v04_*` file names (morris_v04_*, sobol_v04_*, production_v04_*) are historical: they come from the runner names (`run_*_v04.py`) and were not renamed. The older v0.4 outputs with the same base names are in `outputs/phase2/` and are a different dataset.

Provenance, read from the manifests in this folder (all five have git hash c1021d9, branch v0.4-recovery-fix, git_dirty false, params_hash f46db774430a4e21, LAMBDA_A = 0.00248):

| files | manifest | seeds |
|---|---|---|
| morris_v04_* | morris_v04_manifest.json | 2000-2002 (3 seeds per design point, 480 design points) |
| sobol_v04_free_market_* | sobol_v04_free_market_manifest.json | 3000 (one seed per design point) |
| sobol_v04_targeted_subsidy_* | sobol_v04_targeted_subsidy_manifest.json | 3000 (one seed per design point) |
| production_v04_* | production_v04_manifest.json | 0-99 |
| interaction_isolation_* | interaction_isolation_manifest.json | 0-99 |

These runs predate the benefit-ability family (commit 57fe46c); the family at k = 1 is bitwise identical to them.
