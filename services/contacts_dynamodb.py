from boto3.dynamodb.conditions import Key
from typing import Dict, Any, Optional, List


class ContactsDynamodbService:
    def __init__(self, contacts_table):
        self._table = contacts_table

    def resolve_contact_id(self, identity: str) -> str:
        resp = self._table.get_item(
            Key={
                "pk": f"IDENTITY#{identity}",
                "sk": "CONTACT",
            }
        )
        item = resp.get("Item")
        if not item:
            raise ValueError("CONTACT_NOT_FOUND")

        contact_id = item.get("contact_id")
        if not contact_id:
            raise ValueError("CONTACT_NOT_FOUND")

        return contact_id

    def get_profile(self, contact_id: str) -> Dict[str, Any]:
        resp = self._table.get_item(
            Key={
                "pk": f"CONTACT#{contact_id}",
                "sk": "PROFILE",
            }
        )
        item = resp.get("Item")
        if not item:
            raise ValueError("PROFILE_NOT_FOUND")

        return item
    
    def set_password(self, contact_id: str, password: str) -> None:

        self._table.put_item(
            Item={
                "pk": f"CONTACT#{contact_id}",
                "sk": "PASSWORD",
                "password": password,
            }
        )

    def get_password(self, contact_id: str) -> Dict[str, Any]:
        resp = self._table.get_item(
            Key={
                "pk": f"CONTACT#{contact_id}",
                "sk": "PASSWORD",
            }
        )
        item = resp.get("Item")
        if not item:
            raise ValueError("PASSWORD_NOT_FOUND")

        password = item.get("password")
        if not password:
            raise ValueError("PASSWORD_NOT_FOUND")

        return item

    def get_summary_current(self, contact_id: str) -> Dict[str, Any]:
        resp = self._table.get_item(
            Key={
                "pk": f"CONTACT#{contact_id}",
                "sk": "SUMMARY#CURRENT",
            }
        )
        item = resp.get("Item")
        if not item:
            raise ValueError("SUMMARY_NOT_FOUND")

        return item

    def list_identities(self, contact_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        kwargs: Dict[str, Any] = {
            "KeyConditionExpression": Key("pk").eq(f"CONTACT#{contact_id}") & Key("sk").begins_with("IDENTITY#"),
            "ScanIndexForward": True,
        }
        if limit is not None:
            kwargs["Limit"] = limit

        resp = self._table.query(**kwargs)
        return resp.get("Items", [])