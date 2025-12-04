class ReadSheetRangeCapability:
    def __init__(self, sheets_integration):
        self.sheets_integration = sheets_integration

    def __call__(self, sheet, range_, has_headers):
        data = self.sheets_integration.read_range(sheet, range_, has_headers)
        headers = data["headers"]
        rows = data["rows"]

        return [dict(zip(headers, row)) for row in rows]