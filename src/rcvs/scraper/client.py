from __future__ import annotations

import time

import requests
from loguru import logger

BASE_URL = "https://findavet.rcvs.org.uk"
REQUEST_DELAY = 1.5
USER_AGENT = "RCVS-VetGDP-Finder/0.1 (educational project; polite scraper)"


class RCVSClient:
    """
    HTTP client for the RCVS Find a Vet website.

    Wraps requests.Session with polite rate limiting and a single retry on failure.
    """

    def __init__(
        self,
        delay: float = REQUEST_DELAY
    ) -> None:
        """
        Initialise the client.

        :param delay: Seconds to wait between requests
        """
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT})
        self._delay = delay
        self._last_request_time: float = 0.0

    def get(
        self,
        path: str
    ) -> requests.Response:
        """
        Make a GET request to the RCVS website with rate limiting and retry.

        :param path: URL path relative to BASE_URL, or full URL

        :return: Response object
        """
        url = path if path.startswith("http") else f"{BASE_URL}{path}"

        elapsed = time.time() - self._last_request_time
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)

        for attempt in range(2):
            try:
                logger.debug("GET {}", url)
                response = self._session.get(url, timeout=30)
                self._last_request_time = time.time()
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                if attempt == 0:
                    logger.warning("Request failed ({}), retrying: {}", exc, url)
                    time.sleep(2)
                else:
                    logger.error("Request failed after retry: {}", url)
                    raise

        raise RuntimeError("Unreachable")
