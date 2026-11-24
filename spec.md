# Earthquake Shake-Down

## Platform
- Python desktop app using Tkinter, started with `python app.py`.
- Use Pymunk for 2D gravity, collisions, friction, rigid-body motion, and
  optional constraints. Do not use Matter.js or any browser physics engine.
- Calculations with NumPy are kept in their own module, separate from the
  window code.
- Diagrams drawn with Matplotlib are embedded in the Tkinter window.
- Use a controlled Tkinter timer loop (for example, `after`) to advance the
  simulation at a bounded update rate and redraw the interface. The loop must
  use measured elapsed time, avoid blocking the UI thread, and stop or pause
  immediately when the trial state requires it.

## Overview

Earthquake Shake-Down is a Python desktop app in which users design a small
2D building and test it on a simulated shake table. Players choose structural
pieces with real-world prices, arrange them into a building, and control the
table's amplitude and frequency. Pymunk simulates gravity, collisions, and
the resulting motion. The game ends immediately when the first piece falls,
while the 10-second checkpoint determines whether a trial qualifies for scoring.
The project is intended to teach basic structural and earthquake-motion
concepts through experimentation; it is not an engineering design tool or a
prediction of real building performance.

## Purpose

The app is an interactive introduction to how building structures respond to
earthquake-like motion. Users assemble a small 2D building from structural
pieces, choose how far and how quickly the ground moves, and observe whether
their design remains stable. The goal is to encourage experimentation with
different layouts and to show how structural choices, shaking strength, and
survival time affect the result. The app is an educational simulation, not a
prediction of how a real building would perform in an actual earthquake.

## Inputs

- The user can build a structure from pieces representing common building
  elements:
  - a foundation or base that starts on the shake table;
  - floor or deck pieces that support the structure;
  - vertical columns or posts;
  - horizontal beams;
  - diagonal braces or trusses;
  - optional wall panels or a roof for additional mass and lateral support.
- Beams are physics bodies only. Their dimensions, mass, collision shape, and
  price are used by the simulation and cost model; do not calculate beam stress,
  bending, deflection, section properties, or material strength in the first
  implementation.
- Connections between pieces are initially represented by Pymunk contact and
  collisions. The application must keep explicit support relationships between
  placed pieces, including which piece supports which other piece and the
  contact or connection that establishes that support. Flexible joints, bolts,
  and material failure are out of scope unless added later.
- Each piece has a defined shape, size, mass, and price. The initial piece
  catalog must provide those values so the physics and cost calculations are
  repeatable.
- The user sets the shake-table amplitude and frequency with sliders in the
  left control panel or compact numeric inputs directly beneath those sliders
  in the same panel. Keep each slider and numeric input synchronized.
- Amplitude describes how far the table moves side to side. It is the peak
  horizontal displacement in inches: larger amplitude means the ground moves
  farther in each direction.
- Frequency describes how quickly the table repeats that motion. It is measured
  in hertz (cycles per second): low frequency feels like slow swaying, while
  high frequency means faster back-and-forth motion. At the same amplitude,
  higher frequency also produces greater acceleration.
- The interface should show short helper text or tooltips with these
  explanations so users do not need earthquake experience to use the controls.
- The simulation uses seconds, inches, and pounds consistently in the user
  interface. Pymunk may use its own pixel scale, but conversions must be
  applied consistently at the simulation boundary.

## Calculations

### Physics model

- Use the Pymunk 2D physics engine for gravity, collisions, friction, and
  rigid-body motion.
- Gravity is downward at `g = 32.174 ft/s^2` (or its equivalent in the
  simulation unit system).
- The shake table's horizontal position is modeled as:

  `x(t) = A sin(2 pi f t)`

  where `A` is amplitude and `f` is frequency.
- The table's horizontal acceleration is:

  `a(t) = -A (2 pi f)^2 sin(2 pi f t)`

  Convert the input amplitude before using this equation:

  `A_ft = A_in / 12`

  where `A_in` is the input amplitude in inches and `A_ft` is the amplitude
  in feet.

  The maximum acceleration magnitude is therefore:

  `a_max = A_ft (2 pi f)^2`.

  This produces acceleration in `ft/s^2`; convert it to the displayed unit
  only after calculating it.
- The table moves for a fixed 10-second trial at the selected amplitude and
  frequency. The app does not need to draw the wave; the motion is applied to
  the table boundary in the physics simulation.
- Use the same initial conditions for every trial: pieces begin at rest, gravity
  is enabled, and the structure is placed on the table before the timer starts.

### Cost

- Each piece type has a fixed price in the piece catalog. The catalog displays
  the price before the user places the piece. Prices use U.S. dollars and
  should represent a comparable real-world retail or material cost for the
  piece.
- When a piece is placed, its catalog price is added exactly once. Cost is
  based on the piece type and quantity, not on its size, survival time, or
  performance during the trial.
- Total cost is:

  `total cost = sum(piece price for every placed piece)`

- Removing a piece subtracts that piece's price. Duplicating a piece adds
  another copy and another charge at the same catalog price.
- The displayed total updates whenever a piece is added or removed and remains
  fixed while the structure is being tested.
- When the piece catalog is created, record each price's source, date checked,
  assumed material, and assumed dimensions in `01_data`. These prices are
  representative estimates for the game, not construction bids or live quotes.

### Failure and result

- A piece has failed when it disconnects from a required support relationship.
  The application must track a support graph throughout the trial, including
  which piece supports each other piece and the contact or explicit connection
  that establishes that support.
- A disconnected piece is bad even if it has not yet reached the shake pad. End
  the trial at the first disconnect event and record that piece and time.
- A piece that later contacts the shake pad or crosses a canvas boundary is also
  failed, but the first disconnect event is the recorded failure when it occurs.
  A piece that only remains in place on the pad at the start of a trial is not
  considered failed.
- The moving pad is considered the bottom collision surface for boundary
  reporting. A body crossing a canvas side or falling beyond the lower canvas
  boundary is also recorded as failed when no earlier disconnect occurred.
- The game ends immediately when the first piece fails. If a beam, column,
  brace, floor, foundation, or any other piece disconnects or crosses the fall
  boundary, stop the shake and timer.
- Ten seconds is the minimum successful-survival checkpoint, not a hard trial
  limit. A structure that survives for 10 seconds or longer has reached the
  successful-survival state until a piece falls.
- A trial qualifies as a successful 10-second trial once no piece has fallen by
  the 10-second checkpoint. Report the amplitude, frequency, maximum
  acceleration, and total survival time.
- If a piece disconnects or falls before 10 seconds, report the failed piece and
  its elapsed time. The trial does not qualify as a successful 10-second trial,
  and the simulation stops immediately.
- Compare successful trials using the maximum acceleration `a_max`; the score
  is the highest successful `a_max` among the trials recorded in the session.
  If two trials have the same maximum acceleration, use the higher frequency
  as the tie-breaker.

## Outputs

- The table shakes according to the selected amplitude and frequency until the
  first disconnecting piece contacts the pad or leaves the table boundary.
- Show the current amplitude, frequency, elapsed time, trial status, total
  piece cost, and final score. Mark when the 10-second checkpoint is reached
  and continue showing the elapsed time afterward.
- Place the result summary directly underneath the simulation area. It must
  include the total cost along with trial status and, when available, the
  elapsed time and final score.
- Display a labeled line-item cost breakdown immediately above the total cost,
  grouping duplicate piece types with quantity and combined line cost.
- The top score consists of the highest maximum acceleration
  (`a_max = A_ft (2 pi f)^2`) from any trial that reaches the 10-second
  checkpoint without a piece falling. Display the corresponding amplitude,
  frequency, maximum shake speed, maximum acceleration, and total survival time.
  Maximum shake speed uses `v_max = A_ft (2 pi f)`. If successful
  trials have the same maximum acceleration, use the trial with the higher
  frequency as the tie-breaker.
- If no trial reaches the 10-second checkpoint, report that no qualifying score
  has been achieved instead of assigning a partial score.
- When a piece falls, identify it and show its elapsed fall time. End the game
  immediately and freeze the trial timer.

## Look and feel

- Use a bold, playful visual style that supports the earthquake and building
  theme without reducing readability.
- Place a logo and game title at the top of the page using a comic-book-style
  font.
- Use a mountain range picture as a full-page background behind the game.
  Keep the image subdued with a dark or translucent overlay so text, controls,
  and the structure remain easy to see.
- Place the controls on the left side of the page in a distinct panel with a
  readable background.
- Show a panel containing a dropdown of available pieces, the selected piece's
  dimensions, mass, and real-world cost, and a clear add-piece action.
- Render placed pieces with distinct visual treatments for foundations, floors,
  columns, beams, and braces so the assembled design reads like a simple
  building rather than a collection of generic blocks. Use material-inspired
  colors, textures, shading, borders, and depth cues for concrete, wood, steel,
  and bracing. These are visual approximations for education, not engineering
  material models.
- Place clearly labeled amplitude and frequency sliders in the left control
  panel, with smaller numeric inputs directly beneath them in the same panel.
  Include the plain-language helper explanations from the Inputs section.
- Keep result information, including total cost, in a status/results bar
  directly beneath the simulation area rather than in the simulation header.
- Keep the simulation area visually prominent and ensure the background does
  not obscure the structure or status information.
- The mountain image should be decorative rather than required to understand
  or operate the game. Provide appropriate alternative text or mark it as
  decorative when the image is implemented.
- Allow the window to be resized.

## Validation

### Free-fall check

For an object released from rest with no table contact, use:

`t = sqrt(2h/g)`

Case #1
g = 32.174 ft/s^2
h = 3 ft
t = 0.432

Case #2
g = 32.174 ft/s^2
h = 4 ft
t = 0.498

Case #3 
g = 32.174 ft/s^2
h= 5 ft
t = 0.558

### Shake-motion checks

- At amplitude `0`, table displacement and acceleration must both be `0`.
- At frequency `0`, table displacement is constant and maximum acceleration is
  `0`.
- With amplitude and frequency doubled independently, verify that `a_max`
  doubles when amplitude doubles and quadruples when frequency doubles.
- Verify that reaching 10 seconds with no fallen piece marks the trial as a
  successful checkpoint but does not stop the simulation.
- Verify that the game ends and the timer stops immediately after the first
  piece falls.

## Out of scope

- Do not show the actual displacement or acceleration waves.
- Do not add three-dimensional physics.
- Do not include weather, crowd, or structural-material simulation in the first
  implementation.

## Build Stages

After each stage is completed, run the Tkinter app and report the verified
local result. The app is a desktop application; do not create `index.html`,
GitHub Pages files, browser preview URLs, or browser-only implementation
requirements.

### Stage 1: Project foundation

- Create the initial Python entry point and Tkinter window without a build
  dependency.
- Establish the simulation area, control panel, status area, and resizable
  desktop layout.
- Add the amplitude and frequency sliders and smaller numeric inputs beneath
  them in the left control panel, with units and helper descriptions. Keep the
  two input methods synchronized and visually distinct.
- **Validation:** Run `python app.py`, confirm the window opens without errors,
  all planned regions are visible, and resizing remains usable. Enter
  nonnegative values in the compact numeric fields beneath the sliders and
  move both sliders. Confirm each slider and its matching numeric field stay
  synchronized without errors.

### Stage 2: Piece catalog and data

- Define the initial piece catalog in `01_data`, including type, dimensions,
  mass, shape, real-world price, and price source.
- Include at least a base, floor, column, beam, and brace or truss.
- Create a consistent mapping from catalog dimensions to Pymunk simulation
  units.
- **Validation:** Inspect every catalog entry and confirm it has a type,
  dimensions, mass, shape, price, and source. Independently sum a sample set
  of pieces and confirm the catalog total matches that hand calculation.

### Stage 3: Building editor

- Let the user choose a piece from a catalog dropdown, review its dimensions,
  mass, and price, and add it to the simulation area.
- Give each structural category a recognizable visual style and use sensible
  default placement for foundations, floors, columns, beams, and braces so a
  new structure starts with a building-like arrangement.
- Give each piece material-inspired texture, shading, and depth so it looks
  like a recognizable construction component instead of a flat colored block.
  Include subtle details such as concrete aggregate, wood grain, metal
  highlights, and brace fasteners without making labels or controls difficult
  to read.
- Support selecting, moving, and removing pieces before a trial starts.
- Update the displayed piece count and total cost whenever the structure
  changes.
- Prevent editing while a trial is running, or provide a clear reset action.
- **Validation:** Select each required type from the dropdown and confirm its
  dimensions, mass, and price update. Add one piece of each type, confirm the
  pieces have distinct material-inspired visual treatments, move one piece,
  remove one piece, and duplicate one piece. Confirm the visible structure,
  piece count, and total cost match the actions exactly.

### Stage 4: Physics and shake table

- Initialize Pymunk with gravity, collision boundaries, and the table.
- Add the sinusoidal horizontal table motion using the amplitude and frequency
  inputs. Move the table as a kinematic/static body by position so the
  documented displacement is applied consistently.
- Apply the documented unit conversions and show the current shaking values.
- Apply each catalog piece's simulated mass and stable collision properties.
- Use table position and velocity together in the sinusoidal motion so different
  piece shapes respond to lateral table movement through collisions and friction.
- Use enough collision iterations for pieces to remain stable at low motion and
  separate or fall realistically under stronger motion.
- Advance the physics with a controlled Tkinter timer loop using measured
  elapsed time. Keep animation and UI updates on the Tkinter event loop, avoid
  blocking the UI thread, and stop scheduling updates when the trial is paused,
  reset, or failed.
- Provide a prominent `Start shaking` button next to the Simulation area
  heading and a reset control. Starting the preview temporarily locks
  structure editing; resetting restores the design editor without changing the
  placed pieces.
- Show the calculated maximum acceleration in `ft/s^2` beside the shake-table
  inputs.
- Confirm that pieces begin at rest and that each trial starts from the same
  initial conditions.
- **Validation:** Run with amplitude `0` and confirm there is no horizontal
  table motion. Run with frequency `0` and confirm maximum acceleration is
  `0`. Double amplitude and confirm `a_max` doubles; double frequency and
  confirm `a_max` quadruples. Start and reset the physics preview and confirm
  editing is locked only while the preview is running and the original design
  returns after reset.

### Stage 5: Trial lifecycle and fall detection

- Turn the Stage 4 physics preview into a trial with Start, Pause/Resume, and
  Reset controls.
- Display elapsed trial time and the current trial state beneath the simulation.
- Detect when a piece loses a required support relationship, touches the moving
  shake pad, or crosses a boundary, and record the first failure event.
- Maintain and update the support graph as contacts change. A lost required
  support relationship ends the trial immediately, even before pad contact.
- Record each fallen piece and its fall time.
- Mark the 10-second checkpoint when no piece has fallen.
- End the trial immediately after the first piece disconnects or falls. Resetting
  must restore the original design and support relationships so it can be tried
  again.
- **Validation:** Start a stable trial and confirm the elapsed timer runs and
  the 10-second checkpoint appears without stopping the simulation. Pause and
  resume the trial and confirm elapsed time stops and continues appropriately.
  Start a deliberately unstable trial and confirm the disconnected or fallen
  piece is recorded, the shake and timer stop immediately, and reset restores
  the original structure.

### Stage 6: Scoring and results

- Calculate maximum acceleration from amplitude and frequency.
- Record each trial's amplitude, frequency, maximum acceleration, checkpoint
  status, fall times, and total survival time.
- Calculate the final score from the highest qualifying maximum acceleration and
  apply the documented frequency tie-breaker.
- Display the total cost, trial outcome, failed pieces, and final score.
- **Validation:** Record two successful trials and confirm the higher
  `a_max` becomes the score. Record equal-acceleration trials and confirm the
  higher frequency wins. Confirm that a trial failing before 10 seconds cannot
  become the final score.

### Stage 7: Visual design and accessibility

- Add the logo, comic-book styling, mountain range background, and contrast
  overlay.
- Add readable labels and helper text explaining amplitude and frequency.
- Keep the controls and simulation visible across screen sizes.
- Add appropriate keyboard access, focus states, and alternative-text handling
  for decorative imagery.
- Place Start trial, Pause/Resume, and Reset trial together in the Simulation
  area header so trial controls remain visible in one location.
- **Validation:** Navigate controls with the keyboard, confirm focus is visible,
  verify readable contrast over the mountain background, and confirm the
  simulation remains understandable when the background image is unavailable.

### Stage 8: Validation

- Run the free-fall and shake-motion checks in the Validation section.
- Test zero amplitude, zero frequency, duplicate pieces, piece removal, early
  falls, survival beyond 10 seconds, and first-piece trial ending.
- Check that cost totals and score selection match hand calculations.
- Run the desktop app and complete the checklist from Stages 1-7. Verify the
  same tested source runs with `python app.py`, confirm no unhandled errors
  occur, and verify the controlled timer loop, support-disconnection failure,
  and reset behavior during a complete test session.

## Features

### Score board
- Maintain a local score board that records completed trials and the top
  qualifying shake settings survived.
- Store trial history locally on the user's computer, for example in a JSON
  file managed by the desktop app.
- Keep usernames and cross-user comparison out of scope.
- Do not require a server, account, authentication, API, or network database.
- Provide a fixed Score board button in the upper-right corner of the window.
- Opening the button shows a local score-board panel on top of the page.
- Place an X close button in the upper-left corner of the score-board panel.
- The panel includes the highest qualifying score and persisted trial history.
- Close the panel with the X button, the Escape key, or by clicking outside
  it. Return keyboard focus to the Score board button after closing.
- Treat stored scores as local to the computer; closing and reopening the app
  must retain them.
- Clearing or resetting the local score data removes the local score board.

### Welds and Connections
- Include a mode where the player can add welds and connections to joints for
  extra rigid-body strength.
- Unlock the mode after a structure reaches the 10-second checkpoint with
  amplitude `5 in` and frequency `5 Hz`.
- After unlocking, show a Connections section below the shake-table controls
  in the left panel with a dropdown for `No connection` or `Weld joint`.
- In Weld joint mode, the player selects exactly two placed pieces, clicks
  `Add weld`, and receives a visual weld line between them.
- Welds are free and persist for the structure until pieces are removed or the
  structure is cleared. Reset trial restores the design editor and keeps welded
  joints; a new structure can add new welds.
- During physics, welded pieces use rigid Pymunk constraints so they resist
  separation and rotation more strongly than separate colliding pieces.
- Weld connections remain local to the desktop app and do not affect the catalog
  price or cross-user features.
- **Validation:** Run at 5 in / 5 Hz with no fall until 10 seconds and confirm
  Welds and Connections becomes visible and remains visible after reload.
  Select exactly two pieces, confirm Add weld enables, add the weld, and confirm
  a visual line appears. Remove one connected piece and confirm the weld line
  disappears. Start and reset a welded trial and confirm the structure returns
  with its weld configuration preserved.
