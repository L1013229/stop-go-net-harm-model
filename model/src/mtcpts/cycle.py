"""Deterministic alternating one-lane control mechanics.

Two-phase alternating flow through a single-lane section of length L_s. Treated as a
two-phase signal with all-red clearance equal to the section transit time, following the
standard analytical treatment of one-lane work-zone operation (cf. Schonfeld-type models
and TRR analytical/simulation comparisons). Symmetric or asymmetric demand supported.

Under-saturation is required for a stable cycle: per direction, arrivals over a full
cycle must discharge within the green, q*T <= s*g. The MINIMUM stable cycle for given
demand exists because clearance time is fixed; practical policies pad green beyond the
minimum. Fixed-time policy = supplied greens; adaptive policy = greens sized to clear
the accumulated queue plus a margin (a simple model of MTC/actuated behaviour).

All rates in vehicles/second internally; distances m; speeds m/s; times s.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CycleGeometry:
    section_length_m: float          # controlled single-lane length incl. tapers
    platoon_speed_ms: float          # operating speed through the section

    @property
    def clearance_s(self) -> float:
        """All-red: time for the last released vehicle to traverse the section."""
        return self.section_length_m / self.platoon_speed_ms


@dataclass(frozen=True)
class CyclePlan:
    green1_s: float
    green2_s: float
    clearance_s: float

    @property
    def cycle_s(self) -> float:
        return self.green1_s + self.green2_s + 2.0 * self.clearance_s

    def red_s(self, direction: int) -> float:
        """Red duration facing a direction = other green + both clearances."""
        other = self.green2_s if direction == 1 else self.green1_s
        return other + 2.0 * self.clearance_s


def min_stable_greens(q1_vps: float, q2_vps: float, sat_vps: float,
                      clearance_s: float, margin: float = 1.15) -> CyclePlan:
    """Smallest greens (scaled by margin) that clear each direction each cycle.

    Solves g_i >= q_i * T / s with T = g1 + g2 + 2c. Closed form for the joint
    minimum: let a_i = q_i / s. Stability needs a1 + a2 < 1.
    g1 = a1 * 2c / (1 - a1 - a2), g2 likewise; margin scales both.
    """
    a1, a2 = q1_vps / sat_vps, q2_vps / sat_vps
    if a1 + a2 >= 1.0:
        raise ValueError(f"oversaturated: a1+a2={a1 + a2:.3f} >= 1")
    base = 2.0 * clearance_s / (1.0 - a1 - a2)
    return CyclePlan(green1_s=margin * a1 * base, green2_s=margin * a2 * base,
                     clearance_s=clearance_s)


@dataclass(frozen=True)
class DirectionCycleStats:
    arrivals_per_cycle: float
    stopped_per_cycle: float         # arrive during effective red (join a queue)
    f_stop: float                    # stopped / arrivals (per direction)
    max_queue_veh: float             # deterministic peak queue
    platoon_out_duration_s: float    # time the direction's platoon occupies release window


def direction_stats(q_vps: float, plan: CyclePlan, direction: int,
                    sat_vps: float) -> DirectionCycleStats:
    """Deterministic D/D uniform-arrival cycle statistics for one direction."""
    T = plan.cycle_s
    red = plan.red_s(direction)
    green = plan.green1_s if direction == 1 else plan.green2_s
    arr = q_vps * T
    stopped_red = q_vps * red
    # vehicles arriving in green while the queue still discharges also stop (join tail)
    t_clear = stopped_red / max(sat_vps - q_vps, 1e-9)   # queue-dissipation time into green
    t_clear = min(t_clear, green)
    stopped = stopped_red + q_vps * t_clear
    f_stop = min(stopped / arr, 1.0) if arr > 0 else 0.0
    max_q = stopped_red  # peak standing queue at green onset (veh)
    # release platoon: discharge at saturation for t_clear then free arrivals
    platoon_dur = t_clear + (green - t_clear)
    return DirectionCycleStats(arrivals_per_cycle=arr, stopped_per_cycle=stopped,
                               f_stop=f_stop, max_queue_veh=max_q,
                               platoon_out_duration_s=platoon_dur)


def opposing_occupancy_fraction(plan: CyclePlan, geom: CycleGeometry, q_opp_vps: float,
                                sat_vps: float, direction: int) -> float:
    """Fraction of a direction's red during which the single-lane section contains
    at least one OPPOSING vehicle. Deterministic approximation:

    The opposing platoon enters over its green (duration g_opp, discharge profile:
    saturation for t_clear then arrival rate), and the section holds vehicles from
    first entry until last entry + transit. Within the red facing `direction`
    (= g_opp + 2c), occupied window ~= (last_entry - first_entry) + tau_s, where
    first_entry = 0 (green onset), last_entry = effective release span <= g_opp.
    """
    g_opp = plan.green2_s if direction == 1 else plan.green1_s
    red = plan.red_s(direction)
    tau_s = geom.clearance_s
    opp = direction_stats(q_opp_vps, plan, 2 if direction == 1 else 1, sat_vps)
    # release span: all stopped discharge at saturation, then free-flow arrivals cross in green
    release_span = min(g_opp, opp.stopped_per_cycle / max(sat_vps, 1e-9) +
                       max(0.0, g_opp - opp.stopped_per_cycle / max(sat_vps, 1e-9)))
    if opp.arrivals_per_cycle <= 0:
        return 0.0
    occupied = min(release_span + tau_s, red)
    return occupied / red
