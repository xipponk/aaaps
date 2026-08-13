"""
model/model.py — AaapsModel (v0.3 Networked Redesign).

World container for AAAPS v0.3. Implements hybrid 2-stage scheduler,
3 interaction submodels (Normative Diffusion, Aspiration Adjustment, Access Market),
and data collection.
"""

from __future__ import annotations

import copy
import mesa
import networkx as nx
import numpy as np

from config.params import (
    N_STUDENTS,
    N_SECTIONS,
    STUDENTS_PER_SECTION,
    SES_RATIO,
    ABILITY_MEAN,
    ABILITY_STD,
    ABILITY_CLAMP,
    SR_ABILITY_WEIGHT,
    SR_NOISE_WEIGHT,
    BUDGET_PARAMS,
    CONFORMITY_BETA_A,
    CONFORMITY_BETA_B,
    PROSOCIALITY_BETA_A,
    PROSOCIALITY_BETA_B,
    P_VISIBLE,
    ETA,
    ETA_SELF,
    KAPPA,
    SHAREABLE_SEATS,
    STEPS_PER_SEMESTER,
    N_SEMESTERS,
    TOTAL_STEPS,
    COURSES,
    LAMBDA_LIFE,
)
from model.agents import StudentAgent
from model.network import generate_social_network
from model.tasks import TaskObject


class AaapsModel(mesa.Model):
    """AaapsModel v0.3 — Networked Agent-Based Model of CS students."""

    n_students: int
    scenario: str
    current_step: int
    current_semester: int
    social_network: nx.Graph

    def __init__(
        self,
        n_students: int = N_STUDENTS,
        scenario: str = "free_market",
        seed: int | None = None,
        zero_interaction_mode: bool = False,
    ) -> None:
        super().__init__(seed=seed)
        self.n_students = n_students
        self.scenario = scenario
        self.current_step = 0
        self.current_semester = 1
        self.zero_interaction_mode = zero_interaction_mode

        # 1. Instantiate 240 Agents across 6 Sections
        agent_list = []
        ses_choices = ['low', 'mid', 'high']
        ses_probs = [SES_RATIO['low'], SES_RATIO['mid'], SES_RATIO['high']]

        for uid in range(self.n_students):
            sec_id = uid // STUDENTS_PER_SECTION
            ses = str(self.random.choices(ses_choices, weights=ses_probs)[0])
            b_cfg = BUDGET_PARAMS[ses]
            budget = float(self.random.gauss(b_cfg['mean'], b_cfg['std']))

            ab_raw = float(self.random.gauss(ABILITY_MEAN, ABILITY_STD))
            ability = float(np.clip(ab_raw, ABILITY_CLAMP[0], ABILITY_CLAMP[1]))

            sr_raw = (ability / 100.0) * SR_ABILITY_WEIGHT + self.random.random() * SR_NOISE_WEIGHT
            sr = float(np.clip(sr_raw, 0.0, 1.0))
            hobby = float(self.random.random())

            conformity = float(self.random.betavariate(CONFORMITY_BETA_A, CONFORMITY_BETA_B))
            prosociality = float(self.random.betavariate(PROSOCIALITY_BETA_A, PROSOCIALITY_BETA_B))

            agent = StudentAgent(
                unique_id=uid,
                model=self,
                base_ability=ability,
                ses=ses,
                section_id=sec_id,
                monthly_budget=budget,
                self_regulation=sr,
                hobby_pull=hobby,
                conformity=conformity,
                prosociality=prosociality,
            )
            agent_list.append(agent)
            self.agents.add(agent)

        # 2. Network Construction (or Empty Graph if zero-interaction check)
        if self.zero_interaction_mode:
            self.social_network = nx.Graph()
            for a in agent_list:
                self.social_network.add_node(a.unique_id)
        else:
            np_rng = np.random.default_rng(seed if seed is not None else 42)
            self.social_network = generate_social_network(agent_list, np_rng)

    # =========================================================================
    # Step Pipeline: Hybrid 2-Stage Scheduler (Phase A -> B -> C -> D -> E)
    # =========================================================================

    def step(self) -> None:
        """Execute one daily step of the simulation."""
        self.current_step += 1
        self.current_semester = min(N_SEMESTERS, (self.current_step - 1) // STEPS_PER_SEMESTER + 1)

        # --- Phase A: Environment Update ---
        self._phase_a_env_update()

        # --- Phase B: Synchronous Social Update (Snapshot of t-1) ---
        if not self.zero_interaction_mode:
            self._phase_b_social_update()

        # --- Phase C: Asynchronous Individual Action ---
        self.agents.shuffle().do("step")

        # --- Phase D: Coupled Continuous State Update ---
        for agent in self.agents:
            if isinstance(agent, StudentAgent):
                agent.update_coupled_dynamics()

        # --- Phase E: Data Collection ---

    # -------------------------------------------------------------------------
    # Phase A: Environment Update
    # -------------------------------------------------------------------------

    def _phase_a_env_update(self) -> None:
        """Monthly budget/quota reset & task generation."""
        # Monthly reset every 30 days
        if (self.current_step - 1) % 30 == 0:
            for a in self.agents:
                if isinstance(a, StudentAgent):
                    a.budget_remaining = a.monthly_budget

        # Task generation per course & life task generator
        task_id_counter = self.current_step * 1000
        for a in self.agents:
            if not isinstance(a, StudentAgent):
                continue
            incoming = []
            for course in COURSES:
                if self.random.random() < course['lambda_tasks']:
                    task_id_counter += 1
                    d_min, d_max = course['difficulty_range']
                    diff = float(self.random.uniform(d_min, d_max))
                    ai_allowed = course['ai_allowed']
                    if ai_allowed == 'random_50pct':
                        ai_allowed = self.random.random() < 0.5

                    task = TaskObject(
                        task_id=task_id_counter,
                        task_type='academic_assignment',
                        difficulty=diff,
                        base_score=diff * 10.0,
                        deadline_remaining=int(course['deadline_days']),
                        deadline_total=int(course['deadline_days']),
                        ai_allowed=bool(ai_allowed),
                        course_id=course['id'],
                    )
                    incoming.append(task)

            # Life tasks
            if self.random.random() < LAMBDA_LIFE:
                task_id_counter += 1
                task = TaskObject(
                    task_id=task_id_counter,
                    task_type='life_task',
                    difficulty=5.0,
                    base_score=50.0,
                    deadline_remaining=3,
                    deadline_total=3,
                    ai_allowed=False,
                    course_id='LIFE',
                )
                incoming.append(task)

            a._incoming_tasks = incoming

    # -------------------------------------------------------------------------
    # Phase B: Synchronous Social Update (Submodels 7.7 - 7.9)
    # -------------------------------------------------------------------------

    def _phase_b_social_update(self) -> None:
        """Synchronous social update on a snapshot of t-1 agent state."""
        # 1. Take snapshot of t-1 attributes
        snapshot = {}
        student_agents: list[StudentAgent] = [a for a in self.agents if isinstance(a, StudentAgent)]
        
        for a in student_agents:
            snapshot[a.unique_id] = {
                'ai_tier': a.ai_tier,
                'ai_legitimacy': a.ai_legitimacy,
                'score_total': a.score_total,
                'ai_used_today': a._ai_used_today,
                'section_id': a.section_id,
                'prosociality': a.prosociality,
                'quota_balance': a.quota_balance,
            }

        agent_map = {a.unique_id: a for a in student_agents}

        # B1. Legitimacy Diffusion (Normative)
        for a in student_agents:
            nbrs = list(self.social_network.neighbors(a.unique_id))
            if not nbrs:
                continue

            obs_sum = 0.0
            weight_sum = 0.0
            for nbr_id in nbrs:
                w = self.social_network[a.unique_id][nbr_id]['tie_strength']
                if snapshot[nbr_id]['ai_used_today'] and self.random.random() < P_VISIBLE:
                    obs_sum += w
                weight_sum += w

            observed_frac = obs_sum / max(1e-6, weight_sum)
            u_self = 1.0 if a._ai_used_today else 0.0

            l_next = a.ai_legitimacy + ETA * a.conformity * (observed_frac - a.ai_legitimacy) + ETA_SELF * u_self * (1.0 - a.ai_legitimacy)
            a.ai_legitimacy = float(np.clip(l_next, 0.0, 1.0))

        # B2. Aspiration Adjustment (Comparative)
        for a in student_agents:
            nbrs = list(self.social_network.neighbors(a.unique_id))
            if not nbrs:
                continue

            peer_scores = [snapshot[nid]['score_total'] for nid in nbrs]
            weights = [self.social_network[a.unique_id][nid]['tie_strength'] for nid in nbrs]
            peer_signal = float(np.average(peer_scores, weights=weights))

            t_next = a.aspiration + KAPPA * (peer_signal - a.aspiration)
            a.aspiration = float(np.clip(t_next, 10.0, 100.0))

        # B3. Access Sharing Market (Material)
        for a in student_agents:
            a.ai_tier_effective = a.ai_tier
            a.borrowing_from = None
            a.shared_seats_out = 0

        # Section-level scarcity
        section_agents = {}
        for sec in range(N_SECTIONS):
            sec_members = [aid for aid, s in snapshot.items() if s['section_id'] == sec]
            n_tier2_ge = sum(1 for aid in sec_members if snapshot[aid]['ai_tier'] >= 2)
            scarcity = 1.0 - (n_tier2_ge / max(1.0, len(sec_members)))
            section_agents[sec] = float(np.clip(scarcity, 0.0, 1.0))

        demanders = [a for a in student_agents if a.ai_tier < 2 and a.ai_legitimacy > 0.3]
        suppliers = {a.unique_id: SHAREABLE_SEATS[a.ai_tier] for a in student_agents if a.ai_tier >= 2}

        for d in demanders:
            sec_scarcity = section_agents[d.section_id]
            nbrs = list(self.social_network.neighbors(d.unique_id))
            valid_suppliers = [nid for nid in nbrs if nid in suppliers and suppliers[nid] > 0]
            
            if not valid_suppliers:
                continue

            best_s = None
            best_p = -1.0
            for s_id in valid_suppliers:
                w = self.social_network[d.unique_id][s_id]['tie_strength']
                p_match = d.prosociality * w * sec_scarcity
                if p_match > best_p:
                    best_p = p_match
                    best_s = s_id

            if best_s is not None and self.random.random() < best_p:
                d.borrowing_from = best_s
                d.ai_tier_effective = max(d.ai_tier, 2)
                suppliers[best_s] -= 1
                agent_map[best_s].shared_seats_out += 1
