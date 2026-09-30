"""
AlertLens — WebSocket Performance Benchmark
Measures JSON serialization cost, per-client broadcast latency,
and concurrency behavior on a single node.
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock
from app.websocket_manager import ConnectionManager
from app.schemas import IncidentOut, ScoreBreakdownOut

def benchmark_websocket():
    print("=" * 70)
    print("ALERTLENS WEBSOCKET PERFORMANCE AUDIT (SINGLE-NODE BENCHMARK)")
    print("=" * 70)

    # 1. Serialization Cost
    sample_incident = IncidentOut(
        incident_id="inc-perf-test-001",
        severity_score=19.82,
        severity_rank=1,
        mitre_tag="T1110",
        mitre_technique_name="Brute Force",
        alert_count=42,
        created_at="2026-09-29T22:00:00Z",
        acknowledged=False,
        confidence_tier="actionable",
        attack_progression="Escalation Chain Detected",
        progression_detail="Authentication -> Privilege Escalation",
        correlation_confidence=0.95,
        confidence_reason="Campaign Link: Same Source IP & Target Asset across 42 alerts",
        score_breakdown=ScoreBreakdownOut(
            asset_component=9.0,
            event_component=4.0,
            volume_component=3.76,
            top_asset_factor="auth-gateway-01 (high criticality)",
            top_event_factor="failed_login (severity 2)",
            asset_raw_level="HIGH",
            asset_raw_score=3,
            event_type_used="failed_login",
            event_raw_score=2,
            alert_count_used=42,
        )
    )

    t0 = time.perf_counter()
    n_serializations = 10000
    for _ in range(n_serializations):
        raw_dict = sample_incident.model_dump(mode="json")
        _ = json.dumps({"type": "NEW_INCIDENT", "incident": raw_dict})
    ser_time = (time.perf_counter() - t0) * 1000.0
    avg_ser_us = (ser_time / n_serializations) * 1000.0

    print(f"1. Serialization Cost:")
    print(f"   - {n_serializations:,} serializations in {ser_time:.2f} ms")
    print(f"   - Average time per payload: {avg_ser_us:.2f} µs ({1_000_000 / avg_ser_us:,.0f} payloads/sec)")
    print(f"   - Serialized frame size: {len(json.dumps(sample_incident.model_dump(mode='json')))} bytes")

    # 2. Per-client Broadcast Latency
    async def measure_broadcasts():
        print(f"\n2. Broadcast Fanout Overhead across Concurrent Clients:")
        print(f"   {'Client Count':<15} {'Total Broadcast (µs)':<25} {'Avg per Client (µs)':<20} {'Throughput (broadcasts/sec)':<25}")
        print("   " + "-" * 75)

        client_counts = [1, 5, 10, 25, 50, 100]
        payload = {"type": "NEW_INCIDENT", "incident": sample_incident.model_dump(mode="json")}

        for count in client_counts:
            mgr = ConnectionManager()
            for _ in range(count):
                mock_ws = AsyncMock()
                # Simulate sub-millisecond network event-loop write
                mock_ws.send_json = AsyncMock()
                mgr.active_connections.append(mock_ws)

            # Warmup
            await mgr.broadcast(payload)

            # Measure 1,000 broadcasts
            runs = 1000
            t_start = time.perf_counter()
            for _ in range(runs):
                await mgr.broadcast(payload)
            elapsed = time.perf_counter() - t_start

            total_us = (elapsed / runs) * 1_000_000.0
            per_client_us = total_us / count
            rate = runs / elapsed

            print(f"   {count:<15} {total_us:<25.2f} {per_client_us:<20.2f} {rate:<25,.0f}")

    asyncio.run(measure_broadcasts())
    print("=" * 70)

if __name__ == "__main__":
    benchmark_websocket()
