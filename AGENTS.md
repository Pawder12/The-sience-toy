# AGENTS.md

## Cursor Cloud specific instructions

### What this project is
`The Particle Simulator — Ultimate Science Edition` is a single **pygame desktop GUI**
application (Russian-language UI). There is one entry point (`main.py`) and no
web/server component, no test suite, and no linter configuration.

### Dependencies / how to run
- Third-party deps are only `numpy`, `pygame`, `numba` (installed into `.venv/`
  by the startup update script). `llvmlite` comes in transitively via `numba`.
- All other imports are Python standard library, plus local modules imported by
  their bare name (`from constants import *`, `from grid import Grid`, ...), so
  the app must be run from the repository root.
- Run the app: `.venv/bin/python main.py`
- Headless checks (imports / mod loading / grid logic) work without a display by
  setting `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`. The pygame surfarray
  render+save pipeline also works headless with the dummy driver.
- The `.venv` relies on the `python3-venv` system package (apt); it is already
  present on the VM snapshot and is not reinstalled by the update script.

### Mods / data
- Element/reaction definitions live as JSON in `mods/` and are loaded at startup
  by `mod_loader.load_mods("mods")` (currently 49 elements, 4 reactions).

### IMPORTANT: known pre-existing runtime bug (NOT an environment problem)
The application does **not** currently complete a simulation/render step, due to
bugs in the committed code (do not mistake this for a broken dev environment):
- `main.py` imports `step_simulation` (the 17-arg `@njit` core) but calls it with
  4 arguments; the intended 4-arg entry point is `simulator.step_simulation_wrapper`.
- Even via the wrapper, the `@njit(parallel=True)` core in `simulator.py` and the
  `@njit` helpers in `renderer.py` (e.g. `create_base_color_array`) receive plain
  Python `dict`s (`elements_data`, `reactions`), which Numba cannot type-infer, so
  compilation fails with a `TypingError`.
As a result `main.py` crashes on the first frame (before the first
`pygame.display.flip()`). Fixing this requires code changes and is out of scope
for environment setup.
