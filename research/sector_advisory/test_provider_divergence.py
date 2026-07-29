from provider_divergence import find_divergences


def _cluster(cluster, proxy, quadrant, momentum_pct):
    return {"cluster": cluster, "proxy": proxy, "quadrant": quadrant, "momentum_pct": momentum_pct}


def _broad(etf, quadrant, momentum_pct):
    return {"etf": etf, "quadrant": quadrant, "momentum_pct": momentum_pct}


def test_no_divergence_when_same_sign_different_magnitude():
    sub_industry = [_cluster("Financials/Fintech", "XLF", "Improving", 3.79)]
    broad = {"available": True, "sectors": [_broad("XLF", "Leading", 2.88)]}
    assert find_divergences(sub_industry, broad) == []


def test_divergence_when_momentum_sign_disagrees():
    sub_industry = [_cluster("Financials/Fintech", "XLF", "Improving", 3.79)]
    broad = {"available": True, "sectors": [_broad("XLF", "Weakening", -1.5)]}
    out = find_divergences(sub_industry, broad)
    assert len(out) == 1
    assert out[0]["ticker"] == "XLF"
    assert out[0]["hub_momentum_pct"] == 3.79
    assert out[0]["sta_momentum_pct"] == -1.5


def test_no_divergence_when_sta_unavailable():
    sub_industry = [_cluster("Financials/Fintech", "XLF", "Improving", 3.79)]
    broad = {"available": False, "reason": "connection refused"}
    assert find_divergences(sub_industry, broad) == []


def test_non_shared_proxy_never_checked():
    # SMH isn't one of STA's 11 broad-sector ETFs -- nothing to compare against,
    # must never be flagged regardless of its own momentum sign.
    sub_industry = [_cluster("Semis", "SMH", "Weakening", -9.39)]
    broad = {"available": True, "sectors": [_broad("XLK", "Weakening", -3.16)]}
    assert find_divergences(sub_industry, broad) == []


def test_missing_momentum_on_either_side_not_flagged():
    sub_industry = [_cluster("Energy", "XLE", None, None)]
    broad = {"available": True, "sectors": [_broad("XLE", "Leading", 7.19)]}
    assert find_divergences(sub_industry, broad) == []
