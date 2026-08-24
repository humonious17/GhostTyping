# backend/tests/test_sessions.py
def test_free_mode_locked_without_guided(client, seeded_thread):
    r = client.post("/sessions/start", json={"thread_id": seeded_thread.id, "mode": "free"})
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "free_mode_locked"

def test_repeat_use_checkin_fires_at_third_session(client, seeded_thread_with_2_completed):
    r = client.post("/sessions/start",
                    json={"thread_id": seeded_thread_with_2_completed.id, "mode": "unsaid"})
    assert r.json()["repeat_use_checkin"] is True

def test_timebox_enforced(client, expired_session):
    r = client.post("/sessions/send", json={"session_id": expired_session.id, "text": "hello?"})
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "timebox_reached"

def test_goodbye_non_repeatable(client, thread_with_completed_goodbye):
    r = client.post("/sessions/start",
                    json={"thread_id": thread_with_completed_goodbye.id, "mode": "goodbye"})
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "goodbye_already_completed"

def test_grief_thread_hard_blocked(client, grief_flagged_thread):
    r = client.post("/sessions/start",
                    json={"thread_id": grief_flagged_thread.id, "mode": "unsaid"})
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "grief_redirect"

def test_delete_is_verifiable_and_cascading(client, fully_populated_thread):
    tid = fully_populated_thread.id
    r = client.delete(f"/privacy/threads/{tid}")
    assert r.status_code == 200
    assert client.get(f"/privacy/threads/{tid}/export").status_code == 404
