from event_intelligence import build_event_summary
from battle_commentary import build_battle_commentary


def build_theo_commentary(lap_number):
    events = build_event_summary(lap_number)
    battle_commentary = build_battle_commentary(lap_number)

    messages = []

    for event in events["pit_events"]:
        text = f'{event["driver"]} makes a pit stop.'

        if (
            event.get("position_from") is not None
            and event.get("position_to") is not None
        ):
            verb = (
                "Drops"
                if event["position_to"] > event["position_from"]
                else "Moves"
            )

            text += (
                f' {verb} from P{event["position_from"]} '
                f'to P{event["position_to"]}.'
            )

        if event.get("tyre_from") and event.get("tyre_to"):
            text += (
                f' Switches from {event["tyre_from"]} '
                f'to {event["tyre_to"]}.'
            )

        messages.append({
            "type": "RACE_EVENT",
            "priority": "INFO",
            "message": text
        })

    for event in events["top10_events"]:
        if event["type"] == "ENTERED_TOP10":
            text = (
                f'{event["driver"]} moves into the Top 10 '
                f'at P{event["position"]}.'
            )

        else:
            text = f'{event["driver"]} drops out of the Top 10.'

        messages.append({
            "type": "RACE_EVENT",
            "priority": "INFO",
            "message": text
        })

    for battle in battle_commentary["messages"]:
        if battle["priority"] == "INFO":
            continue

        messages.append({
            "type": "BATTLE",
            "priority": battle["priority"],
            "message": battle["message"]
        })

    if not messages:
        messages.append({
            "type": "INFO",
            "priority": "INFO",
            "message": "No significant race developments detected."
        })

    return {
        "lap": lap_number,
        "messages": messages
    }


if __name__ == "__main__":
    for item in build_theo_commentary(25)["messages"]:
        print(item["type"], "-", item["priority"], "-", item["message"])
