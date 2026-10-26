import threading
import time

from data_store import LAST_LAP
from race_state import get_race_state

START_LAP = 2
END_LAP = LAST_LAP
SECONDS_PER_LAP = 1

current_lap = START_LAP
running = False
finished = False


def print_race_state(lap_number):
    race_state = get_race_state(lap_number)

    print("\n" + "=" * 50)
    print("LAP", race_state["current_lap"])
    print("STATUS:", race_state["race_status"])

    for driver in race_state["drivers"][:10]:
        print(
            "P" + str(driver["position"]),
            "-", driver["name"],
            "- gap:", driver["gap"],
            "- tyre:", driver["compound"],
            "- age:", driver["tyre_age"],
            "- pits:", driver["pit_stops"],
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


def start_thread():
    thread = threading.Thread(target=replay, daemon=True)
    thread.start()
    return thread


def main():
    global current_lap, running, finished

    thread = start_thread()

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

            # После финиша поток уже завершился — запускаем новый.
            if not thread.is_alive():
                thread = start_thread()

            print("Replay restarted from lap", START_LAP)

        elif command == "quit":
            running = False
            finished = True
            break

        else:
            print("Unknown command.")

    thread.join()


if __name__ == "__main__":
    main()
