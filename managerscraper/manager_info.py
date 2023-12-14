from typing import Any, Dict, Set, List, Union
from time import sleep

import bs4
import urllib
import urllib.request
import urllib.error

BASE_URL = "https://www.transfermarkt.co.uk/premier-league/trainer/pokalwettbewerb/GB1/plus/0?saison_id="
HEADERS = {"User-Agent": "Mozilla/5.0"}

MANAGER_URL = "https://www.transfermarkt.co.uk/A/profil/trainer/"
STATS_MANAGER_URL = "https://www.transfermarkt.co.uk/A/bilanztrainer/trainer/"


def get_manager_number(url: str) -> str:
    # using regex grab the last number in the url, which follows the structure:
    # /jurgen-klopp/profil/trainer/118
    # we want to grab the 118
    return url.split("/")[-1]


def retry_from_header(func):
    DEFAULT_RETRY = 15  # seconds

    def decorator(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except urllib.error.HTTPError as e:
                if (
                    e.code != 429
                ):  # Check if the error is due to rate limiting (HTTP 429 Too Many Requests)
                    raise e
                retry_after = e.headers.get("Retry-After")
                sleep(float(retry_after) if retry_after else DEFAULT_RETRY)

    return decorator


@retry_from_header
def get_bs4(url: str) -> bs4.BeautifulSoup:
    page_req = urllib.request.Request(url, headers=HEADERS)
    page = urllib.request.urlopen(page_req)
    return bs4.BeautifulSoup(page, "html.parser")


class Manager:
    def __init__(self, name: str, manager_number: str, club: str):
        self._name = name
        self._club = club
        self._manager_number = manager_number

    @property
    def name(self) -> str:
        return self._name

    @property
    def club(self) -> str:
        return self._club

    @property
    def manager_number(self) -> str:
        return self._manager_number

    @property
    def url(self) -> str:
        return MANAGER_URL + self._manager_number

    def create_stats_url(self, page_number: int) -> str:
        return f"https://www.transfermarkt.co.uk/jurgen-klopp/bilanztrainer/trainer/{self._manager_number}/ajax/yw1/page/{page_number}?ajax=yw1"

    def scrape_records_with_other_managers(self) -> Dict[str, Dict[str, Any]]:
        managers = {}
        last_body = None
        for page_number in range(1, 100):
            soup = get_bs4(self.create_stats_url(page_number))
            body = soup.find("tbody")
            if body is None:
                # if there is no body, then the manager is new and has no records
                print(f"No body found in {self.create_stats_url(page_number)}")
                break
            if body == last_body:
                # if the body is the same as the last body, then we have reached the end of the table
                # they repeat the last page when you reach the end
                print(f"Completed Manager ({self._manager_number}): {self._name}")
                break

            assert type(body) == bs4.element.Tag
            rows = body.find_all("tr")
            for raw_row in rows:
                row = list(raw_row)
                identifier = get_manager_number(row[0].find("a").get("href"))
                if identifier in managers:
                    print(
                        f"Duplicated Manager for ({self._manager_number}): {self._name}, {identifier}: {row[0].find('a').get('title')} [{page_number}]"
                    )
                    # print(f"Completed Manager ({self._manager_number}): {self._name}")
                    continue
                managers[identifier] = {
                    "id": self._manager_number,
                    "name": self._name,
                    "targetId": identifier,
                    "targetName": row[0].find("a").get("title"),
                    "matches": row[1].string,
                    "wins": row[2].string,
                    "draws": row[3].string,
                    "losses": row[4].string,
                }
            last_body = body
        return managers

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Manager):
            return self._manager_number == other._manager_number
        return False

    def __hash__(self) -> int:
        return hash(self._manager_number)


FIELDS = ["season", "manager", "identifier", "club"]


def get_managers(season: int) -> Set[Manager]:
    soup = get_bs4(BASE_URL + str(season - 1))
    raw_managers = list(soup.find_all("tbody")[1].find_all("tr"))
    managers = set()
    for raw_manager in raw_managers:
        name = list(raw_manager)[1].find("img").get("title")
        club = list(raw_manager)[4].find("img").get("alt")
        manager_number = get_manager_number(list(raw_manager)[2].find("a").get("href"))
        managers.add(Manager(name, manager_number, club))
    return managers


MANAGER_STATS_FIELDS = [
    "id",
    "name",
    "targetId",
    "targetName",
    "matches",
    "wins",
    "draws",
    "losses",
]
