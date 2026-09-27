# TRR v1.2 influence diagrams: trace and main-text edge audit

Source branch `trr-v1.2-cut`; base revision `bd4649ad3ae1465632a3cec3e0483882a1053ad2`. Fingerprints identify the inspected working-tree source.

**Main: 17 nodes, 22 arrows (21 model/grouped links plus 1 plausible-response annotation).**
**Full: 27 nodes, 48 arrows (47 original model links plus 1 plausible-response annotation).**

Regenerate both figures and this audit with `python3 -B model/scripts/make_influence_diagram.py`. Explicit matplotlib coordinates; no Graphviz. No model run, branch change or commit is required.

## Main-text nodes

| ID | Label | Shape/type | Original visible bundles |
|---|---|---|---|
| control | Control / form | decision | control |
| layout | Section length; / stop-line / placement | decision | layout |
| allred | Programmed / all-red | decision | allred |
| sight | Mutual / sight | uncertain | sight |
| site | Demand, hours; / speed | uncertain | context, motion |
| crash | Constructed crash / reference | evidence | crash |
| occupation | Constructed worker / reference | evidence | occupation |
| behaviour | Violation / rate | uncertain | behaviour |
| entries | Entries | deterministic | entries |
| encounters | Entry timing; / encounters | deterministic | encounters |
| collisions | Collisions | deterministic | collisions |
| headon | Head-on / harm | deterministic | headon |
| worker | Controller strike harm / Attended-device operator harm / Placement and retrieval harm | deterministic | controller, operator, placement |
| queue | Queue-tail harm | deterministic | queue |
| harm | Expected serious / harm events per / operation day | outcome | harm |
| cycle | Cycle timing | deterministic | cycle |
| delay | Delay | outcome | delay |

## Main-text arrows and exact traced-edge mapping

| Arrow | From | To | Style | Full trace | Meaning |
|---|---|---|---|---|---|
| M01 | control | behaviour | Dashed | E01 | Select the form-specific converted entry estimate. |
| M02 | behaviour | entries | Dashed | E02 | Rate multiplied by vehicles facing STOP/red. |
| M03 | control | encounters | Bold solid | E03, E04, E16, E19 | Control form selects release and hold; the grouped route terminates at encounters. |
| M04 | control | worker | Bold solid | E05, E06, E07 | Select controller, tied operator and placement contributions. |
| M05 | layout | sight | Bold solid | E08 | Section length and stop-line placement affect the site sight available to the model. |
| M06 | layout | encounters | Bold solid | E09, E10, E16 | Section length determines clearance and opposing trajectories, hence encounters. |
| M07 | allred | encounters | Bold solid | E11, E12, E16 | Programmed all-red determines opposing release timing and encounters. |
| M08 | site | encounters | Thin solid | E13, E14, E17 | Demand, hours, speed and acceleration enter cycle and encounter calculations; no direct violation-rate adjustment. |
| M09 | sight | collisions | Thin solid | E18, E21 | Available mutual sight determines discovery time and time to avoid collision; the full trace carries this through encounter branch TTC. |
| M22 | sight | encounters | Thin solid | E18 | Sight weights entry times, selects encounters and conditions opposing release. |
| M10 | entries | encounters | Thin solid | E20 | Retain daily entries through branch calculations. |
| M11 | encounters | collisions | Thin solid | E21 | Branch encounters and time to meet determine collision/avoidance probability. |
| M12 | collisions | headon | Thin solid | E23 | Apply branch-specific injury probabilities. |
| M13 | crash | headon | Thin solid (scaling) | E25 | Scale head-on serious harm to a reference built from recorded counts and assumed exposure. |
| M14 | site | worker | Thin solid | E27, E28, E33 | Speed transports controller severity; demand and hours scale exposure. Placement uses demand and duration, not full-day hours. |
| M15 | occupation | worker | Thin solid (scaling) | E29 | Apply the constructed occupational reference; tied operator inherits that same draw. Placement keeps its encroachment scale. |
| M16 | headon | harm | Thin solid | E41 | Record-scaled head-on contribution. |
| M17 | worker | harm | Thin solid | E42, E43, E44 | All three worker contributions with their arm-specific signs. |
| M18 | site | queue | Thin solid | E14, E34 | Demand/cycle counts scale stopped-vehicle exposure; the expert rate/severity remain within the queue bundle. |
| M19 | cycle | delay | Thin solid | E47 | The model computes delay from cycle timing, including the programmed all-red. |
| M20 | allred | cycle | Thin solid | E11, E12 | Programmed all-red enters cycle timing as modelled; this is a computed link. |
| M21 | delay | behaviour | Dotted | U1 | One continuous peripheral arrow: longer waits may raise violations (not in the model). |

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

## Full node inventory

| ID | Printed label | Type | Reader group | Code quantities represented | File and function |
|---|---|---|---|---|---|
| control | Control / form | decision | Decisions | Strategy name: S0 manual, S1a fixed-time signals, S1b monitored signals, S2 attended gated device. All arms are evaluated; this is a scenario choice, not an optimiser. | run_cell; `model/src/mtcpts/model.py:252-282` |
| layout | Section length; / stop-line / placement | decision | Decisions | Cell.section_m and stop-line placement define the section being controlled. Mutual sight is a site property, represented by Priors.d_sight_m and capped at section length in encounters. Placement affects the available sight supplied to the model; the code does not calculate sight from a geometric site plan. | Cell; run_baseline_extras; `model/src/mtcpts/model.py:51-54`; `model/scripts/run_suite.py:247-259` |
| allred | Programmed / all-red | decision | Decisions | Specified clearance-speed and buffer distributions, Priors.v_clear_kmh and Priors.clear_buffer_s. The programme samples designs; actual C1 is computed in cycle, not an independent freely chosen scalar. | Priors; run_cell; `model/src/mtcpts/model.py:79-82`; `model/src/mtcpts/model.py:164-175` |
| context | Demand; hours | fixed | Site context | Cell.q_vph_dir, q_vps=q_vph_dir/3600, OPERATION_HOURS=8, veh_day_dir=q_vph_dir*OPERATION_HOURS. These are fixed context, not random or optimisation variables. | Cell; run_cell; `model/src/mtcpts/model.py:48-54`; `model/src/mtcpts/model.py:148-150`; `model/src/mtcpts/model.py:242-242` |
| motion | Speed; / acceleration | uncertain | Site context | platoon_speed_kmh=v_p_kmh, v_p=v_p_kmh/3.6, a_veh_ms2=a_veh. The main run samples speed; a Fixed(speed) sweep is a separate design scenario. The posted speed limit is not the sampled operating speed. | run_cell; run_baseline_extras; `model/src/mtcpts/model.py:158-160`; `model/scripts/run_suite.py:226-234` |
| timing | Cycle timing / inputs | uncertain | Release control | sat_headway_s=h_sat; startup_lost_s=lost; s0_green_margin=margin; v_clear_kmh=v_clear; clear_buffer_s=buffer_s; t_confirm_s=t_confirm; f_cycle_a=f_a; f_cycle_b=f_b. Values drawn after the design specifications are supplied. | run_cell; `model/src/mtcpts/model.py:161-166`; `model/src/mtcpts/model.py:185-186` |
| sight | Mutual / sight | uncertain | Site context | d_sight_m=d_sight. Its deterministic cap sight=min(d_sight,L) is carried in encounters. This node becomes fixed context in the sight sweep. | run_cell; `model/src/mtcpts/model.py:222-223` |
| behaviour | Violation / rate | uncertain | Behaviour | r_v0, r_v1a (also used by S1b), r_v2; selected r_v per vehicle facing STOP/red. Literature-adjusted rates are preserved exactly, not reduced again for apparent occupancy. | run_cell; `model/src/mtcpts/model.py:210-211`; `model/src/mtcpts/model.py:238-238`; `model/src/mtcpts/model.py:265-278` |
| response | Entry timing; / hold; response | uncertain | Red-running event chain | w_occ, q_lead, w_onset, onset_window_s; p_detect_s0, p_detect_s1b, p_detect_s2 selected into p_det (zero for S1a); ttc50, s_ttc. ModelForm.rho and curve are fixed structural settings, primary rho=0 and logistic, carried here without treating them as sampled priors. | run_cell; TreeParams; ModelForm; `model/src/mtcpts/model.py:212-219`; `model/src/mtcpts/model.py:239-239`; `model/src/mtcpts/model.py:265-286`; `model/src/mtcpts/conflict.py:198-216` |
| injury | Impact; mass; / occupants | uncertain | Red-running event chain | impact_speed_frac=f_imp, independent mass1_kg/mass2_kg=m1/m2, rounded occ1/occ2 from occupancy. Fixed Wang curve coefficients and units are carried in headon. | run_cell; `model/src/mtcpts/model.py:220-227` |
| sej | Expert rates / and severity | uncertain | Worker exposure and queue tail | C.RE3_MTC and C.SEV3 -> paired re3_rate, sev3_p; C.RE1_Queue and C.SEV1 -> paired re1_rate, sev1_p. Reciprocals convert elicited inter-event passes into rates. Expert indices idx1/idx3 couple rate and severity within each pathway, not between pathways. PooledSEJ.sample_pairs preserves the pairs. | run_cell; ExpertMixture.sample_with_index; PooledSEJ.sample_pairs; `model/src/mtcpts/model.py:193-207`; `model/src/mtcpts/distributions.py:94-100`; `model/src/mtcpts/distributions.py:154-160` |
| exposure | Positions; / placement | uncertain | Worker exposure | t_deploy_s=t_dep (both ends, install plus remove); enc_rate_vkm=enc; reach_alpha=alpha; offset_m=offset; offset_op_m=offset_op; deploy_speed_kmh=v_dep; fixed l_exposed_km=l_exp. Fixed reference controller position d_ref=0 or 1 m and two operators belong to the adopted operator comparison; one-operator and other reference offsets are alternatives. | run_cell; review_reads.main; `model/src/mtcpts/model.py:229-240`; `model/scripts/review_reads.py:180-186` |
| secondary | Secondary / harm chance | uncertain | Avoidance sensitivity | p_evade_harm, conditional secondary harm-bearing event probability after successful avoidance; worker injury at operating speed is applied separately. | run_cell; `model/src/mtcpts/model.py:221-221` |
| cycle | All-red; / cycle; queues | deterministic | Release control | L, transit, t_rest, sat_vps, C0, programmed C1, rho_q, stable, g_min, greens, clears; T, red, arr_cycle, stopped_red/n_queue, t_clear_q, stopped, f_stop, cycles_day, facing_day, stopped_day; DayContext and ConflictInputs (including startup lost time). Baseline S0 f_stop0 supplies re1_per_stop conversion. Demand, hours, headway and motion are retained in this bundle for downstream calls. | run_cell; _cycle_quantities; traverse_time_from_rest; `model/src/mtcpts/model.py:129-142`; `model/src/mtcpts/model.py:168-191`; `model/src/mtcpts/model.py:244-263`; `model/src/mtcpts/conflict.py:58-64` |
| entries | Red / STOP / entries | deterministic | Red-running event chain | violations_per_day = facing_stop_per_day*r_v_facing. This is an entry count, not an independently generated Poisson draw. | w5_terms; `model/src/mtcpts/pathways.py:94-101` |
| encounters | Encounters; / time to meet | deterministic | Red-running event chain | Branch time t_a, standing/onset type, weight; occupied, d_near, v_near; visible_occ/hidden_occ; entry weight w and normaliser acc[w]; next entry t_next/v0_next, meets, sep_e, hold, p_enter; p_conf, TTC and closing for A/H/B branches; weighted conf, blind, clear and safe accumulators; p_conflict, conflicts_per_day, p_blind, f_clear, p_safe_window. Carries entry count and full branch states to collisions, not just mean TTC. | nearest_opposing; next_opposing_entry; w5_tree.branch; w5_terms; `model/src/mtcpts/conflict.py:117-195`; `model/src/mtcpts/conflict.py:286-348`; `model/src/mtcpts/conflict.py:367-391`; `model/src/mtcpts/pathways.py:99-99` |
| collisions | Collisions; / avoidances | deterministic | Red-running event chain | q=q_fail(TTC); branch p_coll=p_conf*q*q (or rho*q+(1-rho)*q*q); acc[coll], acc[collv], acc[collt]; tree p_coll, p_evade; collisions_per_day, evasions_per_day; collision-weighted closing_ms and mean_ttc. Branch closing speeds and weighted collision terms continue into injury; no product of marginal medians is used. | q_fail; p_collision_given_conflict; w5_tree.branch; w5_terms; `model/src/mtcpts/conflict.py:247-262`; `model/src/mtcpts/conflict.py:350-362`; `model/src/mtcpts/conflict.py:379-388`; `model/src/mtcpts/pathways.py:100-104` |
| headon | Head-on harm | deterministic | Red-running event chain | closing_kmh=branch closing_ms*3.6*f_imp; momentum dv1/dv2; occupant p1/p2; p_dsi=1-(1-p1)^occ1*(1-p2)^occ2; acc[harm], p_harm; raw W5=Nentries*p_harm. Also holds l5=headon record/centre(S1a W5) and l5*W5 for each arm. centre is median or mean; l5 is shared across arms, not draw-by-draw fitting. | w5_terms.severity_fn; p_event_dsi_headon; w5_tree; Data.delta; `model/src/mtcpts/pathways.py:89-100`; `model/src/mtcpts/severity.py:79-96`; `model/src/mtcpts/conflict.py:355-360`; `model/scripts/make_figures_trr_v12.py:177-191` |
| controller | Controller / strike harm | deterministic | Worker exposure | passes=2*veh_day_dir; raw strikes=passes*re3_rate; sev3=logistic(logit(sev3_p)+0.078*(v_p_kmh-50)); S0 W3=passes*re3_rate*sev3; l3=controller record/centre(S0 W3); calibrated reference l3*W3. Retains the S0 reference draw for the tied operator even when its direct ledger contribution is removed by a device. | w3_events; sev_worker_at_speed; run_cell; Data.delta; `model/src/mtcpts/pathways.py:59-71`; `model/src/mtcpts/severity.py:99-122`; `model/src/mtcpts/model.py:265-282`; `model/scripts/make_figures_trr_v12.py:177-191` |
| operator | Tied operator / harm | deterministic | Worker exposure | Adopted v1.2 S2 op=l3*W3_S0*exp(-reach_alpha*(offset_op_m-d_ref)); zero in S0/S1a/S1b. Same controller draw, same calibrated record, additional standing distance. Original W3r encroachment and independently scaled W3r are alternative formulas listed below, not substituted for this adopted edge. | review_reads.main.tied; Data.delta; `model/scripts/review_reads.py:180-190`; `model/scripts/make_figures_trr_v12.py:182-190` |
| placement | Placement and / retrieval harm | deterministic | Worker exposure | n_veh=2*q_vph_dir*t_dep/3600; lam=n_veh*enc*l_exp*exp(-alpha*offset); W4d=lam*p_worker(v_dep). Present in S1a/S1b/S2, zero in S0. Total on-foot time already includes both heads and both moves; operation hours are not multiplied again. | w4d_events; run_cell; `model/src/mtcpts/pathways.py:123-133`; `model/src/mtcpts/model.py:265-282` |
| queue | Queue-tail harm / (raw / sensitivity) | deterministic | Queue-tail pathway | re1_per_stop=re1_rate/max(f_stop0,1e-6); W1=stopped_day*re1_per_stop*sev1_p. Optional k1=all-cause record/centre(W1_S0) scales the queue term. The principal harm DIFFERENCE suppresses W1; raw totals include it. No operating-speed severity adjustment is applied to W1. | run_cell; w1_events; review_reads.main; welfare.main; `model/src/mtcpts/model.py:244-246`; `model/src/mtcpts/pathways.py:49-56`; `model/scripts/review_reads.py:54-64`; `model/scripts/welfare.py:81-85` |
| avoidance | Avoidance harm / (sensitivity) | deterministic | Avoidance sensitivity | W5b=evasions_per_day*p_evade_harm*p_worker(v_p_kmh); raw term reported separately. Optional record sensitivity adds l5*(W5b_s-W5b_S0), sharing the head-on multiplier. Never in run_cell.results_h or the adopted principal comparison. | w5b_band; decision_outputs_s2.main; `model/src/mtcpts/pathways.py:111-120`; `model/scripts/decision_outputs_s2.py:223-229` |
| occupation | Constructed worker / reference | evidence | Calibration evidence | STRIKE_REC, STRIKE_C: controller serious-harm reference levels built from recorded counts and assumed exposure. These fixed calibration inputs do not alter priors or cause strikes. Alternative fatal-to-serious ratios are reference sensitivities. | module constants; record_reads; Data.delta; `model/scripts/decision_outputs_s2.py:29-31`; `model/scripts/decision_outputs_s2.py:47-54`; `model/scripts/make_figures_trr_v12.py:177-180` |
| crash | Constructed references / head-on; all causes | evidence | Calibration evidence | HEADON_REC/HEADON_C serious-harm anchors; ALL_TTM_DSI_PER_OP_DAY all-cause reference for queue sensitivity. Collision-only record/gate is distinct and is documented below; it does not cause collisions or replace principal serious-harm matching. | module constants; record_reads; review_reads.main; `model/scripts/decision_outputs_s2.py:29-37`; `model/scripts/review_reads.py:54-67` |
| harm | Expected serious / harm events per / operation day | outcome | Outcomes | Per-arm raw H=W1+W3+W5+W4d; adopted record-calibrated delta H_s=W4d_s+op_s-l3*W3_S0+l5*(W5_s-W5_S0). For S1a/S1b op=0; for S2 use tied op. Raw W1 and optional queue/avoidance restorations are labelled edges. P(delta H<0), quantiles, equivalence and break-even are summaries of these paired draws, not separate mechanisms. | run_cell; review_reads.main.dh; Data.delta; `model/src/mtcpts/model.py:287-292`; `model/scripts/review_reads.py:58-64`; `model/scripts/make_figures_trr_v12.py:177-191` |
| delay | Delay | outcome | Outcomes | r=T-green; d1=r^2/[2*T*(1-q/sat)]; delay_h=2*q_vph_dir*hours*d1/3600. S2=S0 by cycle assumption. Optional non-clearing residual delay uses excess=max(q*T-sat*G,0), D=hours*3600, residual_vh=2*excess*D^2/(2*T)/3600. Delay does not feed serious harm. | uniform_delay_per_vehicle_s; welfare.main; review_reads.main; `model/scripts/welfare.py:36-39`; `model/scripts/welfare.py:59-74`; `model/scripts/review_reads.py:225-238` |

## Full edge inventory (original E01 to E47 retained)

| Edge | From | To | Style | Dependence | Checked source anchors |
|---|---|---|---|---|---|
| E01 | control | behaviour | Dashed | Select r_v0, r_v1a (S1a and S1b), or r_v2. | `model/src/mtcpts/model.py:265-278` |
| E02 | behaviour | entries | Dashed | Nentries=facing_day*r_v_facing. | `model/src/mtcpts/pathways.py:95-95` |
| E03 | control | cycle | Bold solid | Select greens[name], clears[name]; S2 copies the attended S0 plan. | `model/src/mtcpts/model.py:187-191`; `model/src/mtcpts/model.py:252-255` |
| E04 | control | response | Bold solid | Select p_det: S0 radio hold; S1a zero; S1b extension; S2 operator hold. Other response priors are shared. | `model/src/mtcpts/model.py:265-286` |
| E05 | control | controller | Bold solid | Lane-standing controller term belongs to S0; direct term is removed in device arms. The S0 reference remains available for tied S2 exposure. | `model/src/mtcpts/model.py:265-280`; `model/scripts/make_figures_trr_v12.py:183-191` |
| E06 | control | operator | Bold solid | Include tied operator exposure only for the attended S2 device. | `model/scripts/make_figures_trr_v12.py:182-185` |
| E07 | control | placement | Bold solid | Zero in S0; physical head placement/retrieval in all three device arms. | `model/src/mtcpts/model.py:265-282` |
| E08 | layout | sight | Bold solid | Section length and stop-line placement determine which site sight is available. The code accepts that sight as d_sight_m, including fixed sight in the sweep; it caps effective sight at L. This is an input-specification relation, not a geometry solver or a decision to change the site's intrinsic visibility. | `model/scripts/run_suite.py:253-259`; `model/src/mtcpts/model.py:222-223`; `model/src/mtcpts/conflict.py:290-290` |
| E09 | layout | cycle | Bold solid | Section length determines traverse times and programmed all-red. | `model/src/mtcpts/model.py:168-175` |
| E10 | layout | encounters | Bold solid | Length sets occupancy, separation, transit and the cap on mutual sight. | `model/src/mtcpts/model.py:258-263`; `model/src/mtcpts/conflict.py:286-290`; `model/src/mtcpts/conflict.py:328-331` |
| E11 | allred | timing | Thin solid | Draw the specified clearance-speed and safety-buffer inputs. Actual all-red C1 is computed in cycle. | `model/src/mtcpts/model.py:164-165` |
| E12 | timing | cycle | Thin solid | Headway -> saturation; confirmation -> C0; design speed/buffer -> C1; margins and scale factors -> greens. Startup lost time is passed to ConflictInputs. | `model/src/mtcpts/model.py:170-191`; `model/src/mtcpts/model.py:258-263` |
| E13 | motion | cycle | Thin solid | Speed and acceleration determine the from-rest traverse and clearance floor. | `model/src/mtcpts/model.py:158-175`; `model/src/mtcpts/conflict.py:58-64` |
| E14 | context | cycle | Thin solid | Demand sets capacity ratio, green, queues and facing counts; hours set cycles/day and daily counts. | `model/src/mtcpts/model.py:129-142`; `model/src/mtcpts/model.py:178-183` |
| E15 | cycle | entries | Thin solid | Use actual facing_STOP/red arrivals from this arm's red duration and cycle count. | `model/src/mtcpts/model.py:254-257`; `model/src/mtcpts/pathways.py:95-95` |
| E16 | cycle | encounters | Thin solid | Clearance, opposing green, queued count, demand, headway and start lag set release/occupancy and next entry, without changing the measured violation rate. | `model/src/mtcpts/model.py:258-263`; `model/src/mtcpts/conflict.py:117-195`; `model/src/mtcpts/conflict.py:333-338` |
| E17 | motion | encounters | Thin solid | Speed/acceleration set the vehicle trajectories, transit, mutual-discovery TTC and closing speed. | `model/src/mtcpts/conflict.py:305-341` |
| E18 | sight | encounters | Thin solid | Cap sight at L; test visible/hidden occupancy and sighted next entry; compute TTC at discovery. Does not scale Nentries. | `model/src/mtcpts/conflict.py:290-290`; `model/src/mtcpts/conflict.py:301-337` |
| E19 | response | encounters | Thin solid | Entry timing mixture and visibility weights plus hold and opposing-driver entry chance set weighted branch conflict probabilities. | `model/src/mtcpts/conflict.py:311-311`; `model/src/mtcpts/conflict.py:333-338`; `model/src/mtcpts/conflict.py:367-377` |
| E20 | entries | encounters | Thin solid | Convert the integrated per-entry conflict probability to daily encounters; retain Nentries for all subsequent event counts. | `model/src/mtcpts/pathways.py:95-101` |
| E21 | encounters | collisions | Thin solid | Branch TTC and p_conf determine collision/avoidance; weighted branch states and Nentries are retained, not replaced by average TTC. | `model/src/mtcpts/conflict.py:344-362`; `model/src/mtcpts/conflict.py:379-388`; `model/src/mtcpts/pathways.py:99-101` |
| E22 | response | collisions | Thin solid | ttc50/s_ttc set q_fail; fixed ModelForm.rho/curve govern alternatives. | `model/src/mtcpts/conflict.py:247-262`; `model/src/mtcpts/conflict.py:350-354` |
| E23 | collisions | headon | Thin solid | Weight each branch's injury probability by that branch's collision term before normalisation and multiplication by daily entries. | `model/src/mtcpts/conflict.py:355-360`; `model/src/mtcpts/conflict.py:381-387`; `model/src/mtcpts/pathways.py:97-97` |
| E24 | injury | headon | Thin solid | Retained closing speed, two masses and integer occupant counts determine at least one serious injury. | `model/src/mtcpts/pathways.py:89-92`; `model/src/mtcpts/severity.py:79-96` |
| E25 | crash | headon | Thin solid (scaling) | l5=head-on serious-harm record/centre(S1a W5); same multiplier applied to all arms. | `model/scripts/make_figures_trr_v12.py:177-191`; `model/scripts/decision_outputs_s2.py:47-54` |
| E26 | sej | controller | Thin solid | Paired per-pass strike rate and conditional severity anchor determine W3. | `model/src/mtcpts/pathways.py:59-71` |
| E27 | motion | controller | Thin solid | Transport the SEJ severity from 50 km/h to the sampled operating speed using the worker-curve logit slope. | `model/src/mtcpts/pathways.py:69-71`; `model/src/mtcpts/severity.py:120-122` |
| E28 | context | controller | Thin solid | Both-direction daily passes = 2*q_vph_dir*hours. | `model/src/mtcpts/model.py:242-242`; `model/src/mtcpts/pathways.py:69-71` |
| E29 | occupation | controller | Thin solid (scaling) | l3=controller serious-harm record/centre(S0 W3); preserve pairing and shape. | `model/scripts/make_figures_trr_v12.py:177-191` |
| E30 | controller | operator | Thin solid | Use that same calibrated controller draw in the adopted tied operator construction. | `model/scripts/review_reads.py:183-185` |
| E31 | exposure | operator | Thin solid | Additional distance enters exp[-alpha*(offset_op-d_ref)]. Two operators is the adopted configuration. | `model/scripts/review_reads.py:182-185` |
| E32 | exposure | placement | Thin solid | Deployment time, encroachment rate, exposed length, offset/reach and deployment-speed injury curve enter W4d. | `model/src/mtcpts/pathways.py:123-133` |
| E33 | context | placement | Thin solid | Both-direction hourly demand multiplies deployment duration, not the full operating day. | `model/src/mtcpts/model.py:274-275`; `model/src/mtcpts/pathways.py:131-131` |
| E34 | cycle | queue | Thin solid | Own-arm stopped_day and S0 f_stop0 turn the per-approach SEJ rate into per-stop exposure. | `model/src/mtcpts/model.py:244-246`; `model/src/mtcpts/pathways.py:56-56` |
| E35 | sej | queue | Thin solid | Paired re1_rate and sev1_p determine queue-tail event risk; severity is not operating-speed transported. | `model/src/mtcpts/model.py:245-246`; `model/src/mtcpts/pathways.py:49-56` |
| E36 | crash | queue | Thin solid (scaling) | Optional k1=all-cause serious-harm record/centre(S0 W1); this is a sensitivity scale, not a proven bound or a primary term. | `model/scripts/review_reads.py:54-64`; `model/scripts/welfare.py:81-85` |
| E37 | collisions | avoidance | Thin solid | Successful evasions use (acc[conf]-acc[coll])/acc[w] times Nentries. | `model/src/mtcpts/conflict.py:383-386`; `model/src/mtcpts/pathways.py:101-101`; `model/src/mtcpts/pathways.py:120-120` |
| E38 | secondary | avoidance | Thin solid | Multiply successful evasions by p_evade_harm. | `model/src/mtcpts/pathways.py:120-120` |
| E39 | motion | avoidance | Thin solid | Apply worker injury probability at operating speed to the secondary event band. | `model/src/mtcpts/pathways.py:120-120` |
| E40 | headon | avoidance | Thin solid (scaling) | Record sensitivity shares l5 with W5 (thin scaling link), anchored to W5 alone; raw W5b remains separately available. | `model/scripts/decision_outputs_s2.py:223-227` |
| E41 | headon | harm | Thin solid | W5 enters raw H and calibrated paired differences. | `model/src/mtcpts/model.py:291-291`; `model/scripts/make_figures_trr_v12.py:191-191` |
| E42 | controller | harm | Thin solid | Retain W3 in S0; subtract its calibrated reference in device-minus-manual delta H. | `model/src/mtcpts/model.py:291-291`; `model/scripts/make_figures_trr_v12.py:191-191` |
| E43 | operator | harm | Thin solid | Add the adopted tied S2 operator term. | `model/scripts/make_figures_trr_v12.py:183-191` |
| E44 | placement | harm | Thin solid | Add incremental placement/retrieval harm under each device. | `model/src/mtcpts/model.py:291-291`; `model/scripts/make_figures_trr_v12.py:191-191` |
| E45 | queue | harm | Thin solid | Raw H includes W1; principal delta H sets queue=0. Optional restoration adds k1*(W1_s-W1_S0), or the unscaled gap. | `model/src/mtcpts/model.py:291-291`; `model/scripts/review_reads.py:58-64` |
| E46 | avoidance | harm | Thin solid | Only the bounded sensitivity restores l5*(W5b_s-W5b_S0); excluded from raw results_h and principal delta H. | `model/scripts/decision_outputs_s2.py:223-229` |
| E47 | cycle | delay | Thin solid | T, green, demand/capacity ratio and daily arrivals determine delay; residual-queue sensitivity uses the same cycle inputs. | `model/scripts/welfare.py:36-39`; `model/scripts/welfare.py:59-74`; `model/scripts/review_reads.py:230-238` |
| U1 | delay | behaviour | Dotted | Longer waits may raise the violation rate. Plausible response only; no response function, coefficient or harm contribution is implemented. | User-requested plausible response; not a traced model link. |

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

## Verification and rendering

The retained source anchors pass; AST inspection covers all 34 Priors fields exactly once. The original 47-link model graph passes its DAG check. Only U1 (main M21) uses the dotted response style. The SVG inventory checks count scientific node/arrow IDs, excluding legend glyphs. Physical canvas size is fixed, all text is at least 9 pt, label bounds are checked, and PNGs are saved as 300 dpi greyscale.

Visual review opened both regenerated PNGs. Main-text revisions replaced the bracket with node-specific targets, exposed the computed cycle-to-delay path, and separated input routes and headings. Full-figure evidence labels identify constructed reference levels. This records the layout review; the checks above are the reproducible automated checks. A geometric review confirms that all 22 main connectors avoid unrelated nodes and text. The full model graph retains the same nodes and computed dependencies. White gaps at remaining crossings prevent them being mistaken for junctions.

```json
{
  "main": {
    "files": [
      "trr/manuscript/figures/fig_influence.png",
      "trr/manuscript/figures/fig_influence.svg"
    ],
    "width_in": 6.5,
    "height_in": 4.25,
    "min_font_pt": 9,
    "png_size": [
      1950,
      1275
    ],
    "dpi": 300,
    "colour_mode": "L",
    "nodes": 17,
    "arrows": 22,
    "model_arrows": 21,
    "unmodelled_arrows": 1,
    "svg_inventory_match": true
  },
  "full": {
    "files": [
      "trr/manuscript/figures/fig_influence_full.png",
      "trr/manuscript/figures/fig_influence_full.svg"
    ],
    "width_in": 6.5,
    "height_in": 9.0,
    "min_font_pt": 9,
    "png_size": [
      1950,
      2700
    ],
    "dpi": 300,
    "colour_mode": "L",
    "nodes": 27,
    "arrows": 48,
    "model_arrows": 47,
    "unmodelled_arrows": 1,
    "svg_inventory_match": true
  }
}
```

### Source fingerprints

| File | SHA256 |
|---|---|
| `model/config/priors.toml` | `e25d8a4b4c941ed940f81d5d0ce41bdc630988e24b5978e2ee93a1cb5e2b55f0` |
| `model/scripts/decision_outputs_s2.py` | `a0cff11979efd12bac28142a7fa30b17bba109b86d119c10bff9dd6383abd53a` |
| `model/scripts/make_figures_trr_v12.py` | `3d33f2aef8843549eed514a3add4b2d2f741930b260e9fe95327926e4630e094` |
| `model/scripts/review_reads.py` | `1da7a0385d8dcda894dd64a247feb1c68fd77f35b064c158384ea970f3edbf0f` |
| `model/scripts/run_suite.py` | `69b0f3465ddc9c0f7198aa98893577bc7e1bc382faa3fd6f9c356e4ee32d6b2d` |
| `model/scripts/variant_operator_reference.py` | `67869eda880d55bcc57977c6f8d3165309b17c03774b463519f3070adc540717` |
| `model/scripts/welfare.py` | `ed01acb459d8dbf7816a92e2d536ca719e7e9176a9b32d015d4d74dbefe72209` |
| `model/src/mtcpts/conflict.py` | `c7d382c10f75c648e62a54283c4e22c80771ccd7dd85f4e7d031a9d1beb02d10` |
| `model/src/mtcpts/cycle.py` | `7886eafbf6a756602a07f4f7816209e57bc9dcaa77d512ab44e953aa596d4a8c` |
| `model/src/mtcpts/distributions.py` | `1634b3dcbdc34f3437278bc046095eca875e1a4de641de2b5d727043f4c3ac9d` |
| `model/src/mtcpts/model.py` | `79958f6b084905b9d99b740e10d5b6b8a087a2b31a43f6d517d092d9985c97f7` |
| `model/src/mtcpts/pathways.py` | `789258b526a2de43caa7a81b065c1c9c3e061cc354d3c53802289f0db4db402a` |
| `model/src/mtcpts/severity.py` | `5868f40afe261d2b8ecd0957de1e73d7ceda7288f1bf81f31aa4e038f0473bf6` |

### Sampled-input coverage

| Prior | Full node |
|---|---|
| `platoon_speed_kmh` | motion |
| `a_veh_ms2` | motion |
| `sat_headway_s` | timing |
| `startup_lost_s` | timing |
| `s0_green_margin` | timing |
| `v_clear_kmh` | timing |
| `clear_buffer_s` | timing |
| `t_confirm_s` | timing |
| `f_cycle_a` | timing |
| `f_cycle_b` | timing |
| `d_sight_m` | sight |
| `r_v0` | behaviour |
| `r_v1a` | behaviour |
| `r_v2` | behaviour |
| `w_occ` | response |
| `q_lead` | response |
| `w_onset` | response |
| `onset_window_s` | response |
| `p_detect_s0` | response |
| `p_detect_s1b` | response |
| `p_detect_s2` | response |
| `ttc50` | response |
| `s_ttc` | response |
| `impact_speed_frac` | injury |
| `mass_kg` | injury |
| `occupancy` | injury |
| `t_deploy_s` | exposure |
| `enc_rate_vkm` | exposure |
| `reach_alpha` | exposure |
| `offset_m` | exposure |
| `offset_op_m` | exposure |
| `deploy_speed_kmh` | exposure |
| `l_exposed_km` | exposure |
| `p_evade_harm` | secondary |

### Explicit layout

Node centres and dimensions are in physical points; origin is bottom left. The main canvas is 468 by 306 points. Full coordinates receive a 66-point footer offset on a 468 by 648 point canvas. Main edge control points are explicit in `main_arrows`; the full trace uses a deterministic orthogonal grid router around the explicit node boxes. No invisible scientific edges are introduced for layout.

| Figure | Node | x | y | Width | Height |
|---|---|---|---|---|---|
| main | control | 39 | 248 | 70 | 28 |
| main | layout | 259 | 201 | 78 | 40 |
| main | allred | 174 | 204 | 70 | 28 |
| main | sight | 338 | 204 | 64 | 31 |
| main | site | 124 | 140 | 88 | 35 |
| main | crash | 374 | 278 | 87 | 25 |
| main | occupation | 114 | 89 | 90 | 27 |
| main | behaviour | 118 | 248 | 57 | 32 |
| main | entries | 180 | 248 | 53 | 32 |
| main | encounters | 245 | 248 | 65 | 32 |
| main | collisions | 313 | 248 | 58 | 32 |
| main | headon | 374 | 248 | 53 | 32 |
| main | worker | 287 | 143 | 201 | 47 |
| main | queue | 260 | 92 | 111 | 28 |
| main | harm | 415 | 193 | 84 | 56 |
| main | cycle | 292 | 64 | 81 | 26 |
| main | delay | 424 | 64 | 62 | 28 |
| full | control | 42 | 522 | 76 | 31 |
| full | layout | 42 | 468 | 76 | 43 |
| full | allred | 42 | 584 | 76 | 32 |
| full | context | 42 | 308 | 73 | 35 |
| full | motion | 136 | 468 | 88 | 36 |
| full | timing | 138 | 584 | 85 | 36 |
| full | sight | 140 | 522 | 76 | 36 |
| full | behaviour | 130 | 414 | 70 | 36 |
| full | response | 242 | 522 | 103 | 39 |
| full | injury | 350 | 522 | 90 | 37 |
| full | sej | 140 | 308 | 82 | 39 |
| full | exposure | 140 | 236 | 87 | 38 |
| full | secondary | 236 | 182 | 85 | 36 |
| full | cycle | 244 | 584 | 104 | 41 |
| full | entries | 212 | 414 | 70 | 36 |
| full | encounters | 294 | 414 | 82 | 39 |
| full | collisions | 388 | 414 | 89 | 39 |
| full | headon | 388 | 354 | 83 | 38 |
| full | controller | 242 | 308 | 98 | 40 |
| full | operator | 336 | 290 | 82 | 40 |
| full | placement | 342 | 236 | 99 | 44 |
| full | queue | 342 | 170 | 99 | 46 |
| full | avoidance | 388 | 122 | 87 | 35 |
| full | occupation | 242 | 356 | 102 | 30 |
| full | crash | 292 | 466 | 88 | 43 |
| full | harm | 424 | 298 | 85 | 58 |
| full | delay | 432 | 584 | 67 | 39 |
