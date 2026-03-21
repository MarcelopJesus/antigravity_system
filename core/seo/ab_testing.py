"""A/B Testing for Titles and Meta Descriptions — Optimizes CTR via GSC data."""
import json
import os
import time
from core.logger import get_logger

logger = get_logger(__name__)

AB_TESTS_FILE = "data/ab_tests.json"


def _load_tests():
    """Load active A/B tests from file."""
    if not os.path.exists(AB_TESTS_FILE):
        return []
    try:
        with open(AB_TESTS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_tests(tests):
    """Save A/B tests to file."""
    os.makedirs(os.path.dirname(AB_TESTS_FILE), exist_ok=True)
    with open(AB_TESTS_FILE, 'w') as f:
        json.dump(tests, f, ensure_ascii=False, indent=2)


def create_ab_test(post_id, keyword, variations):
    """Create a new A/B test for a post.

    Args:
        post_id: WordPress post ID.
        keyword: Target keyword.
        variations: dict with keys 'titles' (list of 3) and 'meta_descriptions' (list of 3).

    Returns:
        Test dict.
    """
    test = {
        "post_id": post_id,
        "keyword": keyword,
        "created_at": time.strftime('%Y-%m-%d'),
        "current_variation": 0,  # Index into variations
        "status": "active",
        "titles": variations.get("titles", []),
        "meta_descriptions": variations.get("meta_descriptions", []),
        "results": [],  # CTR measurements per variation
    }

    tests = _load_tests()
    # Remove existing test for same post
    tests = [t for t in tests if t["post_id"] != post_id]
    tests.append(test)
    _save_tests(tests)

    logger.info("A/B test created for post %d (keyword: %s, %d title variations)",
                post_id, keyword, len(test["titles"]))
    return test


def evaluate_and_rotate(wp_client, gsc_data, min_days=14, ctr_threshold=2.0):
    """Evaluate active A/B tests and rotate to next variation if CTR is low.

    Args:
        wp_client: WordPressClient instance.
        gsc_data: List of page performance dicts from GSC.
        min_days: Minimum days before evaluating.
        ctr_threshold: Minimum CTR % to keep current variation.

    Returns:
        List of actions taken.
    """
    tests = _load_tests()
    if not tests:
        return []

    gsc_by_url = {}
    for item in gsc_data:
        gsc_by_url[item.get("page", "")] = item

    actions = []

    for test in tests:
        if test["status"] != "active":
            continue

        post_id = test["post_id"]
        current_var = test["current_variation"]
        created = test["created_at"]

        # Check if enough time has passed
        days_elapsed = (time.time() - time.mktime(time.strptime(created, '%Y-%m-%d'))) / 86400
        if days_elapsed < min_days:
            continue

        # Find CTR for this post
        # Would need post URL mapping — simplified
        current_ctr = 0
        for url, data in gsc_by_url.items():
            if str(post_id) in url or test["keyword"].replace(" ", "-") in url:
                current_ctr = data.get("ctr", 0)
                break

        # Record result
        test["results"].append({
            "variation": current_var,
            "ctr": current_ctr,
            "measured_at": time.strftime('%Y-%m-%d'),
        })

        # Rotate if CTR below threshold and more variations available
        if current_ctr < ctr_threshold:
            next_var = current_var + 1
            if next_var < len(test["titles"]):
                test["current_variation"] = next_var
                test["created_at"] = time.strftime('%Y-%m-%d')  # Reset timer

                # Update WordPress
                new_title = test["titles"][next_var]
                new_meta = test["meta_descriptions"][next_var] if next_var < len(test["meta_descriptions"]) else ""

                payload = {"title": new_title}
                if new_meta:
                    payload["meta"] = {"_yoast_wpseo_metadesc": new_meta}

                try:
                    wp_client.update_post(post_id, payload)
                    actions.append({
                        "post_id": post_id,
                        "action": "rotated",
                        "from_variation": current_var,
                        "to_variation": next_var,
                        "old_ctr": current_ctr,
                        "new_title": new_title,
                    })
                    logger.info("A/B rotated post %d: var %d→%d (CTR was %.1f%%)",
                                post_id, current_var, next_var, current_ctr)
                except Exception as e:
                    logger.warning("Failed to rotate post %d: %s", post_id, e)
            else:
                # All variations tested — pick best
                best = max(test["results"], key=lambda r: r["ctr"])
                test["status"] = "completed"
                test["winner"] = best["variation"]
                logger.info("A/B test completed for post %d: winner=var %d (CTR %.1f%%)",
                            post_id, best["variation"], best["ctr"])

    _save_tests(tests)
    return actions


def get_active_tests():
    """Return list of active A/B tests."""
    tests = _load_tests()
    return [t for t in tests if t["status"] == "active"]
