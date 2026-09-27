#!/usr/bin/env python3
"""Draw the full traced and grouped main-text influence diagrams in matplotlib.

Run: python3 -B model/scripts/make_influence_diagram.py
Only the two SVG/PNG figure pairs and the edge audit are written.
--audit-only checks source anchors and writes the inventory without rendering.
The full 47-link computational trace is retained. The single delay-to-violation
response annotation is not part of the model DAG.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import re
import subprocess
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "trr/manuscript/figures/fig_influence"
AUDIT = ROOT / "trr/reviews/round10/influence-diagram-edges.md"
M = "model/src/mtcpts/model.py"
P = "model/src/mtcpts/pathways.py"
C = "model/src/mtcpts/conflict.py"
V = "model/src/mtcpts/severity.py"
R = "model/scripts/review_reads.py"
D = "model/scripts/decision_outputs_s2.py"
F = "model/scripts/make_figures_trr_v12.py"
W = "model/scripts/welfare.py"
SU = "model/scripts/run_suite.py"
DIST = "model/src/mtcpts/distributions.py"
WIDTH_PT = 6.5 * 72
FONT = 9.0


@dataclass(frozen=True)
class Ref:
    path: str
    first: int
    last: int
    anchor: str

    def check(self):
        lines = (ROOT / self.path).read_text().splitlines()
        assert 0 < self.first <= self.last <= len(lines), self
        assert self.anchor in "\n".join(lines[self.first - 1:self.last]), self

    def md(self):
        return f"`{self.path}:{self.first}-{self.last}`"


def ref(path, first, last, anchor):
    return Ref(path, first, last, anchor)


@dataclass(frozen=True)
class Node:
    id: str
    label: str
    kind: str
    group: str
    quantities: str
    function: str
    refs: tuple[Ref, ...]
    priors: tuple[str, ...] = ()


NODES = [
    Node("control", "Control\nform", "decision", "Decisions",
         "Strategy name: S0 manual, S1a fixed-time signals, S1b monitored signals, S2 attended gated device. All arms are evaluated; this is a scenario choice, not an optimiser.",
         "run_cell", (ref(M, 252, 282, 'for name in STRATEGIES:'),)),
    Node("layout", "Section length;\nstop-line\nplacement", "decision", "Decisions",
         "Cell.section_m and stop-line placement define the section being controlled. Mutual sight is a site property, represented by Priors.d_sight_m and capped at section length in encounters. Placement affects the available sight supplied to the model; the code does not calculate sight from a geometric site plan.",
         "Cell; run_baseline_extras", (ref(M, 51, 54, 'section_m'), ref(SU, 247, 259, 'Priors(d_sight_m=Fixed(float(sig)))'))),
    Node("allred", "Programmed\nall-red", "decision", "Decisions",
         "Specified clearance-speed and buffer distributions, Priors.v_clear_kmh and Priors.clear_buffer_s. The programme samples designs; actual C1 is computed in cycle, not an independent freely chosen scalar.",
         "Priors; run_cell", (ref(M, 79, 82, 'v_clear_kmh'), ref(M, 164, 175, 'C1 = np.maximum'))),
    Node("context", "Demand;\nhours", "fixed", "Site context",
         "Cell.q_vph_dir, q_vps=q_vph_dir/3600, OPERATION_HOURS=8, veh_day_dir=q_vph_dir*OPERATION_HOURS. These are fixed context, not random or optimisation variables.",
         "Cell; run_cell", (ref(M, 48, 54, 'OPERATION_HOURS'), ref(M, 148, 150, 'q_vps'), ref(M, 242, 242, 'veh_day_dir'))),
    Node("motion", "Speed;\nacceleration", "uncertain", "Site context",
         "platoon_speed_kmh=v_p_kmh, v_p=v_p_kmh/3.6, a_veh_ms2=a_veh. The main run samples speed; a Fixed(speed) sweep is a separate design scenario. The posted speed limit is not the sampled operating speed.",
         "run_cell; run_baseline_extras", (ref(M, 158, 160, 'v_p_kmh'), ref(SU, 226, 234, 'platoon_speed_kmh=Fixed')),
         ("platoon_speed_kmh", "a_veh_ms2")),
    Node("timing", "Cycle timing\ninputs", "uncertain", "Release control",
         "sat_headway_s=h_sat; startup_lost_s=lost; s0_green_margin=margin; v_clear_kmh=v_clear; clear_buffer_s=buffer_s; t_confirm_s=t_confirm; f_cycle_a=f_a; f_cycle_b=f_b. Values drawn after the design specifications are supplied.",
         "run_cell", (ref(M, 161, 166, 'h_sat'), ref(M, 185, 186, 'f_a')),
         ("sat_headway_s", "startup_lost_s", "s0_green_margin", "v_clear_kmh", "clear_buffer_s", "t_confirm_s", "f_cycle_a", "f_cycle_b")),
    Node("sight", "Mutual\nsight", "uncertain", "Site context",
         "d_sight_m=d_sight. Its deterministic cap sight=min(d_sight,L) is carried in encounters. This node becomes fixed context in the sight sweep.",
         "run_cell", (ref(M, 222, 223, 'd_sight = draw'),), ("d_sight_m",)),
    Node("behaviour", "Violation\nrate", "uncertain", "Behaviour",
         "r_v0, r_v1a (also used by S1b), r_v2; selected r_v per vehicle facing STOP/red. Literature-adjusted rates are preserved exactly, not reduced again for apparent occupancy.",
         "run_cell", (ref(M, 210, 211, 'r_v0'), ref(M, 238, 238, 'r_v2'), ref(M, 265, 278, 'r_v = r_v1a')),
         ("r_v0", "r_v1a", "r_v2")),
    Node("response", "Entry timing;\nhold; response", "uncertain", "Red-running event chain",
         "w_occ, q_lead, w_onset, onset_window_s; p_detect_s0, p_detect_s1b, p_detect_s2 selected into p_det (zero for S1a); ttc50, s_ttc. ModelForm.rho and curve are fixed structural settings, primary rho=0 and logistic, carried here without treating them as sampled priors.",
         "run_cell; TreeParams; ModelForm", (ref(M, 212, 219, 'w_occ'), ref(M, 239, 239, 'p_det_s2'), ref(M, 265, 286, 'p_detect=p_det'), ref(C, 198, 216, 'rho: float')),
         ("w_occ", "q_lead", "w_onset", "onset_window_s", "p_detect_s0", "p_detect_s1b", "p_detect_s2", "ttc50", "s_ttc")),
    Node("injury", "Impact; mass;\noccupants", "uncertain", "Red-running event chain",
         "impact_speed_frac=f_imp, independent mass1_kg/mass2_kg=m1/m2, rounded occ1/occ2 from occupancy. Fixed Wang curve coefficients and units are carried in headon.",
         "run_cell", (ref(M, 220, 227, 'impact_speed_frac'),), ("impact_speed_frac", "mass_kg", "occupancy")),
    Node("sej", "Expert rates\nand severity", "uncertain", "Worker exposure and queue tail",
         "C.RE3_MTC and C.SEV3 -> paired re3_rate, sev3_p; C.RE1_Queue and C.SEV1 -> paired re1_rate, sev1_p. Reciprocals convert elicited inter-event passes into rates. Expert indices idx1/idx3 couple rate and severity within each pathway, not between pathways. PooledSEJ.sample_pairs preserves the pairs.",
         "run_cell; ExpertMixture.sample_with_index; PooledSEJ.sample_pairs", (ref(M, 193, 207, 're3_rate'), ref(DIST, 94, 100, 'f.ppf'), ref(DIST, 154, 160, 'self.re3_rate[idx]'))),
    Node("exposure", "Positions;\nplacement", "uncertain", "Worker exposure",
         "t_deploy_s=t_dep (both ends, install plus remove); enc_rate_vkm=enc; reach_alpha=alpha; offset_m=offset; offset_op_m=offset_op; deploy_speed_kmh=v_dep; fixed l_exposed_km=l_exp. Fixed reference controller position d_ref=0 or 1 m and two operators belong to the adopted operator comparison; one-operator and other reference offsets are alternatives.",
         "run_cell; review_reads.main", (ref(M, 229, 240, 't_dep'), ref(R, 180, 186, 'd_ref')),
         ("t_deploy_s", "enc_rate_vkm", "reach_alpha", "offset_m", "offset_op_m", "deploy_speed_kmh", "l_exposed_km")),
    Node("secondary", "Secondary\nharm chance", "uncertain", "Avoidance sensitivity",
         "p_evade_harm, conditional secondary harm-bearing event probability after successful avoidance; worker injury at operating speed is applied separately.",
         "run_cell", (ref(M, 221, 221, 'p_ev_harm'),), ("p_evade_harm",)),
    Node("cycle", "All-red;\ncycle; queues", "deterministic", "Release control",
         "L, transit, t_rest, sat_vps, C0, programmed C1, rho_q, stable, g_min, greens, clears; T, red, arr_cycle, stopped_red/n_queue, t_clear_q, stopped, f_stop, cycles_day, facing_day, stopped_day; DayContext and ConflictInputs (including startup lost time). Baseline S0 f_stop0 supplies re1_per_stop conversion. Demand, hours, headway and motion are retained in this bundle for downstream calls.",
         "run_cell; _cycle_quantities; traverse_time_from_rest", (ref(M, 129, 142, 'T ='), ref(M, 168, 191, 'C1'), ref(M, 244, 263, 'f_stop0'), ref(C, 58, 64, 't_acc'))),
    Node("entries", "Red / STOP\nentries", "deterministic", "Red-running event chain",
         "violations_per_day = facing_stop_per_day*r_v_facing. This is an entry count, not an independently generated Poisson draw.",
         "w5_terms", (ref(P, 94, 101, 'violations_per_day ='),)),
    Node("encounters", "Encounters;\ntime to meet", "deterministic", "Red-running event chain",
         "Branch time t_a, standing/onset type, weight; occupied, d_near, v_near; visible_occ/hidden_occ; entry weight w and normaliser acc[w]; next entry t_next/v0_next, meets, sep_e, hold, p_enter; p_conf, TTC and closing for A/H/B branches; weighted conf, blind, clear and safe accumulators; p_conflict, conflicts_per_day, p_blind, f_clear, p_safe_window. Carries entry count and full branch states to collisions, not just mean TTC.",
         "nearest_opposing; next_opposing_entry; w5_tree.branch; w5_terms", (ref(C, 117, 195, 'd_near'), ref(C, 286, 348, 'p_conf ='), ref(C, 367, 391, 'branch('), ref(P, 99, 99, 'conflicts_per_day'))),
    Node("collisions", "Collisions;\navoidances", "deterministic", "Red-running event chain",
         "q=q_fail(TTC); branch p_coll=p_conf*q*q (or rho*q+(1-rho)*q*q); acc[coll], acc[collv], acc[collt]; tree p_coll, p_evade; collisions_per_day, evasions_per_day; collision-weighted closing_ms and mean_ttc. Branch closing speeds and weighted collision terms continue into injury; no product of marginal medians is used.",
         "q_fail; p_collision_given_conflict; w5_tree.branch; w5_terms", (ref(C, 247, 262, 'return form.rho'), ref(C, 350, 362, 'p_coll ='), ref(C, 379, 388, 'p_evade'), ref(P, 100, 104, 'collisions_per_day'))),
    Node("headon", "Head-on\ninjury harm", "deterministic", "Red-running event chain",
         "closing_kmh=branch closing_ms*3.6*f_imp; momentum dv1/dv2; occupant p1/p2; p_dsi=1-(1-p1)^occ1*(1-p2)^occ2; acc[harm], p_harm; raw W5=Nentries*p_harm. Also holds l5=headon record/centre(S1a W5) and l5*W5 for each arm. centre is median or mean; l5 is shared across arms, not draw-by-draw fitting.",
         "w5_terms.severity_fn; p_event_dsi_headon; w5_tree; Data.delta", (ref(P, 89, 100, 'severity_fn'), ref(V, 79, 96, 'return 1.0'), ref(C, 355, 360, 'acc["harm"]'), ref(F, 177, 191, 'l5 ='))),
    Node("controller", "Controller\nstrike harm", "deterministic", "Worker exposure",
         "passes=2*veh_day_dir; raw strikes=passes*re3_rate; sev3=logistic(logit(sev3_p)+0.078*(v_p_kmh-50)); S0 W3=passes*re3_rate*sev3; l3=controller record/centre(S0 W3); calibrated reference l3*W3. Retains the S0 reference draw for the tied operator even when its direct ledger contribution is removed by a device.",
         "w3_events; sev_worker_at_speed; run_cell; Data.delta", (ref(P, 59, 71, 'passes ='), ref(V, 99, 122, 'logit ='), ref(M, 265, 282, 'strikes_day'), ref(F, 177, 191, 'l3 ='))),
    Node("operator", "Operator\nharm (tied)", "deterministic", "Worker exposure",
         "Adopted v1.2 S2 op=l3*W3_S0*exp(-reach_alpha*(offset_op_m-d_ref)); zero in S0/S1a/S1b. Same controller draw, same calibrated record, additional standing distance. Original W3r encroachment and independently scaled W3r are alternative formulas listed below, not substituted for this adopted edge.",
         "review_reads.main.tied; Data.delta", (ref(R, 180, 190, 'op ='), ref(F, 182, 190, 'mode == "tied"'))),
    Node("placement", "Placement /\nretrieval\nharm", "deterministic", "Worker exposure",
         "n_veh=2*q_vph_dir*t_dep/3600; lam=n_veh*enc*l_exp*exp(-alpha*offset); W4d=lam*p_worker(v_dep). Present in S1a/S1b/S2, zero in S0. Total on-foot time already includes both heads and both moves; operation hours are not multiplied again.",
         "w4d_events; run_cell", (ref(P, 123, 133, 'n_veh ='), ref(M, 265, 282, 'w4 ='))),
    Node("queue", "Queue-tail\nharm\n(raw / S)", "deterministic", "Queue-tail pathway",
         "re1_per_stop=re1_rate/max(f_stop0,1e-6); W1=stopped_day*re1_per_stop*sev1_p. Optional k1=all-cause record/centre(W1_S0) scales the queue term. The principal harm DIFFERENCE suppresses W1; raw totals include it. No operating-speed severity adjustment is applied to W1.",
         "run_cell; w1_events; review_reads.main; welfare.main", (ref(M, 244, 246, 're1_per_stop'), ref(P, 49, 56, 'return day.stopped_per_day'), ref(R, 54, 64, 'qt_scale'), ref(W, 81, 85, 'w1_scale_mean'))),
    Node("avoidance", "Avoidance\nharm (S)", "deterministic", "Avoidance sensitivity",
         "W5b=evasions_per_day*p_evade_harm*p_worker(v_p_kmh); raw term reported separately. Optional record sensitivity adds l5*(W5b_s-W5b_S0), sharing the head-on multiplier. Never in run_cell.results_h or the adopted principal comparison.",
         "w5b_band; decision_outputs_s2.main", (ref(P, 111, 120, 'return evasions_per_day'), ref(D, 223, 229, 'w5b[s]'))),
    Node("occupation", "Constructed worker\nreference", "evidence", "Calibration evidence",
         "STRIKE_REC, STRIKE_C: controller serious-harm reference levels built from recorded counts and assumed exposure. These fixed calibration inputs do not alter priors or cause strikes. Alternative fatal-to-serious ratios are reference sensitivities.",
         "module constants; record_reads; Data.delta", (ref(D, 29, 31, 'STRIKE_REC'), ref(D, 47, 54, 'l3, l5'), ref(F, 177, 180, 'l3 ='))),
    Node("crash", "Crash records\nhead-on;\nall causes", "evidence", "Calibration evidence",
         "HEADON_REC/HEADON_C serious-harm anchors; ALL_TTM_DSI_PER_OP_DAY all-cause reference for queue sensitivity. Collision-only record/gate is distinct and is documented below; it does not cause collisions or replace principal serious-harm matching.",
         "module constants; record_reads; review_reads.main", (ref(D, 29, 37, 'ALL_TTM_DSI_PER_OP_DAY'), ref(R, 54, 67, 'qt_scale'))),
    Node("harm", "Expected serious\nharm events /\noperation day", "outcome", "Outcomes",
         "Per-arm raw H=W1+W3+W5+W4d; adopted record-calibrated delta H_s=W4d_s+op_s-l3*W3_S0+l5*(W5_s-W5_S0). For S1a/S1b op=0; for S2 use tied op. Raw W1 and optional queue/avoidance restorations are labelled edges. P(delta H<0), quantiles, equivalence and break-even are summaries of these paired draws, not separate mechanisms.",
         "run_cell; review_reads.main.dh; Data.delta", (ref(M, 287, 292, 'results_h[name]'), ref(R, 58, 64, 'return (queue'), ref(F, 177, 191, 'return self.a[s]'))),
    Node("delay", "Delay\nvehicle-hours /\noperation day", "outcome", "Outcomes",
         "r=T-green; d1=r^2/[2*T*(1-q/sat)]; delay_h=2*q_vph_dir*hours*d1/3600. S2=S0 by cycle assumption. Optional non-clearing residual delay uses excess=max(q*T-sat*G,0), D=hours*3600, residual_vh=2*excess*D^2/(2*T)/3600. Delay does not feed serious harm.",
         "uniform_delay_per_vehicle_s; welfare.main; review_reads.main", (ref(W, 36, 39, 'return r * r'), ref(W, 59, 74, 'delay_h[s]'), ref(R, 225, 238, 'residual_vh'))),
]


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    route: str
    dependence: str
    refs: tuple[Ref, ...]
    label: str = ""


def edge(source, target, route, dependence, *refs, label=""):
    return Edge(source, target, route, dependence, refs, label)


EDGES = [
    edge("control", "behaviour", "behaviour", "Select r_v0, r_v1a (S1a and S1b), or r_v2.", ref(M, 265, 278, 'r_v = r_v1a')),
    edge("behaviour", "entries", "behaviour", "Nentries=facing_day*r_v_facing.", ref(P, 95, 95, 'r_v_facing')),
    edge("control", "cycle", "engineered", "Select greens[name], clears[name]; S2 copies the attended S0 plan.", ref(M, 187, 191, 'greens["S2"]'), ref(M, 252, 255, 'greens[name]')),
    edge("control", "response", "engineered", "Select p_det: S0 radio hold; S1a zero; S1b extension; S2 operator hold. Other response priors are shared.", ref(M, 265, 286, 'p_detect=p_det')),
    edge("control", "controller", "engineered", "Lane-standing controller term belongs to S0; direct term is removed in device arms. The S0 reference remains available for tied S2 exposure.", ref(M, 265, 280, 'w3 = np.zeros'), ref(F, 183, 191, 'operator = l3*self.w')),
    edge("control", "operator", "engineered", "Include tied operator exposure only for the attended S2 device.", ref(F, 182, 185, 'if s == "S2":')),
    edge("control", "placement", "engineered", "Zero in S0; physical head placement/retrieval in all three device arms.", ref(M, 265, 282, 'w4 = np.zeros')),
    edge("layout", "sight", "engineered", "Section length and stop-line placement determine which site sight is available. The code accepts that sight as d_sight_m, including fixed sight in the sweep; it caps effective sight at L. This is an input-specification relation, not a geometry solver or a decision to change the site's intrinsic visibility.", ref(SU, 253, 259, 'Priors(d_sight_m=Fixed'), ref(M, 222, 223, 'priors.d_sight_m'), ref(C, 290, 290, 's = np.minimum')),
    edge("layout", "cycle", "engineered", "Section length determines traverse times and programmed all-red.", ref(M, 168, 175, 'cell.section_m / (v_clear / 3.6)')),
    edge("layout", "encounters", "engineered", "Length sets occupancy, separation, transit and the cap on mutual sight.", ref(M, 258, 263, 'section_m=L'), ref(C, 286, 290, 's = np.minimum'), ref(C, 328, 331, 'sep_e =')),
    edge("allred", "timing", "computed", "Draw the specified clearance-speed and safety-buffer inputs. Actual all-red C1 is computed in cycle.", ref(M, 164, 165, 'priors.v_clear_kmh')),
    edge("timing", "cycle", "computed", "Headway -> saturation; confirmation -> C0; design speed/buffer -> C1; margins and scale factors -> greens. Startup lost time is passed to ConflictInputs.", ref(M, 170, 191, 'sat_vps ='), ref(M, 258, 263, 'startup_lost_s=lost')),
    edge("motion", "cycle", "computed", "Speed and acceleration determine the from-rest traverse and clearance floor.", ref(M, 158, 175, 't_rest = traverse_time_from_rest'), ref(C, 58, 64, 'v_max / a')),
    edge("context", "cycle", "computed", "Demand sets capacity ratio, green, queues and facing counts; hours set cycles/day and daily counts.", ref(M, 129, 142, 'cycles_day = OPERATION_HOURS'), ref(M, 178, 183, 'rho_q')),
    edge("cycle", "entries", "computed", "Use actual facing_STOP/red arrivals from this arm's red duration and cycle count.", ref(M, 254, 257, 'facing_stop_per_day=facing_day'), ref(P, 95, 95, 'day.facing_stop_per_day')),
    edge("cycle", "encounters", "computed", "Clearance, opposing green, queued count, demand, headway and start lag set release/occupancy and next entry, without changing the measured violation rate.", ref(M, 258, 263, 'clearance_s=clearance'), ref(C, 117, 195, 'ci.release_start_s'), ref(C, 333, 338, 't_a < rel')),
    edge("motion", "encounters", "computed", "Speed/acceleration set the vehicle trajectories, transit, mutual-discovery TTC and closing speed.", ref(C, 305, 341, 'ttc_A = time_to_close')),
    edge("sight", "encounters", "computed", "Cap sight at L; test visible/hidden occupancy and sighted next entry; compute TTC at discovery. Does not scale Nentries.", ref(C, 290, 290, 's = np.minimum'), ref(C, 301, 337, 'hidden_occ')),
    edge("response", "encounters", "computed", "Entry timing mixture and visibility weights plus hold and opposing-driver entry chance set weighted branch conflict probabilities.", ref(C, 311, 311, 'tp.w_occ'), ref(C, 333, 338, 'tp.q_lead'), ref(C, 367, 377, 'tp.w_onset')),
    edge("entries", "encounters", "computed", "Convert the integrated per-entry conflict probability to daily encounters; retain Nentries for all subsequent event counts.", ref(P, 95, 101, 'violations_per_day * tree["p_conflict"]')),
    edge("encounters", "collisions", "computed", "Branch TTC and p_conf determine collision/avoidance; weighted branch states and Nentries are retained, not replaced by average TTC.", ref(C, 344, 362, 'p_coll = p_conf * q * q'), ref(C, 379, 388, 'p_evade'), ref(P, 99, 101, 'collisions_per_day')),
    edge("response", "collisions", "computed", "ttc50/s_ttc set q_fail; fixed ModelForm.rho/curve govern alternatives.", ref(C, 247, 262, 'tp.ttc50'), ref(C, 350, 354, 'q_fail(ttc, tp, form)')),
    edge("collisions", "headon", "computed", "Weight each branch's injury probability by that branch's collision term before normalisation and multiplication by daily entries.", ref(C, 355, 360, 'w * p_coll * p_dsi'), ref(C, 381, 387, '"p_harm"'), ref(P, 97, 97, 'tree["p_harm"]')),
    edge("injury", "headon", "computed", "Retained closing speed, two masses and integer occupant counts determine at least one serious injury.", ref(P, 89, 92, 'impact_speed_frac'), ref(V, 79, 96, 'occ1 *')),
    edge("crash", "headon", "evidence", "l5=head-on serious-harm record/centre(S1a W5); same multiplier applied to all arms.", ref(F, 177, 191, 'l5 = h / centre'), ref(D, 47, 54, 'headon / w5_anchor')),
    edge("sej", "controller", "computed", "Paired per-pass strike rate and conditional severity anchor determine W3.", ref(P, 59, 71, 're3_per_pass * sev3')),
    edge("motion", "controller", "computed", "Transport the SEJ severity from 50 km/h to the sampled operating speed using the worker-curve logit slope.", ref(P, 69, 71, 'v_platoon_kmh'), ref(V, 120, 122, 'v_anchor_kmh')),
    edge("context", "controller", "computed", "Both-direction daily passes = 2*q_vph_dir*hours.", ref(M, 242, 242, 'OPERATION_HOURS'), ref(P, 69, 71, '2.0 * day.veh_per_day_dir')),
    edge("occupation", "controller", "evidence", "l3=controller serious-harm record/centre(S0 W3); preserve pairing and shape.", ref(F, 177, 191, 'l3 = c / centre(self.w)')),
    edge("controller", "operator", "computed", "Use that same calibrated controller draw in the adopted tied operator construction.", ref(R, 183, 185, 'l3_ * parts["S0"]["W3"]')),
    edge("exposure", "operator", "computed", "Additional distance enters exp[-alpha*(offset_op-d_ref)]. Two operators is the adopted configuration.", ref(R, 182, 185, 't["draw_offset_op_m"] - d_ref')),
    edge("exposure", "placement", "computed", "Deployment time, encroachment rate, exposed length, offset/reach and deployment-speed injury curve enter W4d.", ref(P, 123, 133, 'np.exp(-reach_alpha * offset_m)')),
    edge("context", "placement", "computed", "Both-direction hourly demand multiplies deployment duration, not the full operating day.", ref(M, 274, 275, '2.0 * cell.q_vph_dir'), ref(P, 131, 131, 't_deploy_s / 3600.0')),
    edge("cycle", "queue", "computed", "Own-arm stopped_day and S0 f_stop0 turn the per-approach SEJ rate into per-stop exposure.", ref(M, 244, 246, 're1_rate / np.maximum'), ref(P, 56, 56, 'day.stopped_per_day')),
    edge("sej", "queue", "computed", "Paired re1_rate and sev1_p determine queue-tail event risk; severity is not operating-speed transported.", ref(M, 245, 246, 're1_rate'), ref(P, 49, 56, 're1_per_stop * sev1')),
    edge("crash", "queue", "evidence", "Optional k1=all-cause serious-harm record/centre(S0 W1); this is a sensitivity scale, not a proven bound or a primary term.", ref(R, 54, 64, 'qt_scale'), ref(W, 81, 85, 'w1_scale_mean')),
    edge("collisions", "avoidance", "computed", "Successful evasions use (acc[conf]-acc[coll])/acc[w] times Nentries.", ref(C, 383, 386, 'acc["conf"] - acc["coll"]'), ref(P, 101, 101, 'evasions_per_day'), ref(P, 120, 120, 'evasions_per_day')),
    edge("secondary", "avoidance", "computed", "Multiply successful evasions by p_evade_harm.", ref(P, 120, 120, '* p_evade_harm')),
    edge("motion", "avoidance", "computed", "Apply worker injury probability at operating speed to the secondary event band.", ref(P, 120, 120, 'p_worker(v_platoon_kmh)')),
    edge("headon", "avoidance", "evidence", "Record sensitivity shares l5 with W5 (thin scaling link), anchored to W5 alone; raw W5b remains separately available.", ref(D, 223, 227, 'l5 * ((parts[s]["W5"] + w5b[s])')),
    edge("headon", "harm", "computed", "W5 enters raw H and calibrated paired differences.", ref(M, 291, 291, 'w5["events"]'), ref(F, 191, 191, 'l5*(self.v[s]-self.v["S0"])')),
    edge("controller", "harm", "computed", "Retain W3 in S0; subtract its calibrated reference in device-minus-manual delta H.", ref(M, 291, 291, 'w1 + w3'), ref(F, 191, 191, '- l3*self.w')),
    edge("operator", "harm", "computed", "Add the adopted tied S2 operator term.", ref(F, 183, 191, '+ operator')),
    edge("placement", "harm", "computed", "Add incremental placement/retrieval harm under each device.", ref(M, 291, 291, '+ w4'), ref(F, 191, 191, 'return self.a[s]')),
    edge("queue", "harm", "computed", "Raw H includes W1; principal delta H sets queue=0. Optional restoration adds k1*(W1_s-W1_S0), or the unscaled gap.", ref(M, 291, 291, 'w1 +'), ref(R, 58, 64, 'queue * (parts[s]["W1"]')),
    edge("avoidance", "harm", "computed", "Only the bounded sensitivity restores l5*(W5b_s-W5b_S0); excluded from raw results_h and principal delta H.", ref(D, 223, 229, 'w5b["S0"]')),
    edge("cycle", "delay", "computed", "T, green, demand/capacity ratio and daily arrivals determine delay; residual-queue sensitivity uses the same cycle inputs.", ref(W, 36, 39, 'q_vps / sat_vps'), ref(W, 59, 74, 'veh_day * d1'), ref(R, 230, 238, 'excess =')),
]


NOTES = """
## Reading the diagram

This is a grouped computational influence diagram of the current v1.2 model,
including the adopted tied operator construction. Arrows mean that at least one
quantity in the source bundle is an input to a quantity in the target bundle.
They do not assert that every member influences every member. Detailed formulas
below delimit each arrow. Chance nodes contain joint parameter bundles, not
claims of independence within a bundle. No information arcs into decisions,
utility maximisation, or fitted causal effect of control form is asserted.

Rectangles are specified design scenarios; ovals contain sampled inputs;
double ovals contain computations (including fixed site context); hexagons are
outputs; shaded notes are external evidence. Thick solid arrows identify the
engineered control/design route, dashed arrows identify the measured-entry-rate
route, thin solid arrows are subsequent computations, and dotted arrows mark only the requested plausible response outside the model. Record scaling uses thin solid arrows from folded notes. S means a sensitivity only. The raw queue term is included in
the package total but suppressed in the principal paired comparison.

The programmed all-red is **C1 in the release/cycle node**, computed as
`max(L/(v_clear/3.6)+buffer, t_rest)`. The all-red decision rectangle represents
its design specification, not a free `C1` argument that the code does not have.
`Priors` accepts distributions, including `Fixed`; design speed and buffer are
sampled across stated ranges in the principal analysis. The layout rectangle specifies section length and stop-line placement. Mutual sight belongs to site context; placement affects the sight available over that section. The model takes available sight as an input rather than solving site geometry. Operating speed is a chance node in the principal analysis and a
fixed design input in the separately implemented speed sweep. No computational arrow from all-red, sight or speed to the measured violation rate exists in the code. The single dotted annotation must not be read as a fitted dependency. Programmed all-red enters cycle timing through E11 and E12, and cycle-dependent delay is computed by E47. Only the waiting-to-violation response U1 is absent from the model.

The behavioural arrows select a form-specific literature prior and multiply it
by the count of vehicles facing red. They do not demonstrate a randomised causal
effect. S1a and S1b have the same violation-rate draw. Engineered control changes
release/hold, removes the lane-standing controller contribution, introduces
placement/retrieval exposure, and retains an off-road operator in S2.

## Fine-grained calculations inside the merged nodes

The following is the quantity-level expansion of the visible graph. Code
temporaries implementing clamps, masks, quadrature indices and unit conversions
are included in the relevant formula family rather than depicted as extra nodes.

| Visible node | Quantity and its computed parents | Code/function |
|---|---|---|
| context | `q_vps=q_vph_dir/3600`; `veh_day_dir=q_vph_dir*OPERATION_HOURS` | model.py run_cell:149,242 |
| motion, timing, sight, behaviour, response, injury, exposure, secondary | Each named draw is `dist.sample(rng.random(n_iter))`; `v_p=v_p_kmh/3.6`; occupant draws are rounded to integers. Distribution family parameters are supplied by `Priors` (mirrored in priors.toml). | model.py run_cell:152-166,185-186,210-240; distributions.py sampling classes |
| sej | Shared `idx1` couples RE1/SEV1, `idx3` couples RE3/SEV3; rates are reciprocal RE draws. Pooled sampling selects one paired row per pathway. There is no RE1 -> RE3 or frequency -> severity causal arrow. | model.py run_cell:193-207; distributions.py:94-100,154-160 |
| cycle | `t_acc=v/a`, `d_acc=0.5*v*t_acc`; `t_rest=sqrt(2L/a)` if L<=d_acc, otherwise `t_acc+(L-d_acc)/v`; `transit=L/v` | conflict.py traverse_time_from_rest:58-64; model.py:168-170 |
| cycle | `C0=t_rest+t_confirm`; `C1=max(L/(v_clear/3.6)+buffer,t_rest)`; `sat_vps=1/h_sat`; `rho_q=q_vps/sat_vps`; stable iff `2*rho_q<1` | model.py run_cell:171-180 |
| cycle | `g_min(C)=2*rho_q*C/(1-2*rho_q)` on stable draws; `g0=margin*g_min(C0)`; `g1a=f_a*margin*g_min(C1)`; `g1b=f_b*margin*g_min(C1)`; S2 copies S0 | model.py run_cell.g_min:182-191 |
| cycle | `T=2g+2C`; `red=g+2C`; `arr_cycle=q*T`; `stopped_red=q*red`; `t_clear_q=min(stopped_red/(sat-q),g)`; `stopped=stopped_red+q*t_clear_q`; `f_stop=clip(stopped/arr_cycle,0,1)` | model.py _cycle_quantities:129-138 |
| cycle | `cycles_day=hours*3600/T`; `facing_day=2*q*red*cycles_day`; `stopped_day=2*stopped*cycles_day`; `n_queue=round(stopped_red)`; `rel=C+startup_lost_s`; `green_end=C+g` | model.py:139-142,254-263; conflict.py ConflictInputs:102-114, nearest_opposing:128-132 |
| encounters | `s=min(d_sight,L)`; `ow=min(onset_window,R)`; midpoint quadrature `u=(arange(n_grid)+0.5)/n_grid`. Onset: `t_a=u*ow`, moving at v, weight `w_onset/n_grid`. Standing: `t_a=ow+u*(R-ow)`, from rest, weight `(1-w_onset)/n_grid`. | conflict.py w5_tree:286-295,367-377 |
| encounters | Nearest queued vehicle: `j_lo=ceil((t-rel-t_rest)/h)`, `j_hi=min(floor((t-rel)/h),n_q-1)`; occupancy if valid indices. Entry time `t_q=rel+j_q*h`; position `x_q=L-accel_distance(t-t_q,a,v)`; speed `accel_speed(t-t_q,a,v)`. | conflict.py nearest_opposing:128-144 |
| encounters | Free arrivals: `t_clear=rel+n_q*h`, `spacing=1/q`; index bounds use `(t-t_clear-tau)/spacing-0.5` and `(t-t_clear)/spacing-0.5`. Entry `t_k=t_clear+(k_lo+0.5)*spacing`; valid before green_end. `x_f=L-v*(t-t_k)`. Select nearest valid queued/free vehicle -> occupied, d_near, v_near. | conflict.py nearest_opposing:146-163 |
| encounters | Next queued index is zero before rel, otherwise `floor((t-rel)/h)+1`; next free index is `ceil((t-t_clear)/spacing-0.5)` clipped to zero and advanced if necessary. Select earlier valid crossing -> `t_next,v0_next`. | conflict.py next_opposing_entry:173-195 |
| encounters | Visible occupancy iff occupied and d_near<=s; hidden otherwise. `w=where(visible,w_occ*clip(d_near/s,0,1),1)*type_weight`. Weights re-time entries and are normalised; they do not change the measured count. | conflict.py w5_tree.branch:301-311 |
| encounters | Visible branch uses time_to_close(d_near,violator speed,opposing speed,a,v). Hidden branch advances speeds to the sight line, then closes min(d_near,s). Clear-at-entry branch tests `t_next<t_a+transit_v`, computes separation after that delay, applies pre-release hold and sight-conditioned opposing entry. | conflict.py w5_tree.branch:314-341 |
| encounters | `hold=where(t_a<rel,p_detect,0)`; `p_enter=where(sep_e<=s,q_lead*clip(sep_e/s,0,1),1)`; `p_conf_B=where(meets,(1-hold)*p_enter,0)`; `p_conf=where(occupied,1,p_conf_B)`; select TTC/closing by branch. | conflict.py w5_tree.branch:333-348 |
| encounters | time_to_close solves accelerating closure then constant-speed closure: `b=v1+v2_0`, `disc=b^2+2*a*sep`, `T_acc=(-b+sqrt(disc))/a`, cap time `(vmax-v2_0)/a`, then cruise if needed. Acceleration distance is piecewise `0.5*a*t^2` or `d_acc+vmax*(t-t_acc)`; speed=min(a*t,vmax). | conflict.py accel_distance/accel_speed/time_to_close:46-78 |
| collisions | Primary failure `q=1/(1+exp((TTC-ttc50)/s_ttc))`; `p_coll=p_conf*q^2`. Alternatives replace curve or use `p_conf*(rho*q+(1-rho)*q^2)`. Retain branch closing speeds; successful avoidance is conflict minus collision. | conflict.py q_fail/p_collision_given_conflict:247-262; branch:350-354 |
| encounters, collisions, headon | Accumulate `w`, `w*p_conf`, `w*p_coll`, `w*p_coll*p_dsi`, collision-weighted closing/TTC and blind/clear/safe diagnostics. Divide conf/coll/harm by sum(w); divide collision-weighted speeds by sum(w*p_coll). `p_evade=(acc_conf-acc_coll)/acc_w`. Multiply the event probabilities by Nentries to obtain daily counts. | conflict.py:357-391; pathways.py w5_terms:95-107 |
| headon | `closing_kmh=3.6*closing_ms*f_imp`; `dv1=closing*m2/(m1+m2)`, `dv2=closing*m1/(m1+m2)`; logistic occupant curves in mph; event injury `1-(1-p1)^occ1*(1-p2)^occ2`. Evaluated inside each branch integral, not at mean closing speed. | pathways.py severity_fn:89-92; severity.py:23-26,50-55,79-96 |
| controller | `passes=2*veh_day_dir`; `strike_count=passes*re3_rate`; anchored severity `logistic(logit(sev3_p)+0.078*(v-50))`; `W3=passes*re3_rate*sev3(v)` | pathways.py w3_events:59-71; severity.py:99-122; model.py:268 |
| placement | `N=2*q_vph_dir*t_dep/3600`; strikes=`N*enc*l_exp*exp(-alpha*offset)`; harm=strikes*worker_curve(v_dep). The worker curve is logistic(-4.6+0.078*v). | pathways.py w4d_events:123-133; severity.py:19-20,30-31,42-47 |
| operator | Adopted `op=l3*W3_S0*exp(-alpha*(offset_op-d_ref))`; depends on the controller's frequency, severity, speed and calibration through the same draw. No additional operating-day multiplier or independently sampled operator injury severity. | review_reads.py main.tied:180-190; make_figures_trr_v12.py Data.delta:177-191 |
| queue | `re1_per_stop=re1_rate/max(f_stop0,1e-6)` from this cell's S0 profile; `W1=stopped_day*re1_per_stop*sev1_p` | model.py:244-246,288; pathways.py w1_events:49-56 |
| avoidance | `W5b=N_evasions*p_evade_harm*worker_curve(v)`; optional record restoration uses the same l5 as head-on harm | pathways.py w5b_band:111-120; decision_outputs_s2.py:223-229 |
| controller, headon, queue | `l3=record_strike/centre(W3_S0)`; `l5=record_headon/centre(W5_S1a)`; optional `k1=record_allcause/centre(W1_S0)`. Median/mean matching are alternatives; each factor is constant across draws and arms. | make_figures_trr_v12.py Data.delta:177-191; welfare.py:63-69,81-85 |
| harm | Raw arm H and calibrated paired delta H are expanded in the node inventory. Finite paired draws yield P(delta H<0), Wilson intervals, quantiles and equivalence fractions; break-even divides removed baseline harm by the linear device violation coefficient. | model.py:291-317,324-336,352-423; review_reads.py:58-64,124-153; make_figures_trr_v12.py Data.delta/summary:177-202 |
| delay | `d1=(T-g)^2/(2*T*(1-q/sat))`; `D=hours*3600`; `veh_day=2*q_vph_dir*hours`; `delay_h=veh_day*d1/3600`. Optional residual queue adds `2*max(q*T-sat*G,0)*D^2/(2*T)/3600`. | welfare.py:36-39,59-74; review_reads.py:225-238 |

## Alternatives, checks and boundaries not drawn as extra mechanisms

* **Original operator encroachment:** `passes=4*veh_day_dir`,
  `strikes=passes*enc*l_exp*exp(-alpha*offset_op)`,
  `W3r=strikes*p_worker(v)` in pathways.py `w3r_operator_events:136-150`,
  selected in model.py `run_cell:270-275`. It would add direct context, motion
  and exposure -> operator edges and remove controller -> operator. The primary
  figure uses the later v1.2 tied construction, not this original package term.
* **Independent operator calibration:** decision_outputs_s2.py:238-257 and
  variant_operator_reference.py:31-69 strip/reapply offsets, divide the record
  by the median reference exposure and scale W3r. A one-operator alternative
  halves W3r. These are alternatives to the adopted operator formula, not
  additional harms to add to it.
* **Collision record gate:** run_suite.py `validity_gates:90-151` compares
  median S1a/S2 collision counts, collision-per-entry and S0 serious harm with
  external acceptance bands. A check does not alter its tested quantity, so
  there is no invented record -> collision-frequency causal arrow. The
  collision-matched alternative explicitly computes
  `l5c=COLLISION_REC/median(S1a collisions)` in review_reads.py:199-207.
  The main diagram's record arrow uses the manuscript's adopted serious-harm
  matching. The occupational gate likewise does not redraw the strike prior.
* **Dangerous device fault:** pathways.py `w6_band:153-156` is a dormant helper
  (`fault_rate_per_day*p_conflict_fault*p_dsi_event`). There is no production
  caller, sampled fault prior or ledger contribution. It cannot defensibly be
  drawn as an active pathway. Release errors are a separate equalising-rate
  diagnostic (review_reads.py:164-178), not a generated harm term. Slow lawful
  vehicles, common site risks and equipment/labour costs are not computed here.
* **Inactive helper module:** cycle.py supplies scalar cycle utilities and
  tests; run_cell uses its own vectorised `_cycle_quantities`, so no extra
  opposing-occupancy fraction is multiplied into the head-on chain. Likewise
  severity.py `braked_speed`, `headon_delta_vs` and `implied_strike_speed_kmh`
  are not the production injury route; production uses retained branch closing
  speed, `headon_delta_vs_from_closing` and the anchored worker curve.
* **Reported statistics and pricing:** random seed, Monte Carlo size,
  quadrature count, finite masks, PRCC/bootstrap ranks, posterior quantiles,
  practical equivalence margin and reporting ratios are numerical/reporting
  controls, not additional physical causes. Welfare pricing is downstream of
  the two displayed outcomes, using monetary values in welfare-values.toml;
  it does not feed either safety or delay. PooledSEJ.d15_multiplier is loaded
  for release compatibility but is not consumed by run_cell.

No active adopted harm dependence was left without a bundle. The boundaries
above distinguish alternate or inactive formulas from missing dependencies.
"""


def validate():
    ids = {n.id for n in NODES}
    assert len(ids) == len(NODES)
    assert len({(e.source, e.target) for e in EDGES}) == len(EDGES)
    for item in [*NODES, *EDGES]:
        for source in item.refs:
            source.check()
    children = {n: [] for n in ids}
    indegree = dict.fromkeys(ids, 0)
    for e in EDGES:
        assert e.source in ids and e.target in ids
        children[e.source].append(e.target)
        indegree[e.target] += 1
    queue = [n for n, degree in indegree.items() if degree == 0]
    visited = []
    while queue:
        source = queue.pop()
        visited.append(source)
        for target in children[source]:
            indegree[target] -= 1
            if not indegree[target]:
                queue.append(target)
    assert len(visited) == len(ids), "Dependency graph contains a cycle"
    tree = ast.parse((ROOT / M).read_text())
    priors = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Priors")
    fields = {n.target.id for n in priors.body if isinstance(n, ast.AnnAssign)}
    covered = [p for node in NODES for p in node.priors]
    assert set(covered) == fields, (fields - set(covered), set(covered) - fields)
    assert len(covered) == len(set(covered)), "A sampled prior belongs in exactly one bundle"
    assert not re.search("[\u2013\u2014]", "".join(n.label for n in NODES) + NOTES)
    # Geometry/release never changes the measured-entry-rate node.
    assert {e.source for e in EDGES if e.target == "behaviour"} == {"control"}
    return fields


# The dotted response is explicitly outside the traced computational graph.
# Existing cycle -> delay remains E47; waiting -> violation is not evaluated.
RESPONSES = [
    edge("delay", "behaviour", "unmodelled",
         "Longer waits may raise the violation rate. Plausible response only; no response function, coefficient or harm contribution is implemented."),
]
STYLES = {
    "engineered": (1.65, "-"),
    "behaviour": (1.1, (0, (4, 2.5))),
    "computed": (.6, "-"),
    "evidence": (.6, "-"),
    "unmodelled": (1.05, (0, (1, 2.2))),
}


@dataclass(frozen=True)
class Glyph:
    id: str
    label: str
    kind: str
    x: float
    y: float
    w: float
    h: float
    members: tuple[str, ...] = ()


@dataclass(frozen=True)
class Arrow:
    id: str
    source: str
    target: str
    route: str
    points: tuple[tuple[float, float], ...]
    trace: tuple[str, ...]
    meaning: str


MAIN_NODES = [
    Glyph("control", "Control\nform", "decision", 39, 248, 70, 28, ("control",)),
    Glyph("layout", "Section length;\nstop-line\nplacement", "decision", 259, 201, 78, 40, ("layout",)),
    Glyph("allred", "Programmed\nall-red", "decision", 174, 204, 70, 28, ("allred",)),
    Glyph("sight", "Mutual\nsight", "uncertain", 338, 204, 64, 31, ("sight",)),
    Glyph("site", "Demand, hours;\nspeed", "uncertain", 124, 140, 88, 35, ("context", "motion")),
    Glyph("crash", "Constructed crash\nreference", "evidence", 374, 278, 87, 25, ("crash",)),
    Glyph("occupation", "Constructed worker\nreference", "evidence", 114, 89, 90, 27, ("occupation",)),
    Glyph("behaviour", "Violation\nrate", "uncertain", 118, 248, 57, 32, ("behaviour",)),
    Glyph("entries", "Entries", "deterministic", 180, 248, 53, 32, ("entries",)),
    Glyph("encounters", "Entry timing;\nencounters", "deterministic", 245, 248, 65, 32, ("encounters",)),
    Glyph("collisions", "Collisions", "deterministic", 313, 248, 58, 32, ("collisions",)),
    Glyph("headon", "Head-on\nharm", "deterministic", 374, 248, 53, 32, ("headon",)),
    Glyph("worker", "Controller strike harm\nAttended-device operator harm\nPlacement and retrieval harm", "deterministic", 287, 143, 201, 47,
          ("controller", "operator", "placement")),
    Glyph("queue", "Queue-tail harm", "deterministic", 260, 92, 111, 28, ("queue",)),
    Glyph("harm", "Expected serious\nharm events per\noperation day", "outcome", 415, 193, 84, 56, ("harm",)),
    Glyph("cycle", "Cycle timing", "deterministic", 292, 64, 81, 26, ("cycle",)),
    Glyph("delay", "Delay", "outcome", 424, 64, 62, 28, ("delay",)),
]


def main_arrows():
    """Every connector ends on a named node; trace IDs retain the full mapping."""
    glyphs = {g.id: g for g in MAIN_NODES}

    def a(i, source, target, route, bends, trace, meaning):
        # Clip each end to the actual node outline, including off-centre ports.
        middle = tuple(bends)
        start = boundary(glyphs[source], middle[0] if middle else (glyphs[target].x, glyphs[target].y))
        end = boundary(glyphs[target], middle[-1] if middle else (glyphs[source].x, glyphs[source].y))
        return Arrow(f"M{i:02}", source, target, route, (start, *middle, end), tuple(trace), meaning)

    return [
        a(1, "control", "behaviour", "behaviour", [], ["E01"], "Select the form-specific converted entry estimate."),
        a(2, "behaviour", "entries", "behaviour", [], ["E02"], "Rate multiplied by vehicles facing STOP/red."),
        a(3, "control", "encounters", "engineered", [(82,241),(82,226),(224,226),(224,235)], ["E03","E04","E16","E19"], "Control form selects release and hold; the grouped route terminates at encounters."),
        a(4, "control", "worker", "engineered", [(39,179),(201,179),(201,157)], ["E05","E06","E07"], "Select controller, tied operator and placement contributions."),
        a(5, "layout", "sight", "engineered", [], ["E08"], "Section length and stop-line placement affect the site sight available to the model."),
        a(6, "layout", "encounters", "engineered", [(267,227)], ["E09","E10","E16"], "Section length determines clearance and opposing trajectories, hence encounters."),
        a(7, "allred", "encounters", "engineered", [(174,222),(250,222)], ["E11","E12","E16"], "Programmed all-red determines opposing release timing and encounters."),
        a(8, "site", "encounters", "computed", [(136,161),(136,224),(232,224)], ["E13","E14","E17"], "Demand, hours, speed and acceleration enter cycle and encounter calculations; no direct violation-rate adjustment."),
        a(9, "sight", "collisions", "computed", [(313,222)], ["E18","E21"], "Available mutual sight determines discovery time and time to avoid collision; the full trace carries this through encounter branch TTC."),
        a(22, "sight", "encounters", "computed", [(303,224),(281,224),(281,269),(245,269)], ["E18"], "Sight weights entry times, selects encounters and conditions opposing release."),
        a(10, "entries", "encounters", "computed", [], ["E20"], "Retain daily entries through branch calculations."),
        a(11, "encounters", "collisions", "computed", [], ["E21"], "Branch encounters and time to meet determine collision/avoidance probability."),
        a(12, "collisions", "headon", "computed", [], ["E23"], "Apply branch-specific injury probabilities."),
        a(13, "crash", "headon", "evidence", [], ["E25"], "Scale head-on serious harm to a reference built from recorded counts and assumed exposure."),
        a(14, "site", "worker", "computed", [], ["E27","E28","E33"], "Speed transports controller severity; demand and hours scale exposure. Placement uses demand and duration, not full-day hours."),
        a(15, "occupation", "worker", "evidence", [(192,89),(192,130)], ["E29"], "Apply the constructed occupational reference; tied operator inherits that same draw. Placement keeps its encroachment scale."),
        a(16, "headon", "harm", "computed", [(415,248)], ["E41"], "Record-scaled head-on contribution."),
        a(17, "worker", "harm", "computed", [(404,143)], ["E42","E43","E44"], "All three worker contributions with their arm-specific signs."),
        a(18, "site", "queue", "computed", [(181,122),(181,92)], ["E14","E34"], "Demand/cycle counts scale stopped-vehicle exposure; the expert rate/severity remain within the queue bundle."),
        a(19, "cycle", "delay", "computed", [], ["E47"], "The model computes delay from cycle timing, including the programmed all-red."),
        a(20, "allred", "cycle", "computed", [(58,204),(58,54),(244,54)], ["E11","E12"], "Programmed all-red enters cycle timing as modelled; this is a computed link."),
        a(21, "delay", "behaviour", "unmodelled", [(465,64),(465,293),(118,293)], ["U1"], "One continuous peripheral arrow: longer waits may raise violations (not in the model)."),
    ]


# Every original node is retained in the supplement. Positions are in points
# on a fixed 6.5-inch page; no Graphviz, layout engine or font rescaling.
FULL_POS = {
    "control": (42,456,76,31), "layout": (42,402,76,43),
    "allred": (42,518,76,32), "context": (42,242,73,35),
    "motion": (136,402,88,36), "timing": (138,518,85,36),
    "sight": (140,456,76,36), "behaviour": (130,348,70,36),
    "response": (242,456,103,39), "injury": (350,456,90,37),
    "sej": (140,242,82,39), "exposure": (140,170,87,38),
    "secondary": (236,116,85,36), "cycle": (244,518,104,41),
    "entries": (212,348,70,36), "encounters": (294,348,82,39),
    "collisions": (388,348,89,39), "headon": (388,288,83,38),
    "controller": (242,242,98,40), "operator": (336,224,82,40),
    "placement": (342,170,99,44), "queue": (342,104,99,46),
    "avoidance": (388,56,87,35), "occupation": (242,290,102,30),
    "crash": (292,400,88,43), "harm": (424,232,85,58),
    "delay": (432,518,67,39),
}


def full_nodes():
    # The main inventory's long labels are shortened without changing bundles.
    labels = {"headon":"Head-on harm", "queue":"Queue-tail harm\n(raw / sensitivity)",
              "placement":"Placement and\nretrieval harm", "operator":"Tied operator\nharm",
              "harm":"Expected serious\nharm events per\noperation day", "delay":"Delay",
              "avoidance":"Avoidance harm\n(sensitivity)", "context":"Demand; hours",
              "collisions":"Collisions;\navoidances", "crash":"Constructed references\nhead-on; all causes"}
    return [Glyph(n.id, labels.get(n.id,n.label), n.kind, *FULL_POS[n.id], (n.id,)) for n in NODES]


def boundary(g, toward):
    """Exact ellipse or rectangle intersection for an ordinary connector."""
    import math
    dx, dy = toward[0]-g.x, toward[1]-g.y
    if not dx and not dy:
        raise ValueError(g.id)
    if g.kind in ("uncertain", "deterministic", "fixed"):
        t = 1 / math.sqrt((dx/(g.w/2))**2 + (dy/(g.h/2))**2)
    elif g.kind == "outcome":
        cut = min(9, g.w*.2)
        t = min((g.h/2)/abs(dy) if dy else float("inf"),
                (g.w/2)/(abs(dx) + 2*cut/g.h*abs(dy)))
    else:
        t = min(g.w/2/abs(dx) if dx else float("inf"),
                g.h/2/abs(dy) if dy else float("inf"))
    return g.x+dx*t, g.y+dy*t


def full_arrows(glyphs):
    """Route the complete trace around the explicitly placed node rectangles.

    The grid router only chooses connector bends, never node positions or
    scientific dependencies. Crossings are permitted in the complete trace;
    white casings distinguish them from joins. All routes avoid unrelated nodes.
    """
    import heapq
    import math
    import numpy as np
    by_id = {g.id:g for g in glyphs}
    step = 2
    nx, ny = 233, 285
    blocked = np.zeros((nx,ny),dtype=bool)
    heading_boxes = [Glyph("guide","","",142,488,70,12),
                     Glyph("guide","","",386,383,67,12),
                     Glyph("guide","","",140,280,82,12),
                     Glyph("guide","","",42,286,77,12)]
    for g in [*glyphs,*heading_boxes]:
        x0=max(0,math.floor((g.x-g.w/2-2)/step))
        x1=min(nx-1,math.ceil((g.x+g.w/2+2)/step))
        y0=max(0,math.floor((g.y-g.h/2-2)/step))
        y1=min(ny-1,math.ceil((g.y+g.h/2+2)/step))
        blocked[x0:x1+1,y0:y1+1] = True
    used_h=np.zeros((nx,ny),dtype=float)
    used_v=np.zeros((nx,ny),dtype=float)

    def ports(g,source):
        # Endpoint, exterior grid port, and direction away from the glyph.
        result=[]
        for dx,dy in ((1,0),(0,1),(0,-1)) if source else ((-1,0),(0,1),(0,-1)):
            end=(g.x+dx*g.w/2,g.y+dy*g.h/2)
            gx=round(g.x/step) if not dx else (math.ceil((end[0]+6)/step) if dx>0 else math.floor((end[0]-6)/step))
            gy=round(g.y/step) if not dy else (math.ceil((end[1]+6)/step) if dy>0 else math.floor((end[1]-6)/step))
            if 1<=gx<nx-1 and 1<=gy<ny-1 and not blocked[gx,gy]:
                result.append((end,(gx,gy),0 if dx else 1))
        return result

    def route(source,target):
        starts=ports(source,True)
        goals=ports(target,False)
        goal_by_cell={p[1]:p for p in goals}
        assert starts and goals,(source.id,target.id)
        def heuristic(x,y):
            return min(abs(x-gx)+abs(y-gy) for gx,gy in goal_by_cell)
        heap=[]; best={}; parent={}; origin={}
        counter=0
        for start in starts:
            end,(x,y),direction=start
            state=(x,y,direction)
            initial=abs(end[0]-step*x)/step+abs(end[1]-step*y)/step
            best[state]=initial
            parent[state]=None
            origin[state]=start
            heapq.heappush(heap,(initial+heuristic(x,y),counter,state))
            counter+=1
        final=None
        while heap:
            score,_,state=heapq.heappop(heap)
            x,y,d=state
            cost=best[state]
            if score>cost+heuristic(x,y)+1e-8:
                continue
            if (x,y) in goal_by_cell:
                final=state
                break
            for dx,dy in ((1,0),(0,1),(0,-1),(-1,0)):
                xx,yy=x+dx,y+dy
                if not 1<=xx<nx-1 or not 1<=yy<ny-1 or blocked[xx,yy]:
                    continue
                dd=0 if dx else 1
                # Short forward links, few bends, no overlapping trunks.
                c=cost+1+(2.5 if dd!=d else 0)+(1.5 if dx<0 else 0)
                c+=12*(used_h[xx,yy] if dd==0 else used_v[xx,yy])
                c+=2*(used_v[xx,yy] if dd==0 else used_h[xx,yy])
                nxt=(xx,yy,dd)
                if c<best.get(nxt,float("inf")):
                    best[nxt]=c; parent[nxt]=state; origin[nxt]=origin[state]
                    heapq.heappush(heap,(c+heuristic(xx,yy),counter,nxt))
                    counter+=1
        assert final,(source.id,target.id)
        cells=[]; state=final
        while state is not None:
            cells.append(state); state=parent[state]
        cells.reverse()
        for x,y,d in cells:
            (used_h if d==0 else used_v)[x,y]+=1
        end=goal_by_cell[final[:2]][0]
        points=[origin[final][0]]+[(step*x,step*y) for x,y,_ in cells]+[end]
        simple=[points[0]]
        for i,p in enumerate(points[1:-1],1):
            a,b=simple[-1],points[i+1]
            if (p[0]-a[0])*(b[1]-p[1])!=(p[1]-a[1])*(b[0]-p[0]):
                simple.append(p)
        simple.append(points[-1])
        return tuple(simple)

    # Draw local chain links first so they retain the straightest routes.
    priority=(2,11,12,20,21,23,26,29,30,32,41,42,43,44,47)
    order=list(priority)+[i for i in range(1,48) if i not in priority]
    routed={}
    for i in order:
        e=EDGES[i-1]
        routed[i]=route(by_id[e.source],by_id[e.target])
    # Use the narrow, visible gaps for the principal event chain and outcome
    # links. A bounding-box router otherwise takes long detours around the
    # free corners of ellipses and hexagons.
    routed.update({
        20: ((247,348),(253,348)),
        21: ((335,348),(343.5,348)),
        41: ((398,269.56),(416,261)),
        42: ((279.24,255),(365,255),(385.84,246)),
        43: ((377,224),(383.98,224)),
        44: ((380.18,184),(405,192),(416,203)),
    })
    arrows=[Arrow(f"E{i:02}",e.source,e.target,e.route,routed[i],(f"E{i:02}",),e.dependence)
            for i,e in enumerate(EDGES,1)]
    # The only unmodelled link is continuous, routed around the outer edge.
    arrows.append(Arrow("U1","delay","behaviour","unmodelled",
                        ((432,537.5),(432,568),(2,568),(2,376),(130,376),(130,366)),
                        ("U1",),RESPONSES[0].dependence))
    return arrows


def canvas(height):
    # Local in-memory rendering; do not write a matplotlib cache into the repo.
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/trbam-influence-matplotlib")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family":"Liberation Serif", "font.size":FONT,
                         "svg.fonttype":"none", "svg.hashsalt":"trr-influence-v2",
                         "figure.dpi":144, "savefig.dpi":300})
    fig=plt.figure(figsize=(6.5,height/72), facecolor="white")
    ax=fig.add_axes([0,0,1,1], xlim=(0,468), ylim=(0,height))
    ax.set_axis_off()
    return fig,ax


def label(ax,x,y,text,**kwargs):
    assert not re.search("[\u2013\u2014]", text), text
    return ax.text(x,y,text,fontsize=FONT,ha="center",va="center",color="black",
                   linespacing=1.08,zorder=7,**kwargs)


def draw_node(ax,g, legend=False):
    from matplotlib.patches import Ellipse, Rectangle, Polygon
    x,y,w,h=g.x,g.y,g.w,g.h
    kw={"facecolor":"white","edgecolor":"black","linewidth":.7,"zorder":5}
    if g.kind=="decision":
        patch=Rectangle((x-w/2,y-h/2),w,h,**kw)
    elif g.kind in ("uncertain","deterministic","fixed"):
        patch=Ellipse((x,y),w,h,**kw)
        if g.kind in ("deterministic","fixed"):
            inner=Ellipse((x,y),w-4,h-4,fill=False,edgecolor="black",linewidth=.55,zorder=6)
            ax.add_patch(inner)
    elif g.kind=="outcome":
        cut=min(9,w*.2)
        patch=Polygon([(x-w/2,y),(x-w/2+cut,y+h/2),(x+w/2-cut,y+h/2),
                       (x+w/2,y),(x+w/2-cut,y-h/2),(x-w/2+cut,y-h/2)],**kw)
    elif g.kind=="evidence":
        fold=min(6,h*.3)
        patch=Polygon([(x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2-fold),
                       (x+w/2-fold,y+h/2),(x-w/2,y+h/2)],**kw)
        ax.plot([x+w/2-fold,x+w/2-fold,x+w/2],[y+h/2,y+h/2-fold,y+h/2-fold],
                color="black",lw=.6,zorder=6)
    else:
        raise ValueError(g.kind)
    if not legend:
        patch.set_gid("node-"+g.id)
    ax.add_patch(patch)
    if g.label:
        t=label(ax,x,y,g.label)
        t.set_gid("label-"+g.id)
    return patch


def draw_arrow(ax,a):
    from matplotlib.path import Path as PlotPath
    from matplotlib.patches import FancyArrowPatch
    import matplotlib.patheffects as pe
    lw,ls=STYLES[a.route]
    points=a.points
    codes=[PlotPath.MOVETO]+[PlotPath.LINETO]*(len(points)-1)
    patch=FancyArrowPatch(path=PlotPath(points,codes), arrowstyle="-|>",
                         mutation_scale=6,linewidth=lw,linestyle=ls,
                         color="black",zorder=3,capstyle="round",joinstyle="round")
    # A white casing prevents crossings from looking like causal junctions.
    patch.set_path_effects([pe.Stroke(linewidth=lw+1.6,foreground="white"),pe.Normal()])
    patch.set_gid("edge-"+a.id)
    ax.add_patch(patch)


def legend(ax,y):
    ax.plot([5,463],[y+18,y+18],color=".65",lw=.4,zorder=0)
    for x,title,kind in [(15,"Decision","decision"),(103,"Uncertain","uncertain"),
                         (198,"Computed","deterministic"),(291,"Outcome","outcome"),
                         (378,"Reference","evidence")]:
        draw_node(ax,Glyph("legend","",kind,x,y+6,19,10),legend=True)
        ax.text(x+15,y+6,title,fontsize=9,va="center")
    for x,title,route in [(6,"Engineered","engineered"),(122,"Behavioural","behaviour"),(248,"Computed / scaling","computed")]:
        a=Arrow("legend","","",route,((x,y-10),(x+22,y-10)),(),"")
        draw_arrow(ax,a)
        ax.text(x+28,y-10,title,fontsize=9,va="center")
    a=Arrow("legend","","","unmodelled",((6,y-26),(28,y-26)),(),"")
    draw_arrow(ax,a)
    ax.text(34,y-26,"plausible response, not in the model",fontsize=9,va="center")


def row_band(ax,x,y,w,h):
    from matplotlib.patches import Rectangle
    ax.add_patch(Rectangle((x,y),w,h,facecolor=".96",edgecolor="none",zorder=0))


def draw_main():
    fig,ax=canvas(306)
    row_band(ax,89,231,313,34)
    row_band(ax,185,118,205,50)
    row_band(ax,201,77,195,30)
    row_band(ax,247,50,210,28)
    label(ax,39,278,"Decisions",weight="bold")
    label(ax,104,168,"Site context",weight="bold")
    label(ax,227,278,"(a) Red running",weight="bold")
    label(ax,287,174,"(b) Worker exposure",weight="bold")
    label(ax,260,112,"(c) Queue tail",weight="bold")
    label(ax,214,64,"(d) Delay",weight="bold")
    label(ax,357,92,"Outside principal\ndifference")
    arrows=main_arrows()
    for a in arrows:
        draw_arrow(ax,a)
    for n in MAIN_NODES:
        draw_node(ax,n)
    label(ax,284,301,"longer waits may raise violations (not in the model)")
    legend(ax,31)
    return save(fig,MAIN_NODES,arrows,FIG,306)


def draw_full():
    # Legend is below the lower pathway. Main and full use the same 9-point type.
    fig,ax=canvas(648)
    # Shift the explicit full coordinates to leave a clear legend below them.
    nodes=[Glyph(g.id,g.label,g.kind,g.x,g.y+66,g.w,g.h,g.members) for g in full_nodes()]
    arrows=[]
    for a in full_arrows(full_nodes()):
        points=tuple((x,y+66) for x,y in a.points)
        arrows.append(Arrow(a.id,a.source,a.target,a.route,points,a.trace,a.meaning))
    for x,y,w,h in [(4,490,460,59),(96,374,343,106),(95,322,341,52),
                     (96,149,343,159),(192,32,247,98)]:
        row_band(ax,x,y+66,w,h)
    label(ax,42,639,"Decisions",weight="bold")
    label(ax,142,554,"Site context",weight="bold")
    label(ax,276,621,"Release and cycle timing",weight="bold")
    label(ax,386,449,"Red running",weight="bold")
    label(ax,140,346,"Worker exposure",weight="bold")
    label(ax,42,352,"Site context",weight="bold")
    for a in arrows:
        draw_arrow(ax,a)
    for n in nodes:
        draw_node(ax,n)
    label(ax,277,643,"longer waits may raise violations (not in the model)")
    label(ax,234,77,"Queue tail: raw totals and sensitivity only. Avoidance: sensitivity only.")
    legend(ax,37)
    return save(fig,nodes,arrows,FIG.with_name("fig_influence_full"),648)


def save(fig,nodes,arrows,stem,height):
    import matplotlib.pyplot as plt
    from PIL import Image
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    # Check every label at physical size, plus complete visible SVG inventories.
    for t in fig.axes[0].texts:
        assert t.get_fontsize()>=9
        box=t.get_window_extent(renderer)
        assert box.x0>=-1 and box.y0>=-1 and box.x1<=fig.bbox.width+1 and box.y1<=fig.bbox.height+1, (t.get_text(),box)
    svg=io.BytesIO()
    fig.savefig(svg,format="svg",metadata={"Date":None,"Creator":"matplotlib; explicit coordinates"})
    raw=svg.getvalue()
    if stem == FIG:
        raw=b"\n".join(line.rstrip() for line in raw.splitlines()) + b"\n"
    tree=ET.fromstring(raw)
    ids=[e.get("id","") for e in tree.iter()]
    assert sorted(i for i in ids if i.startswith("node-"))==sorted("node-"+n.id for n in nodes)
    assert sorted(i for i in ids if re.fullmatch(r"edge-(?:[ME]\d\d|U\d+)",i))==sorted("edge-"+a.id for a in arrows)
    png=io.BytesIO()
    fig.savefig(png,format="png",dpi=300)
    im=Image.open(io.BytesIO(png.getvalue())).convert("L")
    assert im.width==1950
    stem.with_suffix(".svg").write_bytes(raw)
    im.save(stem.with_suffix(".png"),dpi=(300,300))
    plt.close(fig)
    return {"files":[str(stem.with_suffix(s).relative_to(ROOT)) for s in (".png",".svg")],
            "width_in":6.5,"height_in":height/72,"min_font_pt":9,
            "png_size":list(im.size),"dpi":300,"colour_mode":"L",
            "nodes":len(nodes),"arrows":len(arrows),
            "model_arrows":sum(a.route!="unmodelled" for a in arrows),
            "unmodelled_arrows":sum(a.route=="unmodelled" for a in arrows),
            "svg_inventory_match":True}


MAIN_NOTES = """
## Main-text grouping and omissions

The main figure has 17 visible scientific nodes. The worker double oval contains
three parallel contributions, not a controller -> placement causal chain. The
tied operator still inherits the calibrated controller draw. Demand and hours
are fixed within each cell; speed is sampled, so their shared site-input oval
is not a claim that demand is sampled. Mutual sight remains a separate site oval.
Its incoming layout arrow concerns available sight over the chosen section.

All main-text arrows now terminate at scientific nodes. Control-form hold,
programmed all-red and section length enter Encounters from below. Mutual sight
enters Entry timing/encounters through M22 (E18) and Collisions through M09
(E18/E21), exposing both the timing and avoidance routes. The full trace computes
sight-dependent discovery TTC inside Encounters before evaluating avoidance.

Cycle timing is a visible computed node. Its all-red input and delay output are
thin computed arrows, M20 and M19. Other timing inputs and downstream uses remain
within the grouped pathway arrows, as detailed in the full trace; the main view
does not claim that all-red is the only input to cycle timing.

One continuous dotted delay -> violation-rate arrow runs around the edge of
each figure, labelled once beside the line:
"longer waits may raise violations (not in the model)".
There are no continuation tags or floating arrow targets.

| Full links | Treatment in main figure |
|---|---|
| E11, E12, E15, E16 | All-red to cycle is explicit in M20; release and facing-count arithmetic remain in the grouped red-running inputs, including M03 and M07. |
| E19, E22 | Entry timing, hold and response inputs remain inside encounters/collisions. |
| E24 | Impact, mass and occupant severity retained within head-on harm. |
| E26 | Expert strike rate and severity retained within the worker bundle. |
| E30, E31, E32 | Tied operator and placement/offset arithmetic internal to the worker bundle. |
| E35 | Expert queue rate and severity retained within queue-tail harm. |
| E36, E45 | Queue scaling/restoration appears only in the full reference; queue tail is outside the principal difference. |
| E37, E38, E39, E40, E46 | Avoidance sensitivity, secondary-harm chance and their scaling remain only in the full reference. |

These omissions concern the main-text view only. All 27 original bundles, all
47 original model links, and all 34 Priors fields remain in the full figure and
the inventory below. No parameter value or model calculation was changed.

## Corrections and response boundary

* Mutual sight is site context. Section length and stop-line placement affect
  the available sight specified at model entry. No new site-geometry solver is
  implied by E08.
* U1 is the only dotted link: delay -> violation rate. The line and its
  "not in the model" label refer solely to that behavioural response.
* Programmed all-red -> cycle timing -> delay is modelled. Main M20/M19 and
  full E11/E12/E47 are thin computed arrows. The full diagram retains all
  original node positions and model-edge routes; E11's style and the waiting
  annotation/legend are the only full-figure changes.
* The 47 model links form a DAG. The proposed waiting response is deliberately excluded from computational validation because it is not an implemented dependence. It does not create a directed cycle in this graph; delay is computed from timing, not from entries. Record-scaling links are thin solid, not dotted.
"""


def write_audit(fields,rendering):
    branch=subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()
    sha=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    lines=["# TRR v1.2 influence diagrams: trace and main-text edge audit", "",
           f"Source branch `{branch}`; base revision `{sha}`. Fingerprints identify the inspected working-tree source.", "",
           "**Main: 17 nodes, 22 arrows (21 model/grouped links plus 1 plausible-response annotation).**",
           "**Full: 27 nodes, 48 arrows (47 original model links plus 1 plausible-response annotation).**", "",
           "Regenerate both figures and this audit with `python3 -B model/scripts/make_influence_diagram.py`. Explicit matplotlib coordinates; no Graphviz. No model run, branch change or commit is required.", "",
           "## Main-text nodes", "", "| ID | Label | Shape/type | Original visible bundles |", "|---|---|---|---|"]
    for n in MAIN_NODES:
        lines.append(f"| {n.id} | {n.label.replace(chr(10),' / ')} | {n.kind} | {', '.join(n.members)} |")
    lines += ["", "## Main-text arrows and exact traced-edge mapping", "",
              "| Arrow | From | To | Style | Full trace | Meaning |", "|---|---|---|---|---|---|"]
    style={"engineered":"Bold solid","behaviour":"Dashed","computed":"Thin solid","evidence":"Thin solid (scaling)","unmodelled":"Dotted"}
    for a in main_arrows():
        lines.append(f"| {a.id} | {a.source} | {a.target} | {style[a.route]} | {', '.join(a.trace)} | {a.meaning} |")
    lines += [MAIN_NOTES,"## Full node inventory", "",
              "| ID | Printed label | Type | Reader group | Code quantities represented | File and function |", "|---|---|---|---|---|---|"]
    labels={g.id:g.label for g in full_nodes()}
    for n in NODES:
        sources="; ".join(r.md() for r in n.refs)
        lines.append(f"| {n.id} | {labels[n.id].replace(chr(10),' / ')} | {n.kind} | {n.group} | {n.quantities} | {n.function}; {sources} |")
    lines += ["", "## Full edge inventory (original E01 to E47 retained)", "",
              "| Edge | From | To | Style | Dependence | Checked source anchors |", "|---|---|---|---|---|---|"]
    for i,e in enumerate(EDGES,1):
        lines.append(f"| E{i:02} | {e.source} | {e.target} | {style[e.route]} | {e.dependence} | {'; '.join(r.md() for r in e.refs)} |")
    for i,e in enumerate(RESPONSES,1):
        lines.append(f"| U{i} | {e.source} | {e.target} | Dotted | {e.dependence} | User-requested plausible response; not a traced model link. |")
    lines += [NOTES,"## Verification and rendering","",
              f"The retained source anchors pass; AST inspection covers all {len(fields)} Priors fields exactly once. The original 47-link model graph passes its DAG check. Only U1 (main M21) uses the dotted response style. The SVG inventory checks count scientific node/arrow IDs, excluding legend glyphs. Physical canvas size is fixed, all text is at least 9 pt, label bounds are checked, and PNGs are saved as 300 dpi greyscale.", "",
              "Visual review opened both regenerated PNGs. Main-text revisions replaced the bracket with node-specific targets, exposed the computed cycle-to-delay path, and separated input routes and headings. Full-figure evidence labels identify constructed reference levels. This records the layout review; the checks above are the reproducible automated checks. A geometric review confirms that all 22 main connectors avoid unrelated nodes and text. The full model graph retains the same nodes and computed dependencies. White gaps at remaining crossings prevent them being mistaken for junctions.", ""]
    if rendering:
        lines += ["```json",json.dumps(rendering,indent=2),"```",""]
    else:
        lines += ["Audit-only run; figures have not been rendered by this invocation.",""]
    files=sorted({r.path for obj in [*NODES,*EDGES] for r in obj.refs} | {"model/config/priors.toml","model/src/mtcpts/cycle.py","model/scripts/variant_operator_reference.py"})
    lines += ["### Source fingerprints","","| File | SHA256 |","|---|---|"]
    for path in files:
        lines.append(f"| `{path}` | `{hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}` |")
    lines += ["","### Sampled-input coverage","","| Prior | Full node |","|---|---|"]
    for n in NODES:
        for prior in n.priors:
            lines.append(f"| `{prior}` | {n.id} |")
    lines += ["","### Explicit layout","",
              "Node centres and dimensions are in physical points; origin is bottom left. The main canvas is 468 by 306 points. Full coordinates receive a 66-point footer offset on a 468 by 648 point canvas. Main edge control points are explicit in `main_arrows`; the full trace uses a deterministic orthogonal grid router around the explicit node boxes. No invisible scientific edges are introduced for layout.", "",
              "| Figure | Node | x | y | Width | Height |","|---|---|---|---|---|---|"]
    for name,glyphs in (("main",MAIN_NODES),("full",full_nodes())):
        for g in glyphs:
            lines.append(f"| {name} | {g.id} | {g.x} | {g.y+(66 if name=='full' else 0)} | {g.w} | {g.h} |")
    AUDIT.write_text("\n".join(lines)+"\n")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-only",action="store_true")
    args=parser.parse_args()
    fields=validate()
    assert len(MAIN_NODES)==17
    assert len(EDGES)==47
    assert {(e.source,e.target) for e in RESPONSES}=={("delay","behaviour")}
    arrows = main_arrows()
    ids = {n.id for n in MAIN_NODES}
    assert all(a.source in ids and a.target in ids for a in arrows)
    assert {(a.source, a.target) for a in arrows if a.route == "unmodelled"} == {("delay", "behaviour")}
    routes = {(a.source, a.target): a.route for a in arrows}
    assert routes["allred", "cycle"] == routes["cycle", "delay"] == "computed"
    assert all(routes[source, "encounters"] == "engineered" for source in ("control", "allred", "layout"))
    assert routes["sight", "collisions"] == routes["sight", "encounters"] == "computed"
    rendering=None if args.audit_only else {"main":draw_main(),"full":draw_full()}
    write_audit(fields,rendering)
    print(json.dumps(rendering or {"mode":"audit-only","priors_covered":len(fields)},indent=2))


if __name__=="__main__":
    main()
