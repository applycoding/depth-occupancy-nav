# Build tasks: depth-occupancy-nav

Do the tasks in order, on a feature branch, following PLAN.md exactly. Deviate only if a pin or a test proves a step broken. If you do, record the reason and the measured data in `DEVIATIONS.md` and amend the plan before merge. **Never weaken a threshold, gate or mutant expectation to make CI green, and never make a red job green by writing `DEVIATIONS.md` alone.** If a gate fails, fix the implementation.

Every commit's author and committer is **Arpan Bom <applycoding@gmail.com>**. Do not add co-author trailers. Commit messages and repo text carry no tool attribution. The licence is **Apache-2.0**, and the project is simulation only / synthetic depth only.

A task is done only when its **Accept** checks pass.

## 1. Skeleton and licence

- Create the layout from PLAN.md section 8.
- `LICENSE` must be byte-identical to the official Apache-2.0 text (SHA-256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`).
- Write `NOTICE` as specified in PLAN.md section 8 and criterion 19, including Pillow and not OpenCV.
- Add a README stub that already says simulation only / synthetic depth, Apache-2.0, and that the methods are an original implementation inspired by known work.
- Put SPDX headers on authored source files.
- Add `pyproject.toml` so the core package installs as `depth_occupancy_nav` (Python 3.12).

**Accept:** `sha256sum LICENSE` matches, and `pip install -e .` works with no ROS or Node lookup.

## 2. Pins and dependencies

- Hash-pin `requirements.txt` (or an equivalent compiled file) for NumPy 2.5.4, Pillow 13.0.0, pytest 9.2.0, and ruff 0.17.4. Do not add opencv-python or opencv-python-headless.
- Add `.github/workflow-pins.md` listing every Actions SHA and version from PLAN.md section 3.
- Record the ROS image index digest, the linux/amd64 manifest digest, and navigation2 `1.3.14-1` in that file as well.

**Accept:** a clean install from the hashed requirements yields exactly those versions, and `python -c` prints them. The environment does not import `cv2`.

## 3. Camera, scene and renderer

- Implement the locked camera, the two AABBs, the ground plane, slabs intersection, and the analytic camera-Z renderer (PLAN.md section 5), including the unnormalized optical ray and the `t` / camera-Z range tests.
- Write unit tests for criterion 2 (optical axis and the four neighbour pixels, using the full-precision literals in PLAN.md) and criterion 3 (valid-pixel and hit-kind counts). Expected values are literals from PLAN.md, not recomputed by calling production code to build the expected table.

**Accept:** criteria 2 and 3 pass.

## 4. Back-projection and height filter

- Implement back-projection and the inclusive height band `z_min = 0.15`, `z_max = 1.50`.
- Tests: criterion 6, plus the kept / filtered / front_pts / side_pts counts from criterion 3.

**Accept:** criteria 3 (filter half) and 6 pass.

## 5. Ray walk and two-pass occupancy

- Implement Amanatides-Woo 2D traversal with the locked tie-break, zero-length, and out-of-grid endpoint rules, and the two-pass log-odds update, including OccupancyGrid conversion and log-odds clamp.
- Tests: criterion 4 (exact 28-cell list plus the tiny walk cases in section 5.5), criterion 5 (counts, the exact 22 occupied cells, probes, face clamp 3.5), a conflicting-evidence unit that one occupied increment after a free-saturated cell does not reach 100, and both mutants in criterion 12 with their measured counts.

**Accept:** criteria 4, 5 and 12 pass.

## 6. Planner and extra fixtures

- Implement 8-connected A* with unknown blocked and corner cutting forbidden, plus the 0.15 m inflation helper.
- Tests: criteria 7, 8 and 10 (height-filter mutant, including mid = 395), plus the tiny independent fixtures in criterion 8 (corner cutting, inflation-closed corridor, start equals goal, bad start).

**Accept:** criteria 7, 8 and 10 pass.

## 7. Noise, determinism and Pillow I/O

- Implement the noise model with the locked draw schedule in PLAN.md section 5.3, and the 16-bit millimetre PNG helpers in Pillow.
- Tests: criterion 9 (RMSE, noisy counts including mid = 13, noisy around path, in-process determinism) and criterion 11 (round trip within 0.5 mm).

**Accept:** criteria 9 and 11 pass.

## 8. Core job of the orchestrating workflow

- Write `.github/workflows/ci.yml` on `ubuntu-24.04` with SHA-pinned actions and jobs `core`, `ros`, `web`, and `pages` as in PLAN.md section 10. The `core` job: install hashed requirements, print versions, run ruff, run pytest, run the `grep -P` hygiene probe, scan, and failing fixture, run the authorship check on the PR head or pushed commits with full history, run the action-pin check. Never `ubuntu-latest`. No `continue-on-error` on these jobs.

**Accept:** criterion 13 holds on the PR head (the `core` job has **completed** green).

## 9. ROS 2 package and launch tests

- Build `depth_occupancy_nav_ros` (ament_python) that imports the core library and implements the node contract in PLAN.md section 6.
- Launch test A: node plus static TF, publish locked-scene depth and CameraInfo, assert criterion 14, plus the mismatched CameraInfo rejection case.
- Launch test B: Navfn with the locked static-only costmap, `use_start: true`, `allow_unknown: false`, and the path assertions in criterion 15. Explicit lifecycle and readiness probes. No `nav2_amcl`, no Gazebo.
- The `ros` job: `docker run` of the pinned Jazzy image, assert Debian versions `1.3.14-1`, upload the apt log, run tests A and B. This job is required. A failure fails CI.

**Accept:** criteria 14 and 15 pass in a completed green `ros` job.

## 10. Viewer

- Build the Vite + TypeScript + Canvas 2D viewer (PLAN.md section 7) with base `/depth-occupancy-nav/`.
- Vitest goldens against compact Python JSON as in criterion 16 (exact occupied cells and path lists, not counts alone). Half-even rounding in the TypeScript occupancy conversion.
- Playwright on the built site, following criterion 16 and section 7 (`data-occupied`, around length 51, shadow reports no path, slider changes the metric). Write `docs/demo.png` after the around-path state and commit it once from a local run.

**Accept:** criterion 16 passes, `tsc --noEmit` is clean, and `docs/demo.png` is committed.

## 11. README, NOTICE and docs (before merge)

- Finish the README: what the pipeline does; that a single frame marks the visible surface, not the solid volume; that the height filter is a height gate, not a fitted plane; that invalid pixels do not clear to max range; why the ROS distro is Jazzy (supported LTS, Python 3.12, not "the current LTS"); the scenario table with the measured counts and path costs; the mutants and what each one proves; how to run pytest, the ROS launch tests, the viewer, and the optional manual launch; simulation-only / synthetic-depth limits; a contrast with the sibling repos; "How this was verified", mapping criteria to tests; a link to the Pages demo; that CI runs Nav2 Navfn on the published map. Do not claim real-camera or real-robot validation. Required disclaimers about real cameras and real robots stay in the text.
- Finish NOTICE so it matches the packages actually used at the merge commit.

**Accept:** criteria 18, 19 and 20 hold on the branch that will be merged.

## 12. Pages job and live check (after merge)

- The `pages` job in `ci.yml` deploys the `web` job's `dist` artifact from the same run, only on a `main` push, after `core`, `ros` and `web` succeeded. Enable Pages with source "GitHub Actions".
- After the merge, confirm the completed Pages deploy and the live honesty labels.

**Accept:** criterion 17 holds after the merge.
