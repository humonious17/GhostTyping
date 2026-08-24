"""Auditable thresholds for inverted product-health metrics."""

RISK_THRESHOLDS = {
    "same_thread_fixation_rate": {
        "threshold": 0.10,
        "window_days": 14,
        "response": "Audit high-return cohort journeys and consider stronger timeboxes or check-ins.",
    },
    "crisis_redirect_rate_low": {
        "threshold": 0.5,
        "response": "Audit classifier recall evaluation set.",
    },
    "crisis_redirect_rate_high": {
        "threshold": 15.0,
        "response": "Tune classifier specificity.",
    },
    "grief_redirect_rate": {
        "threshold": 0.02,
        "response": "Review grief detector precision and recall.",
    },
}