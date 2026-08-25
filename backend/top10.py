from driver_data import driver_data

top10 = sorted(
    driver_data.values(),
    key=lambda x: x["position"]
)[:10]

for data in top10:
    print(
        "P" + str(data["position"]),
        "-",
        data["name"],
        "- gap:",
        data["gap"],
        "- tyre:",
        data["compound"],
        "- age:",
        data["tyre_age"],
        "- pits:",
        data["pit_stops"]
    )