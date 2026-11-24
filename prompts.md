## 2026-11-24
- What I asked: Read `spec.md` and describe the plan for building the Python Tkinter desktop app before writing code, including files, beam calculations, potential issues, and refinements.
- What you changed: Added this request log entry; no application code was written.
- Whether it worked: Yes—the implementation plan was provided for review.

## 2026-11-24
- What I asked: Update `spec.md` before implementation to use Pymunk instead of Matter.js, treat beams as physics bodies only, remove `index.html` and browser requirements, track support relationships, and use a controlled timer loop.
- What you changed: Revised `spec.md` with the Python/Tkinter/Pymunk platform, controlled Tkinter animation loop, explicit support-graph disconnection failures, physics-only beam behavior, desktop-local score persistence, and desktop validation stages. No app code was created.
- Whether it worked: Yes—the requested specification changes were applied and verified with a diff/search review.

## 2026-11-24
- What I asked: Build the Python Tkinter/Pymunk earthquake shake-down app according to the updated plan and `spec.md`.
- What you changed: Created the app entry point, shared models, piece catalog, NumPy calculations, Pymunk simulation with support-relationship tracking, local score persistence, requirements file, and focused tests. Added checkpoint-trial recording on reset and installed the required runtime/test packages in the selected Python environment.
- Whether it worked: Yes—syntax compilation passed, all six tests passed, module imports succeeded, Pymunk smoke testing passed for the initial zero-shake steps, and editor diagnostics reported no errors. Interactive GUI behavior still requires running `python app.py` in a desktop session.

## 2026-11-24
- What I asked: Fix the inability to move pieces and make the shake table appear and shake.
- What you changed: Added canvas drag-and-drop piece movement, responsive world-to-canvas coordinate mapping, visible table rendering, animated table positioning, and correct inch conversion at the Pymunk simulation boundary.
- Whether it worked: Yes—six tests pass, the table smoke check reports a changed table position under shaking, and app/physics diagnostics report no errors.

## 2026-11-24
- What I asked: Remove the default structure at startup and make the physics less precise and more forgiving so pieces do not need to be touching at trial start.
- What you changed: The app now starts with an empty board, the first added piece is table-supported, and support validation uses broad center-distance tolerances instead of exact contact geometry while still detecting large separations.
- Whether it worked: Yes—8 tests pass, including empty-board and relaxed-support regression checks, and diagnostics report no errors.

## 2026-11-24
- What I asked: Make any column or other piece that falls off the shake table, or disconnects, fail the test, and record this behavior plus the recent changes in `spec.md`.
- What you changed: Added explicit fall-off detection for every piece, gave physical fall-off precedence over cascading support failures, added a regression test, and updated `spec.md` with the failure rule and recent empty-board, dragging, forgiving-support, visible-table, and unit-conversion changes.
- Whether it worked: Yes—9 tests pass, compilation passes, and all changed Python files report no diagnostics.

## 2026-11-24
- What I asked: Make every structural separation fail the test, including columns disconnecting from foundations, floors disconnecting from columns, and any other support combination.
- What you changed: Added per-support starting relative-position tracking, including foundation-to-table support, and fail when any child materially separates from its recorded parent relationship while preserving forgiving initial gaps. Added regression coverage for columns, floors, beams, and roofs, and documented the rule in `spec.md`.
- Whether it worked: Yes—10 tests pass, the smoke check detects a separated floor as `required support disconnected`, and diagnostics report no errors.

## 2026-11-24
- What I asked: Run all validation cases in `spec.md` against the app's beam/shake calculations and report expected versus actual values in a table.
- What you changed: Ran the full numeric validation set, the regression suite, live Tkinter checkpoint, pause/resume/reset, support-disconnection, table fall-off, and score tie-break scenarios. No application code was changed.
- Whether it worked: The executable calculation and lifecycle checks passed; the final report identifies UI-only or feature checks that cannot be represented as numeric beam calculations.

## 2026-11-24
- What I asked: Add saving and opening work as files, document the feature in `spec.md`, build it, let me try it in the app, and rerun the validation cases.
- What you changed: Added JSON work-file serialization in `workfiles.py`, Open/Save actions and File menu controls in `app.py`, round-trip and invalid-file tests, and a Work files section in `spec.md`.
- Whether it worked: Yes—12 tests pass, all calculation/physics regression cases pass, work round-trip restores 8 pieces, 9 support relationships, and `$201.00` cost, and diagnostics report no errors. The app is being launched for interactive use.

## 2026-11-24
- What I asked: Add a feature to export scoreboard results to CSV or Excel.
- What you changed: Added CSV export support in `exports.py`, Export CSV actions in the main window, File menu, and scoreboard panel, export-specific tests, and a scoreboard-export section in `spec.md`.
- Whether it worked: Yes—14 tests pass, CSV output contains 3 trial rows and 10 columns with the correct top-score marker and failed-piece data, all prior validation cases still pass, and diagnostics report no errors. The app is being relaunched for interactive use.

## 2026-11-24
- What I asked: Diagnose why the app could no longer be opened from the terminal.
- What you changed: Fixed the empty-board startup bug in `app.py` by providing a default value to the piece-ID calculation when no pieces are loaded.
- Whether it worked: Yes—the exact launch command now opens the Tkinter event loop, 8 tests pass, and the app reports no diagnostics. The process was stopped manually after confirming it stayed running.
