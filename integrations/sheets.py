class SheetsIntegration:
    def __init__(self, sheets_service):
        self.sheets_service = sheets_service

    def read_range(self, sheet_name: str, range_: str, has_headers: bool = False):
        data = self.sheets_service.read_range(sheet_name, range_)
        
        if has_headers:
            if data["values"]:
                headers = data["values"][0]
                rows = data["values"][1:]
                return {
                    "headers": headers,
                    "rows": rows,
                    "range": data["range"],
                }
        
        return {
            "headers": None,
            "rows": data["values"],
            "range": data["range"],
        }