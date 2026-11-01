from api.app.event_history import build_events


def test_events_are_derived_from_recent_prediction_history():
    events = build_events(
        [
            {
                "timestamp": "2026-01-01T00:00:00",
                "scenario": "high-latency",
                "telemetry": {
                    "latency_ms": 180.0,
                    "packet_loss_percent": 1.0,
                },
                "analysis": {
                    "severity": "WARNING",
                    "explanation": "Elevated latency detected.",
                },
            }
        ],
        limit=1,
    )

    assert len(events) == 1
    assert events[0]["event_type"] == "HIGH_LATENCY_STATUS"
    assert events[0]["severity"] == "WARNING"
    assert events[0]["metrics"]["latency_ms"] == 180.0
    assert events[0]["metrics"]["packet_loss_percent"] == 1.0


def test_event_limit_returns_newest_records_first():
    predictions = [
        {
            "timestamp": f"2026-01-01T00:00:0{index}",
            "scenario": "normal",
            "telemetry": {},
            "analysis": {"severity": "HEALTHY", "explanation": "OK"},
        }
        for index in range(3)
    ]

    events = build_events(predictions, limit=2)

    assert [event["timestamp"] for event in events] == [
        "2026-01-01T00:00:02",
        "2026-01-01T00:00:01",
    ]
