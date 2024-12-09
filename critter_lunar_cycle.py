import requests
from collections import defaultdict
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Constants
BASE_URL = "https://api.inaturalist.org/v1/observations"
LUNAR_PHASES = [
    "New Moon",
    "Waxing Crescent",
    "First Quarter",
    "Waxing Gibbous",
    "Full Moon",
    "Waning Gibbous",
    "Last Quarter",
    "Waning Crescent",
]


def get_taxon_name(taxon_id):
    """Retrieve the taxon name given its ID."""
    response = requests.get(BASE_URL, params={"taxon_id": taxon_id, "per_page": 1})
    response.raise_for_status()
    return response.json()["results"][0]["taxon"]["name"]


def get_inaturalist_daily_observations(taxon_id, year, month):
    """Fetch daily observation counts for a given taxon_id and month."""
    start_date = f"{year}-{month:02d}-01"
    end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=32)).replace(
        day=1
    ) - timedelta(days=1)

    observations = defaultdict(int)
    params = {
        "taxon_id": taxon_id,
        "d1": start_date,
        "d2": end_date.strftime("%Y-%m-%d"),
        "per_page": 200,
        "order": "asc",
        "order_by": "observed_on",
        "page": 1,
    }

    while True:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            break

        for obs in results:
            observations[obs["observed_on"]] += 1

        if len(results) < params["per_page"]:
            break
        params["page"] += 1

    return observations


def calculate_lunar_phase(date):
    """Calculate the lunar phase for a given date."""
    known_new_moon = datetime(2000, 1, 6, 18, 14)  # Known new moon date
    lunar_cycle_days = 29.53058867  # Average lunar cycle length in days
    days_since_new_moon = (date - known_new_moon).total_seconds() / 86400
    normalized_phase = (days_since_new_moon % lunar_cycle_days) / lunar_cycle_days

    if normalized_phase < 0.03 or normalized_phase >= 0.97:
        return "New Moon"
    elif normalized_phase < 0.25:
        return "Waxing Crescent"
    elif normalized_phase < 0.27:
        return "First Quarter"
    elif normalized_phase < 0.50:
        return "Waxing Gibbous"
    elif normalized_phase < 0.53:
        return "Full Moon"
    elif normalized_phase < 0.75:
        return "Waning Gibbous"
    elif normalized_phase < 0.77:
        return "Last Quarter"
    return "Waning Crescent"


def get_lunar_cycle_for_month(year, month):
    """Get the lunar phase for each day of a given month."""
    start_date = datetime(year, month, 1)
    end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    lunar_cycle = {}
    current_date = start_date
    while current_date <= end_date:
        lunar_cycle[current_date.strftime("%Y-%m-%d")] = calculate_lunar_phase(
            current_date
        )
        current_date += timedelta(days=1)

    return lunar_cycle


def plot_observations_by_lunar_phase(observations, lunar_cycle, taxon_name, year):
    """Plot the number of observations for each lunar phase aggregated over the entire year."""
    phase_counts = defaultdict(int)

    for date, count in observations.items():
        lunar_phase = lunar_cycle.get(date)
        if lunar_phase:
            phase_counts[lunar_phase] += count

    counts = [phase_counts[phase] for phase in LUNAR_PHASES]

    plt.figure(figsize=(10, 6))
    plt.bar(LUNAR_PHASES, counts, color="skyblue", edgecolor="black")
    plt.title(f"Observations of {taxon_name} in {year}", fontsize=16)
    plt.xlabel("Lunar Phase", fontsize=12)
    plt.ylabel("Number of Observations", fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def main():
    """Main function to run the analysis."""
    taxon_id = int(input("Enter the taxon_id: "))
    year = int(input("Enter the year (YYYY): "))

    print("Fetching observations...")

    # Aggregate observations across all months of the year
    all_observations = defaultdict(int)
    all_lunar_cycle = {}

    for month in range(1, 13):
        print(f"Processing {month:02d}/{year}...")
        observations = get_inaturalist_daily_observations(taxon_id, year, month)
        taxon_name = get_taxon_name(taxon_id)

        print("Calculating lunar phases...")
        lunar_cycle = get_lunar_cycle_for_month(year, month)

        # Aggregate observations and lunar cycle data
        for date, count in observations.items():
            all_observations[date] += count
        all_lunar_cycle.update(lunar_cycle)

    print("Plotting data...")
    plot_observations_by_lunar_phase(
        all_observations, all_lunar_cycle, taxon_name, year
    )


if __name__ == "__main__":
    main()
