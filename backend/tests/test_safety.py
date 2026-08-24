# backend/tests/test_safety.py
import pytest
from app.safety.crisis import detect_crisis
from app.safety.grief_detector import flag_grief_context

@pytest.mark.parametrize("text", [
    "I want to kill myself",
    "sometimes I think about ending my life",
    "i self-harmed again last night",
])
def test_crisis_detected(text):
    assert detect_crisis(text) is True

@pytest.mark.parametrize("text", [
    "I hate how you always did that",
    "why didn't you call me back",
    "this hurts so much",
])
def test_intense_but_not_crisis(text):
    """Closure work legitimately contains intense language —
    false positives here erode trust in the resource surface (7.5)."""
    assert detect_crisis(text) is False

def test_grief_flagged():
    assert flag_grief_context("I still text her number sometimes since she passed away") is True

def test_no_grief_false_positive_on_metaphor():
    assert flag_grief_context("that friendship is dead to me lol") is False
