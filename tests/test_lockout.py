from app.security.lockout import AttemptTracker


def test_prune_and_clear():
    tracker = AttemptTracker(max_failures=2, window_seconds=10)
    tracker.register_failure("ana", now=100.0)
    tracker.register_failure("ana", now=101.0)
    assert tracker.is_locked("ana", now=102.0)
    assert not tracker.is_locked("ana", now=200.0)
    tracker.register_failure("ana", now=200.0)
    tracker.clear("ana")
    assert not tracker.is_locked("ana", now=201.0)
