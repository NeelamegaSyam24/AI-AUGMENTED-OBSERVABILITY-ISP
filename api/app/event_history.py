from typing import Any


def build_events(predictions: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    events = []
    for prediction in reversed(predictions[-limit:]):
        telemetry = prediction["telemetry"]
        events.append(
            {
                "timestamp": prediction["timestamp"],
                "event_type": prediction["scenario"].upper().replace("-", "_") + "_STATUS",
                "severity": prediction["analysis"]["severity"],
                "scenario": prediction["scenario"],
                "description": prediction["analysis"]["explanation"],
                "component": "core-router",
                "metrics": {
                    key: telemetry.get(key)
                    for key in (
                        "latency_ms",
                        "packet_loss_percent",
                        "jitter_ms",
                        "throughput_mbps",
                        "bandwidth_utilization_percent",
                    )
                },
            }
        )
    return events
