import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.validator import is_price_anomalous, title_matches_expected, find_outlier_sources, validate_result

# is_price_anomalous
def test_price_not_anomalous_with_few_history():
    assert is_price_anomalous(1000, [1100, 1200]) == False

def test_price_anomalous_big_drop():
    assert is_price_anomalous(500, [1000, 1000, 1000]) == True

def test_price_not_anomalous_small_drop():
    assert is_price_anomalous(900, [1000, 1000, 1000]) == False

# title_matches_expected
def test_title_matches_keyword():
    assert title_matches_expected("ASUS RTX 5060 Ti 16GB", ["asus", "rtx"]) == True

def test_title_no_match():
    assert title_matches_expected("Some Random GPU", ["asus", "gigabyte"]) == False

def test_title_empty_keywords():
    assert title_matches_expected("Anything", []) == True

# find_outlier_sources
def test_no_outliers_similar_prices():
    results = [("A", 1000, "Shop1", ""), ("B", 1050, "Shop2", ""), ("C", 980, "Shop3", "")]
    assert find_outlier_sources(results) == []

def test_outlier_detected():
    results = [("A", 1000, "Shop1", ""), ("B", 1000, "Shop2", ""), ("C", 300, "Shop3", "")]
    assert "Shop3" in find_outlier_sources(results)

# validate_result
def test_validate_clean_result():
    ok, reasons = validate_result("ASUS RTX 5060 Ti 16GB", 45000, "Shop1")
    assert ok == True
    assert reasons == []

def test_validate_keyword_mismatch():
    ok, reasons = validate_result("Random GPU", 45000, "Shop1", expected_keywords=["asus"])
    assert ok == False
    assert len(reasons) == 1
