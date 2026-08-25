# THEO — Formula 1 AI Race Engineer

THEO is an AI-powered Formula 1 race analysis and strategy assistant designed to interpret race data, evaluate strategic situations and generate engineer-style recommendations during a Grand Prix.

The MVP combines race-state reconstruction, telemetry-derived analysis, tyre and pit-stop strategy, battle detection, undercut/overcut evaluation and an intervention layer that determines when THEO should actively communicate with the user.

## MVP 1.0

THEO MVP 1.0 was developed and validated using data from the 2025 Mexico City Grand Prix.

The current version reconstructs the race from historical data and processes it as if the race were happening live.

The architecture is designed so that historical replay can later be replaced by a live Formula 1 data feed without rebuilding the core analytical and strategic layers.

## Core capabilities

THEO MVP 1.0 can:

- reconstruct the race state for a selected lap;
- track driver positions and gaps;
- track tyre compound and tyre age;
- identify pit stops;
- calculate the last clean lap;
- filter laps affected by Race Control conditions;
- analyse driver pace;
- detect tyre degradation;
- analyse gaps and battles between drivers;
- estimate catch scenarios;
- evaluate pit windows;
- estimate post-pit rejoin position;
- analyse post-pit traffic;
- evaluate undercut opportunities;
- evaluate overcut opportunities;
- compare rival strategy options;
- detect VSC and other race-neutralisation conditions;
- generate Team Engineer strategy decisions;
- determine when THEO should actively intervene;
- suppress repeated strategic messages when the situation has not materially changed.

## Operating modes

The project is designed around two operating modes.

### Neutral Mode

THEO follows the race as a whole and provides analytical commentary about important developments.

### Team Engineer Mode

THEO focuses on a selected driver/team and behaves as a strategy assistant.

The Team Engineer layer can produce decisions such as:

- `PIT_NOW`
- `PIT_WINDOW_OPEN`
- `STAY_OUT`
- `HOLD_AND_MONITOR`

The decision is based on multiple analytical signals rather than a single rule.

## System architecture

The MVP follows a layered architecture:

```text
Race Data
    ↓
Race State
    ↓
Race Intelligence
    ↓
Pace / Tyres / Battles / Gaps
    ↓
Pit Strategy
    ↓
Undercut / Overcut
    ↓
Rival Strategy
    ↓
Team Engineer
    ↓
Race Neutralization
    ↓
THEO Intervention Layer
    ↓
API
    ↓
Frontend
```

This separation allows individual analytical components to be improved without rebuilding the entire application.

## Backend

The backend is written in Python.

Main groups of modules include:

### Race reconstruction

```text
race_state.py
race_replay.py
race_control.py
race_changes.py
race_neutralization.py
```

These modules reconstruct the race and provide contextual information about the current race state.

### Race data

```text
laps.py
positions.py
intervals.py
drivers.py
driver_data.py
standings.py
stints.py
pit_stops.py
weather.py
top10.py
```

These modules provide the underlying driver and race information used by the analytical layer.

### Race analysis

```text
pace_analysis.py
gap_analysis.py
battle_analysis.py
catch_prediction.py
tyre_degradation.py
tyre_intelligence.py
```

This layer interprets raw race information and identifies strategic signals.

### Pit strategy

```text
pit_gain_calibration.py
post_pit_gain.py
pit_strategy.py
undercut_analysis.py
overcut_analysis.py
```

The pit strategy layer estimates the consequences of stopping and evaluates alternative strategic scenarios.

Among other things, it considers:

- pit-loss time;
- projected rejoin position;
- traffic after the stop;
- tyre performance;
- recent pace;
- track-position loss;
- undercut potential;
- overcut potential.

### Strategy intelligence

```text
strategy_commentary.py
rival_strategy_commentary.py
rival_strategy_decision.py
team_engineer_strategy.py
```

This layer combines individual analytical signals into higher-level strategic recommendations.

### THEO intelligence

```text
event_intelligence.py
race_intelligence.py
theo_commentary.py
theo_intervention.py
```

The intervention layer determines whether a development is important enough for THEO to actively communicate it.

This prevents the assistant from repeating identical messages every lap.

## Intervention priorities

THEO classifies strategic developments by importance.

### CRITICAL

Examples:

- `PIT_NOW`;
- major strategic changes;
- strong pit triggers during race neutralisation.

### HIGH

Examples:

- `PIT_WINDOW_OPEN`;
- undercut or overcut opportunities;
- high-priority battles;
- strong degradation signals.

### INFO

Examples:

- stable `STAY_OUT`;
- `HOLD_AND_MONITOR`;
- race situations without a meaningful strategic change.

THEO compares the current strategic state with the previous lap.

If nothing meaningful changes, the message can be suppressed.

## Race neutralisation

THEO recognises race-neutralisation conditions separately from normal green-flag running.

The current strategy layer can distinguish conditions including:

```text
GREEN
VSC
SAFETY_CAR
RED_FLAG
YELLOW
```

During a VSC or Safety Car period, the pit opportunity can be elevated.

However, neutralisation alone does not automatically produce a `PIT_NOW` recommendation. It is combined with tyre, battle and strategic information.

## Race Control and clean laps

Race Control information is used to prevent abnormal laps from contaminating pace analysis.

The system can exclude laps affected by events such as:

- yellow flags;
- double yellow flags;
- slippery-track conditions;
- relevant Race Control restrictions;
- pit-related laps;
- other laps unsuitable for normal pace comparison.

This produces a cleaner pace dataset for downstream analysis.

## Test race

The current MVP uses:

**Mexico City Grand Prix 2025**

Race data is stored in:

```text
data/mexico_2025/
```

Current datasets include:

```text
drivers.json
intervals.json
laps.json
pit.json
position.json
race_control.json
stints.json
weather.json
```

## Project structure

```text
THEO/
│
├── backend/
│   ├── main.py
│   ├── race_state.py
│   ├── race_replay.py
│   ├── race_control.py
│   ├── race_changes.py
│   ├── race_neutralization.py
│   ├── pace_analysis.py
│   ├── gap_analysis.py
│   ├── battle_analysis.py
│   ├── catch_prediction.py
│   ├── tyre_degradation.py
│   ├── tyre_intelligence.py
│   ├── pit_strategy.py
│   ├── undercut_analysis.py
│   ├── overcut_analysis.py
│   ├── rival_strategy_decision.py
│   ├── team_engineer_strategy.py
│   ├── theo_commentary.py
│   ├── theo_intervention.py
│   │
│   ├── tests/
│   │   ├── _bootstrap.py
│   │   ├── test_mvp_end_to_end.py
│   │   ├── test_overcut_candidates.py
│   │   ├── test_overcut_scan.py
│   │   ├── test_pit_strategy.py
│   │   └── test_team_engineer_scan.py
│   │
│   └── tools/
│       ├── check_tyre_age.py
│       └── download_race_data.py
│
├── data/
│   └── mexico_2025/
│
├── frontend/
│   ├── app/
│   │   ├── RaceDashboard.tsx
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   │
│   └── package.json
│
├── .gitignore
└── README.md
```

## Frontend

The frontend is built with Next.js and TypeScript.

The main race interface is implemented in:

```text
frontend/app/RaceDashboard.tsx
```

The interface is designed to display race information together with THEO's analytical and strategic output.

## Running the backend

Activate the Python virtual environment.

From the project root:

```bash
source .venv/bin/activate
```

Move to the backend:

```bash
cd backend
```

Start the backend:

```bash
uvicorn main:app --reload
```

## Running the frontend

Open another terminal.

From the project root:

```bash
cd frontend
```

Start the development server:

```bash
npm run dev
```

The backend and frontend should run simultaneously during development.

## Testing

Tests are stored in:

```text
backend/tests/
```

The main full-system test is:

```text
test_mvp_end_to_end.py
```

From the `backend` directory run:

```bash
python3 tests/test_mvp_end_to_end.py
```

## MVP 1.0 validation

The final end-to-end test covered laps 10–71 of the Mexico City Grand Prix 2025.

Results:

```text
race_state_ok: 62
events_ok: 62
theo_ok: 62

strategy_ok: 620
team_engineer_ok: 620
intervention_ok: 620

errors: 0
no_data: 0
```

The test included:

- 62 race-state reconstructions;
- 620 strategy calculations;
- 620 Team Engineer calculations;
- 620 intervention calculations;
- critical strategy signals;
- high-priority strategy signals;
- VSC handling;
- end-of-race strategy calculations.

Final result:

```text
PASS - No runtime errors detected.
```

## MVP status

**THEO MVP 1.0 — COMPLETE**

The current version demonstrates the complete analytical chain from race data to an autonomous strategy intervention.

The MVP is intended as the foundation for further development rather than a finished Formula 1 strategy system.

Future versions can extend the model with additional race intelligence, improved strategic modelling, live data integration and more advanced AI-generated commentary.