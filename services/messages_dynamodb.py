from boto3.dynamodb.conditions import Key
from typing import List, Dict, Any, Optional
from models.message import Message


class MessagesDynamodbService:
    def __init__(self, messages_table):
        self._table = messages_table


    def get_history(self, identity: str, limit: Optional[int] = None) -> List[Message]:

        kwargs: Dict[str, Any] = {
            "KeyConditionExpression": Key("identity").eq(identity),
            "ScanIndexForward": True,
        }
        if limit == 1:
            kwargs["ScanIndexForward"] = False
            kwargs["Limit"] = 1
        else:
            if limit is not None:
                kwargs["Limit"] = limit

        resp = self._table.query(**kwargs)
        items = resp.get("Items", [])

        messages = [self._from_dynamo_item(i) for i in items]

        return messages

    def save_message(
        self,
        *,
        identity: str,
        direction: str,
        channel: str,
        message_type: str,
        content: Dict[str, Any],
        payload: Dict[str, Any],
        timestamp_iso: str,
        timestamp_epoch: int,
        msg_id: str = "",
    ) -> None:
        message_key = f"{timestamp_iso}#{direction}#{msg_id}"

        item = {
            "identity": identity,
            "message_key": message_key,
            "channel": channel,
            "direction": direction,
            "message_type": message_type,
            "timestamp_iso": timestamp_iso,
            "timestamp_epoch": timestamp_epoch,
            "content": content,
            "payload": payload,
        }

        self._table.put_item(Item=item)

    def _from_dynamo_item(self, item: Dict[str, Any]) -> Message:
        return Message(
            identity=item["identity"],
            message_key=item["message_key"],
            channel=item.get("channel", ""),
            direction=item.get("direction", ""),
            message_type=item.get("message_type", ""),
            timestamp_iso=item.get("timestamp_iso"),
            timestamp_epoch=item.get("timestamp_epoch"),
            content=item.get("content"),
            payload=item.get("payload"),
        )