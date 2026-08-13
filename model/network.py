"""
model/network.py — Social Network generation for AAAPS v0.3.

Generates a static Stochastic Block Model across 6 sections with SES and
ability homophily rewiring. Ensures network connectivity and target degree bounds.
"""

from __future__ import annotations

import networkx as nx
import numpy as np

from config.params import (
    N_STUDENTS,
    N_SECTIONS,
    STUDENTS_PER_SECTION,
    SBM_P_WITHIN,
    SBM_P_BETWEEN,
    HOMOPHILY_SES,
    HOMOPHILY_ABILITY,
    TARGET_K_BAR_RANGE,
    TIE_STRENGTH_BETA_A,
    TIE_STRENGTH_BETA_B,
)


def generate_social_network(
    agents: list,
    rng: np.random.Generator,
    max_retries: int = 50,
) -> nx.Graph:
    """Generate the static social network graph for AAAPS v0.3.

    Parameters
    ----------
    agents : list
        List of StudentAgent instances (must have unique_id, section_id, SES, base_ability).
    rng : np.random.Generator
        Random number generator for reproducibility.
    max_retries : int
        Max attempts to build a connected graph within degree bounds.

    Returns
    -------
    nx.Graph
        Undirected graph where nodes are agent unique_ids and edges have attribute 'tie_strength'.
    """
    n = len(agents)
    agent_map = {a.unique_id: a for a in agents}
    ids = [a.unique_id for a in agents]

    # Block matrix for 6 sections
    block_sizes = [STUDENTS_PER_SECTION] * N_SECTIONS
    prob_matrix = np.full((N_SECTIONS, N_SECTIONS), SBM_P_BETWEEN)
    np.fill_diagonal(prob_matrix, SBM_P_WITHIN)

    for attempt in range(max_retries):
        # 1. Base SBM Graph
        sbm = nx.stochastic_block_model(
            block_sizes, prob_matrix, seed=int(rng.integers(0, 1_000_000))
        )
        G = nx.Graph()
        for u, v in sbm.edges():
            G.add_edge(ids[u], ids[v])

        # Ensure all nodes are present in G
        for node_id in ids:
            if not G.has_node(node_id):
                G.add_node(node_id)

        # 2. Homophily Rewiring (SES & Ability)
        edges = list(G.edges())
        for u, v in edges:
            a1, a2 = agent_map[u], agent_map[v]
            # SES homophily check
            if a1.SES != a2.SES and rng.random() < HOMOPHILY_SES:
                # Rewire to another same-SES candidate if possible
                same_ses = [
                    a.unique_id for a in agents
                    if a.SES == a1.SES and a.unique_id != u and not G.has_edge(u, a.unique_id)
                ]
                if same_ses:
                    new_v = rng.choice(same_ses)
                    G.remove_edge(u, v)
                    G.add_edge(u, new_v)
                    continue

            # Ability homophily check (if abilities are far apart)
            ability_diff = abs(a1.base_ability - a2.base_ability)
            if ability_diff > 20.0 and rng.random() < HOMOPHILY_ABILITY:
                similar_ability = [
                    a.unique_id for a in agents
                    if abs(a.base_ability - a1.base_ability) <= 15.0 and a.unique_id != u and not G.has_edge(u, a.unique_id)
                ]
                if similar_ability:
                    new_v = rng.choice(similar_ability)
                    G.remove_edge(u, v)
                    G.add_edge(u, new_v)

        # 3. Sanity Checks: Connectivity & Average Degree k_bar
        if not nx.is_connected(G):
            continue

        degrees = [d for _, d in G.degree()]
        k_bar = float(np.mean(degrees))
        if not (TARGET_K_BAR_RANGE[0] <= k_bar <= TARGET_K_BAR_RANGE[1]):
            continue

        # 4. Assign edge tie_strength ~ Beta(2,2)
        for u, v in G.edges():
            G[u][v]['tie_strength'] = float(rng.beta(TIE_STRENGTH_BETA_A, TIE_STRENGTH_BETA_B))

        return G

    # Fallback if max_retries exceeded: construct a connected graph with k_bar in bounds
    print(f"[Warning] SBM network generation hit max_retries ({max_retries}), using connected fallback.")
    G = nx.erdos_renyi_graph(n, p=0.035, seed=int(rng.integers(0, 1_000_000)))
    mapping = {i: ids[i] for i in range(n)}
    G = nx.relabel_nodes(G, mapping)
    if not nx.is_connected(G):
        # Force connectivity via backbone ring
        for i in range(n):
            G.add_edge(ids[i], ids[(i + 1) % n])
    for u, v in G.edges():
        G[u][v]['tie_strength'] = float(rng.beta(TIE_STRENGTH_BETA_A, TIE_STRENGTH_BETA_B))
    return G
