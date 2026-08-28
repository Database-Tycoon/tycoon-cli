from tycoon_city.sim.contracts import validate_shipment


class Shipment:
    def __init__(self, data: dict):
        self.data = data


class LogisticsHub:
    def __init__(self):
        self.contraband_count = 0
        self.landed_shipments = []

    def receive(self, shipment: Shipment) -> tuple[str, list[str] | None]:
        ok, errors = validate_shipment(shipment.data)
        if ok:
            self.landed_shipments.append(shipment)
            return "Landed", None
        else:
            self.contraband_count += 1
            return "Contraband", errors
