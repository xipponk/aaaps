# AAAPS — AI-Augmented Academic Performance Simulation (v0.3)

A networked agent-based model of 240 undergraduate computer-science students across
six academic sections over an eight-semester degree, investigating how differential
access to generative AI tools interacts with individual ability, socioeconomic status,
and peer social networks to shape academic inequality and cognitive dependency.

## Model (v0.3)

The v0.3 model is a structural rewrite of the v0.2 flat, independent-agent model,
carried out in response to desk-rejection critiques. Key changes:

- **Networked population**: 240 agents in 6 sections, connected via a stochastic block
  model with ability and socioeconomic homophily (mean degree 6-10).
- **Three interaction channels**: material access sharing, normative legitimacy
  diffusion, and comparative aspiration adjustment.
- **Coupled continuous dynamics**: AI dependency `d`, metacognitive calibration error
  `c`, and retained ability `a_r` evolve through coupled difference equations, replacing
  the v0.2 hardcoded three-phase mechanism.
- **Five policy scenarios**: baseline (no AI), free market, universal access (temporary,
  with a permanent variant as robustness benchmark), mixed policy, and targeted subsidy.

## Repository layout

- `config/params.py` — parameter registry with [C]/[K]/[F] calibration tags
- `model/` — agents, network, tasks, and the Mesa-based `AaapsModel` scheduler
- `scenarios/` — scenario runners
- `analysis/` — Morris screening, Sobol GSA (free_market and targeted_subsidy), and the
  100-seed production comparison
- `docs/` — implementation brief and model notes
- `test_zero_interaction.py` — the zero-interaction verification check

## Verification and sensitivity analysis

- **Zero-interaction check**: with the network disabled, the model reproduces the v0.2
  baseline mechanics within stochastic bounds, confirming the interaction layer is the
  source of the new emergent behavior.
- **Two-stage GSA**: Morris elementary-effects screening (23 candidate parameters),
  then Sobol variance decomposition (12 retained parameters, N=512, 7,168 evaluations),
  run on both the free_market and targeted_subsidy scenarios.

## Running

```bash
pip install -r requirements.txt

python analysis/run_production.py               # 100-seed scenario comparison
python analysis/run_sobol.py                    # Sobol GSA, free_market
python analysis/run_sobol_targeted_subsidy.py   # Sobol GSA, targeted_subsidy
python analysis/run_morris_screening.py         # Morris screening (stage 1)
```

All parameters are read via `from config import params as P` and mutated at runtime by
the analysis scripts; do not use named imports in model code.

## Citation

If you use this model, please cite the accompanying paper:

Triyason, T. (2026). Equal Access, Unequal Benefit: A Networked Agent-Based Model of
AI Tool Access in Higher Education.

## License

MIT — see `LICENSE`.
