"""
Shared HTTP fetch utility with retry and backoff.
Used by all scrapers in place of raw session.get().
"""
import time


def fetch_with_retry(session, url: str, timeout: int = 20, retries: int = 3, backoff: int = 5):
    """
    Fetches a URL with up to `retries` attempts and linear backoff.
    Distinguishes network errors from HTTP errors for cleaner logging.
    Returns a Response object or None on total failure.
    """
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
