import csv

import rich.progress

from managerscraper.manager_info import *


def write_manager_metadata() -> None:
    # make a csv of all managers per season in one csv file following the field names in FIELDS
    with open("managers.csv", "w") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for season in rich.progress.track(
            range(2000, 2024), description="Scraping Meta Manager Info"
        ):
            managers = get_managers(season)
            for manager in managers:
                writer.writerow(
                    {
                        "season": season,
                        "manager": manager.name,
                        "identifier": manager.manager_number,
                        "club": manager.club,
                    }
                )


def write_manager_stats() -> None:
    managers = set().union(
        *[
            get_managers(season)
            for season in rich.progress.track(
                range(2000, 2022), description="Scraping Meta Manager Info"
            )
        ]
    )
    with open("manager_stats.csv", "w") as f:
        writer = csv.DictWriter(f, fieldnames=MANAGER_STATS_FIELDS)
        writer.writeheader()
        for manager in rich.progress.track(managers, description="Scraping managers"):
            stats = manager.scrape_records_with_other_managers()
            for stat in stats.values():
                writer.writerow(stat)


if __name__ == "__main__":
    # write_manager_metadata()
    write_manager_stats()
