from tycoon_city.sim.contracts import validate_request, validate_shipment


def test_validate_request_valid():
    req = {
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "citizen_id": "c1",
        "timestamp": "2026-08-07T12:00:00Z",
        "priority": "HIGH",
        "request_type": "DATA_SOURCE",
        "status": "PENDING",
        "complexity": 5,
    }
    ok, errors = validate_request(req)
    assert ok is True
    assert errors == []


def test_validate_request_missing_required():
    req = {
        "citizen_id": "c1"
        # Missing many required
    }
    ok, errors = validate_request(req)
    assert ok is False
    assert len(errors) > 0
    assert "Missing required field: request_id" in errors


def test_validate_request_bad_enum_and_bounds():
    req = {
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "citizen_id": "c1",
        "timestamp": "2026-08-07T12:00:00Z",
        "priority": "VERY_HIGH",  # Bad enum
        "request_type": "DATA_SOURCE",
        "status": "PENDING",
        "complexity": 11,  # Out of bounds
    }
    ok, errors = validate_request(req)
    assert ok is False
    assert "Field priority must be one of ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']" in errors
    assert "Field complexity must be <= 10" in errors


def test_validate_shipment_valid_missing_contaminated():
    ship = {
        "shipment_id": "550e8400-e29b-41d4-a716-446655440000",
        "route_id": "r1",
        "payload_size": 100,
        "arrival_time": "2026-08-07T12:00:00Z",
    }
    ok, errors = validate_shipment(ship)
    assert ok is True
    assert errors == []
