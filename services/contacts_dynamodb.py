from boto3.dynamodb.conditions import Key
from typing import Dict, Any, Optional, List


class ContactsDynamodbService:
    def __init__(self, contacts_table):
        self._table = contacts_table

    def resolve_contact_id(self, identity: str) -> Optional[str]:
        resp = self._table.get_item(
            Key={
                "pk": f"IDENTITY#{identity}",
                "sk": "CONTACT",
            }
        )
        item = resp.get("Item")
        if not item:
            return None
        return item.get("contact_id")

    def get_profile(self, contact_id: str) -> Optional[Dict[str, Any]]:
        resp = self._table.get_item(
            Key={
                "pk": f"CONTACT#{contact_id}",
                "sk": "PROFILE",
            }
        )
        return resp.get("Item")

    def get_summary_current(self, contact_id: str) -> Optional[Dict[str, Any]]:
        resp = self._table.get_item(
            Key={
                "pk": f"CONTACT#{contact_id}",
                "sk": "SUMMARY#CURRENT",
            }
        )
        return resp.get("Item")

    def list_identities(self, contact_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        kwargs: Dict[str, Any] = {
            "KeyConditionExpression": Key("pk").eq(f"CONTACT#{contact_id}") & Key("sk").begins_with("IDENTITY#"),
            "ScanIndexForward": True,
        }
        if limit is not None:
            kwargs["Limit"] = limit

        resp = self._table.query(**kwargs)
        return resp.get("Items", [])