# SPDX-License-Identifier: Apache-2.0
"""PLAN.md section 9 success criteria (core)."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np
import pytest

from depth_occupancy_nav.backproject import pixel_to_map
from depth_occupancy_nav.camera import CX, CY, FX, FY, Camera
from depth_occupancy_nav.grid import (
    L_FREE,
    L_MAX,
    L_OCC,
    LogOddsGrid,
    log_odds_to_prob,
    ray_walk_2d,
    update_grid_from_depth,
)
from depth_occupancy_nav.height_filter import height_keep_mask
from depth_occupancy_nav.io_png import decode_depth_png_mm, encode_depth_png_mm
from depth_occupancy_nav.noise import add_depth_noise, depth_rmse
from depth_occupancy_nav.planner import _can_step, astar, inflate_grid, path_enters_aabb
from depth_occupancy_nav.render import render_depth
from depth_occupancy_nav.scene import FRONT_BOX

LICENSE_SHA = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"

# Hygiene CI asserts this marker exists; do not add banned patterns below.
SHOULD_FAIL_HYGIENE_FIXTURE = "marker-only"

FRONT_OCCUPIED = [
    (37, 25, 2.75, -0.45),
    (37, 26, 2.75, -0.35),
    (37, 27, 2.75, -0.25),
    (37, 28, 2.75, -0.15),
    (37, 29, 2.75, -0.05),
    (37, 30, 2.75, 0.05),
    (37, 31, 2.75, 0.15),
    (37, 32, 2.75, 0.25),
    (37, 33, 2.75, 0.35),
    (37, 34, 2.75, 0.45),
]

SIDE_OCCUPIED = [
    (50, 42, 4.05, 1.25),
    (52, 42, 4.25, 1.25),
    (54, 42, 4.45, 1.25),
    (50, 43, 4.05, 1.35),
    (50, 44, 4.05, 1.45),
    (50, 45, 4.05, 1.55),
    (50, 46, 4.05, 1.65),
    (50, 47, 4.05, 1.75),
    (50, 48, 4.05, 1.85),
    (50, 49, 4.05, 1.95),
    (50, 50, 4.05, 2.05),
    (50, 51, 4.05, 2.15),
]

NEIGHBOR_EXPECTED = {
    (39, 29): (2.75, 0.0198464155033934, 0.8198464155033934),
    (40, 29): (2.75, -0.0198464155033934, 0.8198464155033934),
    (39, 30): (2.75, 0.0198464155033934, 0.7801535844966067),
    (40, 30): (2.75, -0.0198464155033934, 0.7801535844966067),
}


@pytest.fixture(scope="module")
def depth_image():
    depth, kinds = render_depth()
    return depth, kinds


def test_criterion_1_license():
    data = Path("LICENSE").read_bytes()
    assert hashlib.sha256(data).hexdigest() == LICENSE_SHA


def test_criterion_2_optical_axis(depth_image):
    depth, _ = depth_image
    cam = Camera()
    assert abs(FX - 69.2820323027551) < 1e-12
    assert abs(FY - 69.2820323027551) < 1e-12
    assert abs(L_OCC - 0.8472978603872037) < 1e-15
    assert abs(L_FREE - (-0.6190392084062235)) < 1e-15
    assert abs(log_odds_to_prob(L_OCC) - 0.7) < 1e-15
    assert abs(log_odds_to_prob(L_FREE) - 0.35) < 1e-15

    pt = pixel_to_map(CX, CY, 2.75, cam)
    assert abs(pt[0] - 2.75) < 1e-12 and abs(pt[1]) < 1e-12 and abs(pt[2] - 0.80) < 1e-12

    for u, v in ((39, 29), (40, 29), (39, 30), (40, 30)):
        z = depth[v, u]
        assert abs(z - 2.75) < 1e-12
        pt = pixel_to_map(float(u), float(v), z, cam)
        ex = NEIGHBOR_EXPECTED[(u, v)]
        assert np.linalg.norm(pt - np.array(ex)) < 1e-12
        assert abs(pt[0] - 2.75) < 1e-12


def test_criterion_3_renderer_counts(depth_image):
    depth, kinds = depth_image
    valid = int(np.sum(depth > 0))
    assert valid == 2434
    fb = int(np.sum(kinds == "front_box"))
    gr = int(np.sum(kinds == "ground"))
    sb = int(np.sum(kinds == "side_box"))
    assert fb == 660 and gr == 1471 and sb == 303


def test_criterion_3_height_filter_counts(depth_image):
    depth, kinds = depth_image
    cam = Camera()
    kept = filtered = front_pts = side_pts = 0
    for v in range(cam.height):
        for u in range(cam.width):
            z = depth[v, u]
            if z <= 0:
                continue
            pt = pixel_to_map(float(u), float(v), z, cam)
            if height_keep_mask(pt.reshape(1, 3))[0]:
                kept += 1
                if kinds[v, u] == "front_box":
                    front_pts += 1
                if kinds[v, u] == "side_box":
                    side_pts += 1
            else:
                filtered += 1
    assert kept == 823 and filtered == 1611
    assert front_pts == 572 and side_pts == 251


def test_criterion_4_ray_walk():
    walk = ray_walk_2d(0, 0, 2.75, 0)
    expected = [(10 + i, 30) for i in range(28)]
    assert walk == expected

    zlen = ray_walk_2d(0.5, 0.0, 0.5, 0.0)
    assert zlen == [(15, 30)]

    neg_x = ray_walk_2d(0.0, 0.0, -0.5, 0.0)
    assert neg_x == [(10, 30), (9, 30), (8, 30), (7, 30), (6, 30), (5, 30)]

    tie = ray_walk_2d(0.05, 0.05, 0.25, 0.25)
    assert tie == [(10, 30), (11, 30), (11, 31), (12, 31), (12, 32)]

    outside = ray_walk_2d(0.0, 0.0, 10.0, 0.0)
    assert outside == [(ix, 30) for ix in range(10, 80)]

    from depth_occupancy_nav.grid import LogOddsGrid, _two_pass_free_then_occ

    g = LogOddsGrid.empty()
    rays = [
        {
            "kept": True,
            "occ_endpoint": True,
            "end_cell": (100, 30),
            "walk": [(10, 30), (11, 30)],
        }
    ]
    _two_pass_free_then_occ(g, rays)
    assert g.counts()["occupied"] == 0


def test_prob_to_occupancy_value_half_even():
    from depth_occupancy_nav.grid import prob_to_occupancy_value

    assert prob_to_occupancy_value(0.625, True) == 62
    assert prob_to_occupancy_value(0.565, True) == 56
    assert prob_to_occupancy_value(0.555, True) == 56


def test_criterion_5_occupancy(depth_image):
    depth, _ = depth_image
    g = update_grid_from_depth(depth)
    c = g.counts()
    assert c == {"occupied": 22, "free": 1698, "unknown": 3080, "mid": 0}
    vals = g.occupancy_values()
    occ_cells = {(ix, iy) for iy in range(60) for ix in range(80) if vals[iy, ix] == 100}
    expected = {(t[0], t[1]) for t in FRONT_OCCUPIED + SIDE_OCCUPIED}
    assert occ_cells == expected
    assert abs(g.log_odds[30, 37] - L_MAX) < 1e-12
    probes = {
        (2.65, 0): 0,
        (2.75, 0): 100,
        (2.95, 0): -1,
        (3.50, 0): -1,
        (0.50, 0): 0,
        (1.50, 0): 0,
        (5.50, -1.50): 0,
        (4.05, 1.70): 100,
    }
    for xy, exp in probes.items():
        assert g.value_at_world(xy[0], xy[1]) == exp


def test_conflicting_evidence_after_free_saturation():
    g = LogOddsGrid.empty()
    g.log_odds[30, 30] = -2.0
    g.updated[30, 30] = True
    g.add_occ(30, 30)
    p = log_odds_to_prob(g.log_odds[30, 30])
    assert g.occupancy_values()[30, 30] != 100
    assert p < 0.65


def test_criterion_6_height_filter_unit():
    assert not height_keep_mask(np.array([[0.0, 0.0, 0.0]]))[0]
    assert height_keep_mask(np.array([[0.0, 0.0, 0.80]]))[0]
    assert not height_keep_mask(np.array([[0.0, 0.0, 1.60]]))[0]
    assert height_keep_mask(np.array([[0.0, 0.0, 0.15]]))[0]
    assert height_keep_mask(np.array([[0.0, 0.0, 1.50]]))[0]
    assert not height_keep_mask(np.array([[0.0, 0.0, 0.149999]]))[0]
    assert not height_keep_mask(np.array([[0.0, 0.0, 1.5000001]]))[0]


def test_criterion_7_planner(depth_image):
    depth, _ = depth_image
    grid_vals = update_grid_from_depth(depth).occupancy_values()
    open_r = astar(grid_vals, (0.5, 0.0), (1.5, 0.0))
    assert open_r.cells is not None
    assert len(open_r.cells) == 11
    assert abs(open_r.cost - 10.0) < 1e-12
    assert open_r.cells == [(15 + i, 30) for i in range(11)]

    around = astar(grid_vals, (0.5, 0.0), (5.5, -1.5))
    assert around.cells is not None
    assert len(around.cells) == 51
    assert around.cells[0] == (15, 30) and around.cells[-1] == (65, 15)
    expected_cost = 35 + 15 * math.sqrt(2)
    assert abs(around.cost - expected_cost) < 1e-12

    shadow = astar(grid_vals, (0.5, 0.0), (5.5, 0.0))
    inside = astar(grid_vals, (0.5, 0.0), (2.95, 0.0))
    assert shadow.cells is None and inside.cells is None

    from depth_occupancy_nav.grid import GridConfig

    cfg = GridConfig()
    assert not path_enters_aabb(
        around.cells, cfg, FRONT_BOX.xmin, FRONT_BOX.xmax, FRONT_BOX.ymin, FRONT_BOX.ymax
    )


def test_criterion_8_inflation(depth_image):
    depth, _ = depth_image
    grid_vals = update_grid_from_depth(depth).occupancy_values()
    infl = inflate_grid(grid_vals, 0.15, 0.10)
    assert int(np.sum(infl == 100)) == 130
    around = astar(infl, (0.5, 0.0), (5.5, -1.5))
    assert around.cells is not None and len(around.cells) == 51
    expected_cost = 35 + 15 * math.sqrt(2)
    assert abs(around.cost - expected_cost) < 1e-12
    for ix, iy in around.cells:
        assert grid_vals[iy, ix] != 100
        assert infl[iy, ix] == 0

    from depth_occupancy_nav.grid import GridConfig

    cfg = GridConfig(resolution=0.10, origin_x=0.0, origin_y=0.0, width=5, height=5)
    corridor = np.full((5, 5), -1, dtype=np.int32)
    corridor[2, :] = 0
    corridor[2, 2] = 100
    infl_c = inflate_grid(corridor, 0.15, 0.10)
    assert astar(infl_c, (0.05, 0.25), (0.45, 0.25), cfg).cells is None

    corner = np.zeros((3, 3), dtype=np.int32)
    corner[0, 1] = 100
    assert not _can_step(corner, 0, 0, 1, 1)
    corner[0, 1] = 0
    assert _can_step(corner, 0, 0, 1, 1)
    tiny = GridConfig(resolution=0.10, origin_x=0.0, origin_y=0.0, width=3, height=3)
    same = astar(corner, (0.05, 0.05), (0.05, 0.05), tiny)
    assert same.cells == [(0, 0)] and same.cost == 0.0
    blocked = corner.copy()
    blocked[0, 0] = 100
    assert astar(blocked, (0.05, 0.05), (0.25, 0.25), tiny).cells is None


def test_criterion_9_noise(depth_image):
    depth, _ = depth_image
    noisy1 = add_depth_noise(depth, 1)
    noisy2 = add_depth_noise(depth, 1)
    assert np.array_equal(noisy1, noisy2)
    rmse, dropped = depth_rmse(depth, noisy1)
    assert dropped == 0
    assert abs(rmse - 0.0364728080413652) < 1e-9
    gn = update_grid_from_depth(noisy1)
    c = gn.counts()
    assert c["occupied"] == 41 and c["free"] == 1684 and c["unknown"] == 3062 and c["mid"] == 13
    around = astar(gn.occupancy_values(), (0.5, 0.0), (5.5, -1.5))
    assert around.cells is not None and len(around.cells) == 51
    d2a, d2b = render_depth()[0], render_depth()[0]
    assert np.array_equal(d2a, d2b)
    g1 = update_grid_from_depth(d2a)
    g2 = update_grid_from_depth(d2b)
    assert np.array_equal(g1.occupancy_values(), g2.occupancy_values())


def test_criterion_10_height_mutant(depth_image):
    depth, _ = depth_image
    g = update_grid_from_depth(depth, mode="height_mutant")
    c = g.counts()
    assert c == {"occupied": 78, "free": 1247, "unknown": 3080, "mid": 395}
    grid_vals = g.occupancy_values()
    assert astar(grid_vals, (0.5, 0.0), (5.5, -1.5)).cells is None
    assert astar(grid_vals, (0.5, 0.0), (1.5, 0.0)).cells is not None
    assert grid_vals[30, 15] == 0 and grid_vals[30, 25] == 0
    assert grid_vals[30, 28] == 100
    assert grid_vals[30, 29] == 100
    assert grid_vals[30, 30] == 100


def test_criterion_11_png_roundtrip(depth_image):
    depth, _ = depth_image
    raw = encode_depth_png_mm(depth)
    back = decode_depth_png_mm(raw)
    mask = depth > 0
    err = np.max(np.abs(back[mask] - depth[mask]))
    assert err < 0.0005
    assert np.all(back[~mask] == 0)


def test_criterion_12_one_pass_mutants(depth_image):
    depth, _ = depth_image
    for mode, exp in (
        ("one_pass_m1", {"occupied": 0, "free": 1709, "unknown": 3080, "mid": 11}),
        ("one_pass_m2", {"occupied": 0, "free": 1714, "unknown": 3080, "mid": 6}),
    ):
        g = update_grid_from_depth(depth, mode=mode)
        assert g.counts() == exp
        assert g.occupancy_values()[30, 37] == 0
    base = update_grid_from_depth(depth)
    assert base.occupancy_values()[30, 37] == 100
    assert base.counts()["occupied"] == 22
