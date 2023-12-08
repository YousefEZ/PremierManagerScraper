import csv
from typing import Any, Dict, Set, List, Union
from time import sleep

import bs4
import urllib
import urllib.request

BASE_URL = "https://www.transfermarkt.co.uk/premier-league/trainer/pokalwettbewerb/GB1/plus/0?saison_id="
HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_bs4(url: str) -> bs4.BeautifulSoup:
    page_req = urllib.request.Request(url, headers=HEADERS)
    page = urllib.request.urlopen(page_req)
    return bs4.BeautifulSoup(page, "html.parser")


class Manager:

    def __init__(self, name: str, club: str):
        self._name = name
        self._club = club

    @property
    def name(self) -> str:
        return self._name

    @property
    def club(self) -> str:
        return self._club


FIELDS = ["season", "manager", "club"] 

class ManagerTable:

    def __init__(self, season: int):
        self._season = season

    def get_managers(self):
        soup = get_bs4(BASE_URL + str(self._season - 1))
        raw_managers = list(soup.find_all("tbody")[1].find_all("tr"))
        managers = []
        for raw_manager in raw_managers:
            name = list(raw_manager)[1].find("img").get("title")
            club = list(raw_manager)[4].find("img").get("alt")
            managers.append(Manager(name, club)) 
        return managers


if __name__ == "__main__":
    with open("managers.csv", "w") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for season in range(2000, 2025):
            print(f"Getting managers for season {season}...")
            table = ManagerTable(season)
            managers = table.get_managers()
            for manager in managers:
                writer.writerow({"season": season, "manager": manager.name, "club": manager.club})



