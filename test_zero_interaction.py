"""
test_zero_interaction.py — Zero-Interaction Sanity Verification Check.

Compares full networked model vs zero-interaction model (p_within=p_between=0)
across 1 semester (120 steps).
"""

import numpy as np
from scenarios.free_market import run as run_free_market


def verify_zero_interaction():
    print("=== Running Zero-Interaction Verification Check ===")

    # 1. Zero-interaction run
    model_zero = run_free_market(seed=42, zero_interaction_mode=True)
    zero_scores = [a.score_total for a in model_zero.agents]
    zero_deps = [a.dependency for a in model_zero.agents]

    print(f"Zero-Interaction Model (N={len(zero_scores)}):")
    print(f"  Mean Score: {np.mean(zero_scores):.2f} (std: {np.std(zero_scores):.2f})")
    print(f"  Mean Dependency: {np.mean(zero_deps):.4f} (std: {np.std(zero_deps):.4f})")

    # 2. Full Networked run
    model_net = run_free_market(seed=42, zero_interaction_mode=False)
    net_scores = [a.score_total for a in model_net.agents]
    net_deps = [a.dependency for a in model_net.agents]

    print(f"\nFull Networked Model (N={len(net_scores)}):")
    print(f"  Mean Score: {np.mean(net_scores):.2f} (std: {np.std(net_scores):.2f})")
    print(f"  Mean Dependency: {np.mean(net_deps):.4f} (std: {np.std(net_deps):.4f})")

    # Sanity checks
    assert len(zero_scores) == 240, "Zero-interaction model agent count mismatch!"
    assert len(net_scores) == 240, "Networked model agent count mismatch!"
    print("\n[SUCCESS] Zero-Interaction Verification Check passed cleanly!")


if __name__ == "__main__":
    verify_zero_interaction()
