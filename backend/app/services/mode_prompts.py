"""Short, auditable prompt variants for guided session modes."""

MODE_ADDENDA = {
    "unsaid": "Help the user express one thing left unsaid. Do not ask them to contact anyone.",
    "replay": "Reflect one exchange from the imported material without inventing missing context.",
    "question": "Help the user explore one question without claiming the simulated person knows the answer.",
    "goodbye": "Support a closing exercise. Keep replies brief and never invite continued conversation.",
    "free": "Support free reflective writing while staying grounded in the imported style profile.",
}


def mode_addendum(mode: str) -> str:
    try:
        return MODE_ADDENDA[mode]
    except KeyError as exc:
        raise ValueError(f"Unsupported session mode: {mode}") from exc