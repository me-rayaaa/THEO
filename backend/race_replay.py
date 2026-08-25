import threading
import time

from race_state import get_race_state

START_LAP = 2
END_LAP = 71
SECONDS_PER_LAP = 1

current_lap = START_LAP
running = False
finished = False


def print_race_state(lap_number):
    race_state = get_race_state(lap_number)

    print("\n" + "=" * 50)
    print("LAP", race_state["current_lap"])
    print("STATUS:", race_state["race_status"])

    print("\nTOP 10")

    for driver in race_state["drivers"]:
        print(
            "P" + str(driver["position"]),
            "-",
            driver["name"],
            "- gap:",
            driver["gap"],
            "- tyre:",
            driver["compound"],
            "- age:",
            driver["tyre_age"],
            "- pits:",
            driver["pit_stops"],
            "- last clean lap:",
            driver["last_clean_lap"]
        )


def replay():
    global current_lap, running, finished

    while not finished:
        if running:
            print_race_state(current_lap)

            current_lap += 1

            if current_lap > END_LAP:
                running = False
                finished = True
                print("\nRace finished.")
                break

            time.sleep(SECONDS_PER_LAP)

        else:
            time.sleep(0.1)


thread = threading.Thread(target=replay)
thread.start()

print("Commands: start, pause, restart, quit")

while True:
    command = input("> ").strip().lower()

    if command == "start":
        running = True

    elif command == "pause":
        running = False
        print("Replay paused.")

    elif command == "restart":
        running = False
        current_lap = START_LAP
        finished = False
        print("Replay restarted from lap", START_LAP)

    elif command == "quit":
        running = False
        finished = True
        break

    else:
        print("Unknown command.")

thread.join()