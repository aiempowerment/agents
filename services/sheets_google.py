import json
from typing import Any, Dict
import boto3
import gspread
from google.oauth2.service_account import Credentials


class SheetsGoogleService:
    def __init__(self, tenant_config: Dict[str, Any]):
        self._config = tenant_config.get("sheets", {})
        self._region = self._config.get("region", {})
        self._spreadsheets = self._config.get("spreadsheets", {})
        self._client = None

    def _load_service_account_info(self) -> Dict[str, Any]:
        config = self._config.get("google", {})
        s3_path = config.get("service_account_s3")
        if not s3_path:
            raise RuntimeError("Missing sheets.google.service_account_s3 in tenant_config")

        s3 = boto3.client("s3", region_name=self._region)
        bucket, key = s3_path.replace("s3://", "").split("/", 1)
        obj = s3.get_object(Bucket=bucket, Key=key)
        return json.loads(obj["Body"].read())

    def _get_client(self):
        if self._client:
            return self._client

        info = self._load_service_account_info()
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        self._client = gspread.authorize(creds)
        return self._client

    def read_range(self, key: str, range_: str, has_headers: bool = False) -> Dict[str, Any]:
        spreadsheet_config = self._spreadsheets.get(key)
        if not spreadsheet_config:
            raise KeyError(f"Spreadsheets '{key}' not defined in tenant_config.sheets.spreadsheets")

        spreadsheet_id = spreadsheet_config["spreadsheet_id"]
        if not range_:
            raise ValueError(f"No range provided for spreadsheets '{key}'")

        client = self._get_client()
        sh = client.open_by_key(spreadsheet_id)
        values = sh.values_get(range_).get("values", [])

        if has_headers and values:
            headers = values[0]
            rows = values[1:]
        else:
            headers = []
            rows = values

        return {
            "key": key,
            "range": range_,
            "values": values,
            "headers": headers,
            "rows": rows,
        }