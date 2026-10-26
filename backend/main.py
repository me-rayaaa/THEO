from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from data_store import LapOutOfRange
from race_state import get_race_state
from race_changes import get_lap_changes
from analysis import build_analysis
from event_intelligence import build_event_summary
from theo_commentary import build_theo_commentary
from strategy_commentary import build_strategy_commentary
from rival_strategy_commentary import build_rival_strategy_commentary
from rival_strategy_decision import build_rival_strategy_decision
from team_engineer_strategy import build_team_engineer_strategy
from theo_intervention import build_theo_intervention

TOP_N = 10

app = FastAPI()


@app.exception_handler(LapOutOfRange)
def lap_out_of_range(request: Request, error: LapOutOfRange):
    # Неверный круг — понятный 404, а не 500.
    return JSONResponse(status_code=404, content={"detail": str(error)})

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "project": "THEO",
        "status": "running"
    }


@app.get("/api/race/{lap_number}")
def race(lap_number: int):
    race_state = get_race_state(lap_number)
    # Модель считает по всем 20 пилотам, экран показывает первые 10.
    race_state["drivers"] = race_state["drivers"][:TOP_N]
    return race_state


@app.get("/api/race/{lap_number}/top10")
def top10(lap_number: int):
    race_state = get_race_state(lap_number)

    return {
        "current_lap": race_state["current_lap"],
        "drivers": race_state["drivers"][:TOP_N]
    }


@app.get("/api/race/{lap_number}/weather")
def weather(lap_number: int):
    race_state = get_race_state(lap_number)

    return {
        "current_lap": race_state["current_lap"],
        "weather": race_state["weather"]
    }


@app.get("/api/race/{lap_number}/status")
def status(lap_number: int):
    race_state = get_race_state(lap_number)

    return {
        "current_lap": race_state["current_lap"],
        "race_status": race_state["race_status"]
    }


@app.get("/api/race/{lap_number}/changes")
def changes(lap_number: int):
    return {
        "lap": lap_number,
        "changes": get_lap_changes(lap_number)
    }


@app.get("/api/race/{lap_number}/analysis")
def analysis(lap_number: int):
    return build_analysis(lap_number)


@app.get("/api/race/{lap_number}/events")
def events(lap_number: int):
    return build_event_summary(lap_number)


@app.get("/api/race/{lap_number}/theo")
def theo(lap_number: int):
    return build_theo_commentary(lap_number)


@app.get("/api/race/{lap_number}/strategy/{driver_number}")
def strategy(lap_number: int, driver_number: int):
    return build_strategy_commentary(
        target_lap=lap_number,
        driver_number=driver_number
    )


@app.get(
    "/api/race/{lap_number}/rival-strategy/"
    "{driver_number}/{target_driver_number}"
)
def rival_strategy(
    lap_number: int,
    driver_number: int,
    target_driver_number: int
):
    return build_rival_strategy_commentary(
        target_lap=lap_number,
        driver_number=driver_number,
        target_driver_number=target_driver_number
    )


@app.get(
    "/api/race/{lap_number}/rival-decision/"
    "{driver_number}/{target_driver_number}"
)
def rival_decision(
    lap_number: int,
    driver_number: int,
    target_driver_number: int
):
    return build_rival_strategy_decision(
        target_lap=lap_number,
        driver_number=driver_number,
        target_driver_number=target_driver_number
    )


@app.get(
    "/api/race/{lap_number}/team-engineer/{driver_number}"
)
def team_engineer(
    lap_number: int,
    driver_number: int
):
    return build_team_engineer_strategy(
        target_lap=lap_number,
        driver_number=driver_number
    )


@app.get(
    "/api/race/{lap_number}/intervention/{driver_number}"
)
def intervention(
    lap_number: int,
    driver_number: int
):
    return build_theo_intervention(
        target_lap=lap_number,
        driver_number=driver_number
    )
