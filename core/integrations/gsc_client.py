"""Google Search Console client — Fetches performance data for articles."""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from core.logger import get_logger

load_dotenv(override=True)

logger = get_logger(__name__)

GSC_SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']


def _get_gsc_service(service_account_path='config/service_account.json'):
    """Build GSC API service using service account credentials.

    Returns:
        Google Search Console API service, or None on failure.
    """
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_file(
            service_account_path, scopes=GSC_SCOPES
        )
        service = build('searchconsole', 'v1', credentials=credentials)
        return service
    except ImportError:
        logger.warning("google-api-python-client not installed. GSC integration unavailable.")
        return None
    except Exception as e:
        logger.warning("Failed to initialize GSC service: %s", e)
        return None


def get_article_performance(property_url, days=28, service_account_path='config/service_account.json'):
    """Fetch performance data for all pages from Google Search Console.

    Args:
        property_url: GSC property URL (e.g., 'https://mjesus.com.br').
        days: Number of days to look back.
        service_account_path: Path to service account JSON.

    Returns:
        List of dicts with keys: page, clicks, impressions, ctr, position.
        Empty list on failure.
    """
    if not property_url:
        property_url = os.getenv("GSC_PROPERTY_URL", "")
    if not property_url:
        logger.warning("GSC_PROPERTY_URL not configured. Skipping GSC data.")
        return []

    service = _get_gsc_service(service_account_path)
    if not service:
        return []

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    try:
        response = service.searchanalytics().query(
            siteUrl=property_url,
            body={
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': ['page'],
                'rowLimit': 500,
            }
        ).execute()

        results = []
        for row in response.get('rows', []):
            results.append({
                'page': row['keys'][0],
                'clicks': row.get('clicks', 0),
                'impressions': row.get('impressions', 0),
                'ctr': round(row.get('ctr', 0) * 100, 2),
                'position': round(row.get('position', 0), 1),
            })

        logger.info("GSC data fetched: %d pages, %s to %s", len(results), start_date, end_date)
        return results

    except Exception as e:
        logger.warning("GSC query failed: %s", e)
        return []


def get_keyword_performance(property_url, days=28, service_account_path='config/service_account.json'):
    """Fetch performance data by query (keyword) from GSC.

    Returns:
        List of dicts with keys: query, clicks, impressions, ctr, position.
    """
    if not property_url:
        property_url = os.getenv("GSC_PROPERTY_URL", "")
    if not property_url:
        return []

    service = _get_gsc_service(service_account_path)
    if not service:
        return []

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    try:
        response = service.searchanalytics().query(
            siteUrl=property_url,
            body={
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': ['query'],
                'rowLimit': 1000,
            }
        ).execute()

        results = []
        for row in response.get('rows', []):
            results.append({
                'query': row['keys'][0],
                'clicks': row.get('clicks', 0),
                'impressions': row.get('impressions', 0),
                'ctr': round(row.get('ctr', 0) * 100, 2),
                'position': round(row.get('position', 0), 1),
            })

        return results

    except Exception as e:
        logger.warning("GSC keyword query failed: %s", e)
        return []


def find_page2_opportunities(property_url, days=28, service_account_path='config/service_account.json'):
    """Find articles ranking on page 2 (positions 11-20) — optimization opportunities.

    Returns:
        List of dicts with page performance data, sorted by impressions desc.
    """
    all_pages = get_article_performance(property_url, days, service_account_path)
    page2 = [p for p in all_pages if 11 <= p['position'] <= 20]
    page2.sort(key=lambda x: x['impressions'], reverse=True)

    if page2:
        logger.info("Found %d page-2 opportunities (positions 11-20)", len(page2))
    return page2


def compare_periods(property_url, days=28, service_account_path='config/service_account.json'):
    """Compare current period vs previous period to detect position changes.

    Returns:
        List of dicts with: page, current_position, previous_position, change.
    """
    current = get_article_performance(property_url, days, service_account_path)
    previous = get_article_performance(property_url, days * 2, service_account_path)

    if not current or not previous:
        return []

    prev_map = {p['page']: p['position'] for p in previous}
    changes = []

    for item in current:
        page = item['page']
        curr_pos = item['position']
        prev_pos = prev_map.get(page)

        if prev_pos is not None:
            change = prev_pos - curr_pos  # positive = improved
            changes.append({
                'page': page,
                'current_position': curr_pos,
                'previous_position': prev_pos,
                'change': round(change, 1),
                'status': 'improved' if change > 1 else ('declined' if change < -1 else 'stable'),
                'clicks': item['clicks'],
                'impressions': item['impressions'],
            })

    # Sort by biggest declines first (need attention)
    changes.sort(key=lambda x: x['change'])
    return changes
