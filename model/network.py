"""
model/network.py — Social Network generation for AAAPS v0.3.

Generates a static Stochastic Block Model across sections with SES and
ability homophily rewiring. Ensures network connectivity and target degree bounds.
"""

from __future__ import annotations

import networkx as nx
import numpy as np

from config import params as P


def generate_social_network(
    agents: list,
    rng: np.random.Generator,
    max_retries: int = 50,
) -> nx.Graph:
    """Generate the static social network graph for AAAPS v0.3."""
    n = len(agents)
    agent_map = {a.unique_id: a for a in agents}
    ids = [a.unique_id for a in agents]

    # Dynamically determine section sizes based on agent count
    n_sections = max(1, len(set(a.section_id for a in agents)))
    students_per_sec = n // n_sections if n_sections > 0 else n
    block_sizes = [students_per_sec] * n_sections
    
    # Adjust remainder if n not perfectly divisible
    remainder = n - sum(block_sizes)
    if remainder > 0 and block_sizes:
        block_sizes[-1] += remainder

    prob_matrix = np.full((n_sections, n_sections), P.SBM_P_BETWEEN)
    np.fill_diagonal(prob_matrix, P.SBM_P_WITHIN)

    for attempt in range(max_retries):
        # 1. Base SBM Graph
        sbm = nx.stochastic_block_model(
            block_sizes, prob_matrix, seed=int(rng.integers(0, 1_000_000))
        )
        G = nx.Graph()
        for u, v in sbm.edges():
            if u < len(ids) and v < len(ids):
                G.add_edge(ids[u], ids[v])

        # Ensure all nodes are present in G
        for node_id in ids:
            if not G.has_node(node_id):
                G.add_node(node_id)

        # 2. Homophily Rewiring (SES & Ability)
        edges = list(G.edges())
        for u, v in edges:
            a1, a2 = agent_map[u], agent_map[v]
            if a1.SES != a2.SES and rng.random() < P.HOMOPHILY_SES:
                same_ses = [
                    a.unique_id for a in agents
                    if a.SES == a1.SES and a.unique_id != u and not G.has_edge(u, a.unique_id)
                ]
                if same_ses:
                    new_v = rng.choice(same_ses)
                    G.remove_edge(u, v)
                    G.add_edge(u, new_v)
                    continue

            ability_diff = abs(a1.base_ability - a2.base_ability)
            if ability_diff > 20.0 and rng.random() < P.HOMOPHILY_ABILITY:
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
        k_bar = float(np.mean(degrees)) if degrees else 0.0
        if not (P.TARGET_K_BAR_RANGE[0] <= k_bar <= P.TARGET_K_BAR_RANGE[1]):
            continue

        # 4. Assign edge tie_strength ~ Beta(2,2)
        for u, v in G.edges():
            G[u][v]['tie_strength'] = float(rng.beta(P.TIE_STRENGTH_BETA_A, P.TIE_STRENGTH_BETA_B))

        return G

    # Fallback if max_retries exceeded
    p_fallback = min(1.0, 8.0 / max(1, n - 1))
    G = nx.erdos_renyi_graph(n, p=p_fallback, seed=int(rng.integers(0, 1_000_000)))
    mapping = {i: ids[i] for i in range(n)}
    G = nx.relabel_nodes(G, mapping)
    if not nx.is_connected(G):
        for i in range(n):
            G.add_edge(ids[i], ids[(i + 1) % n])
    for u, v in G.edges():
        G[u][v]['tie_strength'] = float(rng.beta(P.TIE_STRENGTH_BETA_A, P.TIE_STRENGTH_BETA_B))
    return G
