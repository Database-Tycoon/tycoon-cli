from tycoon_city.sim.logistics import LogisticsHub, Shipment


def test_logistics_landed():
    hub = LogisticsHub()
    valid_data = {
        "shipment_id": "550e8400-e29b-41d4-a716-446655440000",
        "route_id": "r1",
        "payload_size": 100,
        "arrival_time": "2026-08-07T12:00:00Z",
    }
    shipment = Shipment(valid_data)
    result, errors = hub.receive(shipment)

    assert result == "Landed"
    assert errors is None
    assert hub.contraband_count == 0
    assert len(hub.landed_shipments) == 1


def test_logistics_contraband():
    hub = LogisticsHub()
    invalid_data = {
        "shipment_id": "550e8400-e29b-41d4-a716-446655440000"
        # Missing required fields
    }
    shipment = Shipment(invalid_data)
    result, errors = hub.receive(shipment)

    assert result == "Contraband"
    assert errors is not None
    assert len(errors) > 0
    assert hub.contraband_count == 1
    assert len(hub.landed_shipments) == 0
