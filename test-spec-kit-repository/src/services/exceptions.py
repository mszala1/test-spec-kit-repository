class UpstreamError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class LocationNotFoundError(Exception):
    def __init__(self, location: str) -> None:
        self.location = location
        self.message = f"Location not found: {location}"
        super().__init__(self.message)


class InvalidDateError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
