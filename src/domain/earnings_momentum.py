from typing import List, Optional

def classify_earnings_momentum(
    net_income_last_4_quarters: Optional[List[float]]
) -> str:
    """
    Classifies recent earnings behavior based on quarter-over-quarter
    net income changes.

    The function analyzes the last four reported quarters and returns:
    - "Improving" if earnings increased in at least two transitions
    - "Declining" if earnings decreased in at least two transitions
    - "Stable" otherwise

    This is a descriptive indicator derived from historical data only.
    """
    if not net_income_last_4_quarters or len(net_income_last_4_quarters) < 4:
        return "Insufficient Data"

    deltas = []
    for i in range(len(net_income_last_4_quarters) - 1):
        prev = net_income_last_4_quarters[i + 1]
        curr = net_income_last_4_quarters[i]
        if prev == 0:
            deltas.append(0)
        else:
            deltas.append((curr - prev) / abs(prev))

    positives = sum(1 for d in deltas if d > 0)
    negatives = sum(1 for d in deltas if d < 0)

    if positives >= 2:
        return "Improving"
    if negatives >= 2:
        return "Declining"
    return "Stable"
