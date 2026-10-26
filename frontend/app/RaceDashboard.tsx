"use client";

import { useEffect, useState } from "react";

type Driver = {
  driver_number: number;
  position: number;
  name: string;
  team: string;
  gap: number | string | null;
  compound: string;
  tyre_age: number | null;
  pit_stops: number;
  last_clean_lap: number | null;
};

type RaceState = {
  grand_prix: string;
  current_lap: number;
  race_status: string;
  weather: {
    air_temperature: number;
    track_temperature: number;
    rainfall: number;
    humidity: number;
    wind_speed: number;
  } | null;
  drivers: Driver[];
};

type PitEvent = {
  type: string;
  driver: string;
  position_from?: number;
  position_to?: number;
  tyre_from?: string;
  tyre_to?: string;
};

type Top10Event = {
  type: string;
  driver: string;
  position: number;
};

type EventSummary = {
  lap: number;
  pit_events: PitEvent[];
  top10_events: Top10Event[];
  other_position_changes: number;
};

type TheoMessage = {
  type: string;
  priority: string;
  message: string;
};

type TheoCommentary = {
  lap: number;
  messages: TheoMessage[];
};

type StrategyData = {
  lap: number;
  driver: string | null;
  recommendation: string;
  best_lap: number | null;
  optimal_window: number[];
  traffic_level: string | null;
  projected_rejoin_position: number | null;
  message: string;
};

type RivalDecisionData = {
  lap: number;
  driver: string;
  target: string;
  undercut_status: string;
  overcut_status: string;
  undercut_quality: number | null;
  overcut_quality: number | null;
  quality_difference: number;
  decision: string;
  message: string;
};

type TeamEngineerData = {
  lap: number;
  driver: string;
  position: number;
  decision: string;
  pit_recommendation: string;
  degradation_level: string;
  rival_decision: string | null;
  battle_priority: string | null;
  race_status: string;
  neutralized: boolean;
  pit_now_trigger: boolean;
  pit_window_trigger: boolean;
  message: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const START_LAP = 2;
const END_LAP = 71; // должен совпадать с LAST_LAP в backend/data_store.py

// null — если backend ответил ошибкой; AbortError пробрасывается дальше.
async function fetchJson<T>(
  path: string,
  signal: AbortSignal
): Promise<T | null> {
  const response = await fetch(`${API_URL}${path}`, { signal });

  if (!response.ok) {
    return null;
  }

  return response.json();
}

export default function RaceDashboard() {
  const [lap, setLap] = useState(25);

  const [race, setRace] = useState<RaceState | null>(null);
  const [events, setEvents] = useState<EventSummary | null>(null);
  const [theo, setTheo] = useState<TheoCommentary | null>(null);

  const [selectedDriver, setSelectedDriver] = useState<number | null>(null);

  const [teamEngineer, setTeamEngineer] =
    useState<TeamEngineerData | null>(null);

  const [strategy, setStrategy] =
    useState<StrategyData | null>(null);

  const [rivalStrategy, setRivalStrategy] =
    useState<RivalDecisionData | null>(null);

  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Отменяем запросы прошлого круга, чтобы они не перезаписали новый.
    const controller = new AbortController();

    async function loadRace() {
      try {
        const [raceData, eventsData, theoData] = await Promise.all([
          fetchJson<RaceState>(`/api/race/${lap}`, controller.signal),
          fetchJson<EventSummary>(`/api/race/${lap}/events`, controller.signal),
          fetchJson<TheoCommentary>(`/api/race/${lap}/theo`, controller.signal),
        ]);

        if (!raceData || !eventsData || !theoData) {
          setError(`No data for lap ${lap}`);
          return;
        }

        setError(null);
        setRace(raceData);
        setEvents(eventsData);
        setTheo(theoData);

        setSelectedDriver(
          (current) => current ?? raceData.drivers[0]?.driver_number ?? null
        );
      } catch {
        if (!controller.signal.aborted) {
          setError("Backend is unavailable");
        }
      }
    }

    loadRace();

    return () => controller.abort();
  }, [lap]);

  useEffect(() => {
    if (selectedDriver === null) {
      setTeamEngineer(null);
      return;
    }

    const controller = new AbortController();

    async function loadTeamEngineer() {
      try {
        const data = await fetchJson<TeamEngineerData>(
          `/api/race/${lap}/team-engineer/${selectedDriver}`,
          controller.signal
        );

        setTeamEngineer(
          data && data.decision !== "NO_DATA" ? data : null
        );
      } catch {
        if (!controller.signal.aborted) {
          setTeamEngineer(null);
        }
      }
    }

    loadTeamEngineer();

    return () => controller.abort();
  }, [lap, selectedDriver]);

  useEffect(() => {
    if (selectedDriver === null) {
      setStrategy(null);
      return;
    }

    const controller = new AbortController();

    async function loadStrategy() {
      try {
        const data = await fetchJson<StrategyData>(
          `/api/race/${lap}/strategy/${selectedDriver}`,
          controller.signal
        );

        // NO_DATA раньше доходил до рендера и ронял страницу.
        setStrategy(
          data && data.recommendation !== "NO_DATA" ? data : null
        );
      } catch {
        if (!controller.signal.aborted) {
          setStrategy(null);
        }
      }
    }

    loadStrategy();

    return () => controller.abort();
  }, [lap, selectedDriver]);

  useEffect(() => {
    if (
      selectedDriver === null ||
      race === null
    ) {
      setRivalStrategy(null);
      return;
    }

    // Ждём данные нового круга, иначе соперник берётся из прошлого.
    if (race.current_lap !== lap) {
      return;
    }

    const driver = race.drivers.find(
      (item) =>
        item.driver_number === selectedDriver
    );

    if (
      !driver ||
      driver.position === 1
    ) {
      setRivalStrategy(null);
      return;
    }

    const target = race.drivers.find(
      (item) =>
        item.position === driver.position - 1
    );

    if (!target) {
      setRivalStrategy(null);
      return;
    }

    const controller = new AbortController();
    const targetNumber = target.driver_number;

    async function loadRivalStrategy() {
      try {
        const data = await fetchJson<RivalDecisionData>(
          `/api/race/${lap}/rival-decision/${selectedDriver}/${targetNumber}`,
          controller.signal
        );

        setRivalStrategy(
          data && data.decision !== "NO_DATA" ? data : null
        );
      } catch {
        if (!controller.signal.aborted) {
          setRivalStrategy(null);
        }
      }
    }

    loadRivalStrategy();

    return () => controller.abort();
  }, [lap, selectedDriver, race]);

  // На последнем круге воспроизведение останавливается само,
  // без вызова setPlaying внутри setLap.
  const isPlaying = playing && lap < END_LAP;

  useEffect(() => {
    if (!isPlaying) {
      return;
    }

    const timer = setInterval(() => {
      setLap((currentLap) =>
        Math.min(END_LAP, currentLap + 1)
      );
    }, 1000);

    return () => clearInterval(timer);
  }, [isPlaying]);

  if (
    !race ||
    !events ||
    !theo
  ) {
    return (
      <main className="min-h-screen bg-black text-white p-10">
        {error ?? "Loading..."}
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-black text-white p-10">
      <div className="max-w-6xl mx-auto">

        <div className="mb-10">
          <h1 className="text-5xl font-bold">
            THEO
          </h1>

          <p className="text-zinc-400 mt-2">
            Formula 1 Race Intelligence
          </p>
        </div>

        {error && (
          <div className="mb-6 text-red-400">
            {error}
          </div>
        )}
        <div className="flex gap-4 mb-8">
          <button
            onClick={() =>
              setLap((value) =>
                Math.max(
                  START_LAP,
                  value - 1
                )
              )
            }
            className="border border-zinc-700 px-4 py-2 rounded"
          >
            Previous
          </button>

          <button
            onClick={() =>
              setPlaying(!isPlaying)
            }
            className="border border-zinc-700 px-4 py-2 rounded"
          >
            {isPlaying ? "Pause" : "Play"}
          </button>

          <button
            onClick={() =>
              setLap((value) =>
                Math.min(
                  END_LAP,
                  value + 1
                )
              )
            }
            className="border border-zinc-700 px-4 py-2 rounded"
          >
            Next
          </button>
        </div>

        <div className="flex gap-8 mb-8">

          <div>
            <p className="text-zinc-500 text-sm">
              GRAND PRIX
            </p>

            <p className="text-xl">
              {race.grand_prix}
            </p>
          </div>

          <div>
            <p className="text-zinc-500 text-sm">
              LAP
            </p>

            <p className="text-xl">
              {race.current_lap}
            </p>
          </div>

          <div>
            <p className="text-zinc-500 text-sm">
              STATUS
            </p>

            <p className="text-xl">
              {race.race_status}
            </p>
          </div>

        </div>

        {race.weather && (
          <div className="mb-10 text-zinc-400">
            Air{" "}
            {race.weather.air_temperature}°C
            {" · "}
            Track{" "}
            {race.weather.track_temperature}°C
            {" · "}
            Humidity{" "}
            {race.weather.humidity}%
            {" · "}
            Wind{" "}
            {race.weather.wind_speed} m/s
          </div>
        )}

        <div className="grid grid-cols-3 gap-8">

          <div className="col-span-2">

            <h2 className="text-2xl font-semibold mb-4">
              TOP 10
            </h2>

            <div className="space-y-2">

              {race.drivers.map((driver) => (

                <button
                  key={driver.driver_number}
                  onClick={() =>
                    setSelectedDriver(
                      driver.driver_number
                    )
                  }
                  className={`w-full text-left grid grid-cols-7 gap-4 items-center border-b py-3 ${
                    selectedDriver ===
                    driver.driver_number
                      ? "border-white"
                      : "border-zinc-800"
                  }`}
                >

                  <div className="font-bold text-xl">
                    P{driver.position}
                  </div>

                  <div className="col-span-2">

                    <div className="font-semibold">
                      {driver.name}
                    </div>

                    <div className="text-sm text-zinc-500">
                      {driver.team}
                    </div>

                  </div>

                  <div>

                    <div className="text-xs text-zinc-500">
                      GAP
                    </div>

                    <div>
                      {driver.gap ?? "-"}
                    </div>

                  </div>

                  <div>

                    <div className="text-xs text-zinc-500">
                      TYRE
                    </div>

                    <div>
                      {driver.compound}
                    </div>

                  </div>

                  <div>

                    <div className="text-xs text-zinc-500">
                      AGE
                    </div>

                    <div>
                      {driver.tyre_age ?? "-"}
                    </div>

                  </div>

                  <div>

                    <div className="text-xs text-zinc-500">
                      PITS
                    </div>

                    <div>
                      {driver.pit_stops}
                    </div>

                  </div>

                </button>

              ))}

            </div>

          </div>

          <div className="space-y-8">

            {teamEngineer && (
              <div>

                <h2 className="text-2xl font-semibold mb-4">
                  TEAM ENGINEER
                </h2>

                <div className="border border-zinc-700 rounded p-5">

                  <div className="text-xs text-zinc-500 mb-2">
                    {teamEngineer.driver} · P
                    {teamEngineer.position}
                  </div>

                  <div className="text-3xl font-semibold mb-6">
                    {teamEngineer.decision.replaceAll(
                      "_",
                      " "
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-6">

                    <div>

                      <div className="text-xs text-zinc-500">
                        PIT MODEL
                      </div>

                      <div className="text-lg">
                        {teamEngineer.pit_recommendation.replaceAll(
                          "_",
                          " "
                        )}
                      </div>

                    </div>

                    <div>

                      <div className="text-xs text-zinc-500">
                        TYRES
                      </div>

                      <div className="text-lg">
                        {teamEngineer.degradation_level.replaceAll(
                          "_",
                          " "
                        )}
                      </div>

                    </div>

                    <div>

                      <div className="text-xs text-zinc-500">
                        RIVAL
                      </div>

                      <div className="text-lg">
                        {teamEngineer.rival_decision
                          ? teamEngineer.rival_decision.replaceAll(
                              "_",
                              " "
                            )
                          : "-"}
                      </div>

                    </div>

                    <div>

                      <div className="text-xs text-zinc-500">
                        BATTLE
                      </div>

                      <div className="text-lg">
                        {teamEngineer.battle_priority ??
                          "-"}
                      </div>

                    </div>

                  </div>

                  <div className="border-t border-zinc-800 pt-4">

                    <div className="text-xs text-zinc-500 mb-2">
                      THEO RECOMMENDATION
                    </div>

                    <p className="text-white leading-relaxed">
                      {teamEngineer.message}
                    </p>

                  </div>

                </div>

              </div>
            )}

            <div>

              <h2 className="text-2xl font-semibold mb-4">
                STRATEGY
              </h2>

              {strategy ? (

                <div className="border border-zinc-800 rounded p-5">

                  <div className="text-xs text-zinc-500 mb-2">
                    {strategy.driver}
                  </div>

                  <div className="text-2xl font-semibold mb-5">
                    {strategy.recommendation}
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-5">

                    <div>

                      <div className="text-xs text-zinc-500">
                        BEST LAP
                      </div>

                      <div className="text-lg">
                        {strategy.best_lap ?? "-"}
                      </div>

                    </div>

                    <div>

                      <div className="text-xs text-zinc-500">
                        REJOIN
                      </div>

                      <div className="text-lg">
                                                {strategy.projected_rejoin_position
                          ? `P${strategy.projected_rejoin_position}`
                          : "-"}
                      </div>

                    </div>

                    <div>

                      <div className="text-xs text-zinc-500">
                        PIT WINDOW
                      </div>

                      <div className="text-lg">
                        {strategy.optimal_window.length >
                        0
                          ? `${
                              strategy
                                .optimal_window[0]
                            }–${
                              strategy.optimal_window[
                                strategy
                                  .optimal_window
                                  .length - 1
                              ]
                            }`
                          : "-"}
                      </div>

                    </div>

                    <div>

                      <div className="text-xs text-zinc-500">
                        TRAFFIC
                      </div>

                      <div className="text-lg">
                        {strategy.traffic_level ?? "-"}
                      </div>

                    </div>

                  </div>

                  <div className="border-t border-zinc-800 pt-4">

                    <p className="text-white leading-relaxed">
                      {strategy.message}
                    </p>

                  </div>

                </div>

              ) : (

                <div className="text-zinc-500">
                  Select a driver
                </div>

              )}

            </div>

            {rivalStrategy && (

              <div>

                <h2 className="text-2xl font-semibold mb-4">
                  RIVAL STRATEGY
                </h2>

                <div className="border border-zinc-800 rounded p-5">

                  <div className="text-xs text-zinc-500 mb-2">
                    {rivalStrategy.driver}
                    {" → "}
                    {rivalStrategy.target}
                  </div>

                  <div className="mb-6">

                    <div className="text-xs text-zinc-500 mb-1">
                      DECISION
                    </div>

                    <div className="text-2xl font-semibold">
                      {rivalStrategy.decision.replaceAll(
                        "_",
                        " "
                      )}
                    </div>

                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-6">

                    <div className="border border-zinc-800 rounded p-4">

                      <div className="text-xs text-zinc-500 mb-1">
                        UNDERCUT
                      </div>

                      <div className="text-lg font-semibold">
                        {
                          rivalStrategy.undercut_status
                        }
                      </div>

                      <div className="text-sm text-zinc-400 mt-2">
                        Quality{" "}
                        {
                          rivalStrategy.undercut_quality
                        }
                      </div>

                    </div>

                    <div className="border border-zinc-800 rounded p-4">

                      <div className="text-xs text-zinc-500 mb-1">
                        OVERCUT
                      </div>

                      <div className="text-lg font-semibold">
                        {
                          rivalStrategy.overcut_status
                        }
                      </div>

                      <div className="text-sm text-zinc-400 mt-2">
                        Quality{" "}
                        {
                          rivalStrategy.overcut_quality
                        }
                      </div>

                    </div>

                  </div>

                  <div className="border-t border-zinc-800 pt-4">

                    <div className="text-xs text-zinc-500 mb-2">
                      THEO
                    </div>

                    <p className="text-white leading-relaxed">
                      {rivalStrategy.message}
                    </p>

                  </div>

                </div>

              </div>

            )}

            <div>

              <h2 className="text-2xl font-semibold mb-4">
                RACE EVENTS
              </h2>

              <div className="space-y-4">

                {events.pit_events.length === 0 &&
                  events.top10_events.length ===
                    0 &&
                  events.other_position_changes ===
                    0 && (

                    <div className="text-zinc-500">
                      No major events
                    </div>

                  )}

                {events.pit_events.map(
                  (event, index) => (

                    <div
                      key={`pit-${index}`}
                      className="border border-zinc-800 rounded p-4"
                    >

                      <div className="text-xs text-zinc-500 mb-1">
                        PIT STOP
                      </div>

                      <div className="font-semibold text-lg">
                        {event.driver}
                      </div>

                      {event.position_from !==
                        undefined &&
                        event.position_to !==
                          undefined && (

                          <div className="text-sm text-zinc-400 mt-2">
                            P
                            {
                              event.position_from
                            }{" "}
                            → P
                            {event.position_to}
                          </div>

                        )}

                      {event.tyre_from &&
                        event.tyre_to && (

                          <div className="text-sm text-zinc-400 mt-1">
                            {event.tyre_from}
                            {" → "}
                            {event.tyre_to}
                          </div>

                        )}

                    </div>

                  )
                )}

                {events.top10_events.map(
                  (event, index) => (

                    <div
                      key={`top10-${index}`}
                      className="border border-zinc-800 rounded p-4"
                    >

                      <div className="text-xs text-zinc-500 mb-1">
                        {event.type ===
                        "ENTERED_TOP10"
                          ? "ENTERED TOP 10"
                          : "LEFT TOP 10"}
                      </div>

                      <div className="font-semibold text-lg">
                        {event.driver}
                      </div>

                      <div className="text-sm text-zinc-400 mt-2">
                        P{event.position}
                      </div>

                    </div>

                  )
                )}

                {events.other_position_changes >
                  0 && (

                  <div className="border border-zinc-800 rounded p-4">

                    <div className="text-xs text-zinc-500 mb-1">
                      OTHER POSITION CHANGES
                    </div>

                    <div className="text-lg font-semibold">
                      {
                        events.other_position_changes
                      }{" "}
                      drivers
                    </div>

                  </div>

                )}

              </div>

            </div>

            <div>

              <h2 className="text-2xl font-semibold mb-4">
                THEO ANALYSIS
              </h2>

              <div className="border border-zinc-800 rounded p-5 space-y-5">

                {theo.messages.map(
                  (item, index) => (

                    <div
                      key={index}
                      className="border-b border-zinc-800 pb-5 last:border-b-0 last:pb-0"
                    >

                      <div className="text-xs text-zinc-500 mb-2">
                        {item.type}
                        {" · "}
                        {item.priority}
                      </div>

                      <div className="text-white leading-relaxed">
                        {item.message}
                      </div>

                    </div>

                  )
                )}

              </div>

            </div>

          </div>

        </div>

      </div>
    </main>
  );
}