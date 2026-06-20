"""
Shared HTTP fetch utility with retry, backoff, and Tor fallback.
Used by all scrapers in place of raw session.get().
"""
import time
import requests


def _fetch(session, url: str, timeout: int, retries: int, backoff: int):
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, timeout=timeout)
            if response.status_code == 429:
                wait = backoff * attempt
                print(f"[http] Rate limited (429) on attempt {attempt} — waiting {wait}s")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response
        except Exception as e:
            if attempt < retries:
                wait = backoff * attempt
                print(f"[http] Attempt {attempt} failed for {url}: {e} — retrying in {wait}s")
                time.sleep(wait)
            else:
                print(f"[http] All {retries} attempts failed for {url}: {e}")
    return None


def fetch_with_retry(session, url: str, timeout: int = 20, retries: int = 3, backoff: int = 5):
    """
    Fetches a URL with Tor session first.
    If all Tor attempts fail, falls back to direct connection (real IP).
    Returns a Response object or None on total failure.
    """
    result = _fetch(session, url, timeout, retries, backoff)
    if result is not None:
        return result

    print(f"[http] Tor failed for {url} — falling back to direct connection")
    try:
        direct_session = requests.Session()
        direct_session.headers.update(session.headers)
        result = _fetch(direct_session, url, timeout, retries=2, backoff=backoff)
        if result is not None:
            print(f"[http] Direct connection succeeded for {url}")
        return result
    except Exception as e:
        print(f"[http] Direct fallback also failed for {url}: {e}")
        return None
