from typing import Dict, Any, Optional
import time
import uuid


class MemoryDynamodbService:
    def __init__(self, memory_table):
        self._table = memory_table

    def get_state(self, *, channel_id: str) -> Dict[str, Any]:
        if not channel_id:
            raise ValueError("CHANNEL_ID_MISSING")

        resp = self._table.get_item(
            Key={
                "pk": f"CH#{channel_id}",
                "sk": "STATE",
            }
        )

        item = resp.get("Item")
        if item:
            return item

        now = int(time.time())

        state = {
            "pk": f"CH#{channel_id}",
            "sk": "STATE",
            "channel_id": channel_id,
            "version": 1,
            "created_at": now,
            "updated_at": now,
            "charter": {},
            "meta": {
                "stable": True,
                "phase": "idle",
                "confidence": "high",
            },
            "priorities": {},
            "next_action": {},
            "blockers": {},
            "events": {},
            "captures": {},
            "closeouts": {},
        }

        self._table.put_item(Item=state)
        return state

    def update_state(self, *, channel_id: str, op: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not channel_id:
            raise ValueError("CHANNEL_ID_MISSING")
        if not op:
            raise ValueError("OP_MISSING")
        if payload is None:
            raise ValueError("PAYLOAD_MISSING")

        self.get_state(channel_id=channel_id)

        if op == "set_charter":
            return self._set_charter(channel_id=channel_id, payload=payload)

        if op == "set_meta":
            return self._set_meta(channel_id=channel_id, payload=payload)

        if op == "set_next_action":
            return self._set_next_action(channel_id=channel_id, payload=payload)

        if op == "clear_next_action":
            return self._clear_next_action(channel_id=channel_id)

        if op == "set_priority":
            return self._set_priority(channel_id=channel_id, payload=payload)

        if op == "archive_priority":
            return self._archive_priority(channel_id=channel_id, payload=payload)

        if op == "upsert_blocker":
            return self._upsert_blocker(channel_id=channel_id, payload=payload)

        if op == "archive_blocker":
            return self._archive_blocker(channel_id=channel_id, payload=payload)

        if op == "upsert_event":
            return self._upsert_event(channel_id=channel_id, payload=payload)

        if op == "archive_event":
            return self._archive_event(channel_id=channel_id, payload=payload)

        if op == "add_capture":
            return self._add_capture(channel_id=channel_id, payload=payload)

        if op == "archive_capture":
            return self._archive_capture(channel_id=channel_id, payload=payload)

        if op == "add_closeout":
            return self._add_closeout(channel_id=channel_id, payload=payload)

        raise ValueError("OP_INVALID")

    def _base_update(self, *, channel_id: str, update_expression: str, ean: Dict[str, str], eav: Dict[str, Any]) -> Dict[str, Any]:
        now = int(time.time())

        update_expression = (
            "SET "
            "channel_id = if_not_exists(channel_id, :channel_id), "
            "created_at = if_not_exists(created_at, :now), "
            "updated_at = :now, "
            "version = if_not_exists(version, :zero) + :one, "
            + update_expression
        )

        eav = {
            **(eav or {}),
            ":channel_id": channel_id,
            ":now": now,
            ":zero": 0,
            ":one": 1,
        }

        kwargs = {
            "Key": {"pk": f"CH#{channel_id}", "sk": "STATE"},
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": eav,
            "ReturnValues": "ALL_NEW",
        }

        if ean:
            kwargs["ExpressionAttributeNames"] = ean

        resp = self._table.update_item(**kwargs)

        return resp["Attributes"]

    def _set_charter(self, *, channel_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        charter = payload.get("charter")
        if charter is None:
            raise ValueError("CHARTER_MISSING")

        return self._base_update(
            channel_id=channel_id,
            update_expression=" charter = :charter",
            ean={},
            eav={":charter": charter},
        )

    def _set_meta(self, *, channel_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        patch = payload.get("meta")
        if patch is None:
            raise ValueError("META_MISSING")

        stable = patch.get("stable")
        phase = patch.get("phase")
        confidence = patch.get("confidence")

        ean = {"#m": "meta"}
        eav: Dict[str, Any] = {}

        sets = []
        if stable is not None:
            sets.append("#m.#stable = :stable")
            ean["#stable"] = "stable"
            eav[":stable"] = stable
        if phase is not None:
            sets.append("#m.#phase = :phase")
            ean["#phase"] = "phase"
            eav[":phase"] = phase
        if confidence is not None:
            sets.append("#m.#confidence = :confidence")
            ean["#confidence"] = "confidence"
            eav[":confidence"] = confidence

        if not sets:
            raise ValueError("META_PATCH_EMPTY")

        return self._base_update(
            channel_id=channel_id,
            update_expression=" " + ", ".join(sets),
            ean=ean,
            eav=eav,
        )

    def _set_next_action(self, *, channel_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        title = payload.get("title")
        body = payload.get("body")
        if not title:
            raise ValueError("TITLE_MISSING")
        if not body:
            raise ValueError("BODY_MISSING")

        next_action = {
            "title": title,
            "body": body,
            "status": payload.get("status", "active"),
            "importance": payload.get("importance", "high"),
        }

        return self._base_update(
            channel_id=channel_id,
            update_expression=" next_action = :next_action",
            ean={},
            eav={":next_action": next_action},
        )

    def _clear_next_action(self, *, channel_id: str) -> Dict[str, Any]:
        return self._base_update(
            channel_id=channel_id,
            update_expression=" next_action = :empty",
            ean={},
            eav={":empty": {}},
        )

    def _set_priority(self, *, channel_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        rank = payload.get("rank")
        title = payload.get("title")
        body = payload.get("body")

        if rank is None:
            raise ValueError("PRIORITY_RANK_MISSING")
        if rank not in [1, 2, 3]:
            raise ValueError("PRIORITY_RANK_INVALID")
        if not title:
            raise ValueError("TITLE_MISSING")
        if not body:
            raise ValueError("BODY_MISSING")

        pid = payload.get("id") or f"p{rank}"
        pr = {
            "id": pid,
            "rank": rank,
            "title": title,
            "body": body,
            "status": payload.get("status", "active"),
            "importance": payload.get("importance", "high"),
        }

        ean = {"#p": "priorities", "#id": pid}
        eav = {":pr": pr}

        return self._base_update(
            channel_id=channel_id,
            update_expression=" #p.#id = :pr",
            ean=ean,
            eav=eav,
        )

    def _archive_priority(self, *, channel_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        pid = payload.get("id")
        if not pid:
            raise ValueError("PRIORITY_ID_MISSING")

        ean = {"#p": "priorities", "#id": pid, "#status": "status"}
        eav = {":arch": "archived"}

        return self._base_update(
            channel_id=channel_id,
            update_expression=" #p.#id.#status = :arch",
            ean=ean,
            eav=eav,
        )

    def _upsert_blocker(self, *, channel_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        bid = payload.get("id") or f"b{uuid.uuid4()}"
        body = payload.get("body")
        if not body:
            raise ValueError("BODY_MISSING")

        bl = {
            "id": bid,
            "body": body,
            "status": payload.get("status", "active"),
            "importance": payload.get("importance", "high"),
        }

        ean = {"#b": "blockers", "#id": bid}
        eav = {":bl": bl}

        return self._base_update(
            channel_id=channel_id,
            update_expression=" #b.#id = :bl",
            ean=ean,
            eav=eav,
        )

    def _archive_blocker(self, *, channel_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        bid = payload.get("id")
        if not bid:
            raise ValueError("BLOCKER_ID_MISSING")

        ean = {"#b": "blockers", "#id": bid, "#status": "status"}
        eav = {":arch": "archived"}

        return self._base_update(
            channel_id=channel_id,
            update_expression=" #b.#id.#status = :arch",
            ean=ean,
            eav=eav,
        )

    def _upsert_event(self, *, channel_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        eid = payload.get("id") or f"e{uuid.uuid4()}"
        title = payload.get("title")
        body = payload.get("body", "")
        valid_from = payload.get("valid_from")
        valid_until = payload.get("valid_until")

        if not title:
            raise ValueError("TITLE_MISSING")
        if valid_from is None:
            raise ValueError("VALID_FROM_MISSING")
        if valid_until is None:
            raise ValueError("VALID_UNTIL_MISSING")
        if valid_until < valid_from:
            raise ValueError("EVENT_WINDOW_INVALID")

        ev = {
            "id": eid,
            "title": title,
            "body": body,
            "valid_from": int(valid_from),
            "valid_until": int(valid_until),
            "status": payload.get("status", "active"),
            "importance": payload.get("importance", "critical"),
        }

        ean = {"#e": "events", "#id": eid}
        eav = {":ev": ev}

        return self._base_update(
            channel_id=channel_id,
            update_expression=" #e.#id = :ev",
            ean=ean,
            eav=eav,
        )

    def _archive_event(self, *, channel_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        eid = payload.get("id")
        if not eid:
            raise ValueError("EVENT_ID_MISSING")

        ean = {"#e": "events", "#id": eid, "#status": "status"}
        eav = {":arch": "archived"}

        return self._base_update(
            channel_id=channel_id,
            update_expression=" #e.#id.#status = :arch",
            ean=ean,
            eav=eav,
        )

    def _add_capture(self, *, channel_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        text = payload.get("text") or payload.get("body")
        if not text:
            raise ValueError("CAPTURE_TEXT_MISSING")

        cid = payload.get("id") or f"c{uuid.uuid4()}"
        now = int(time.time())

        cap = {
            "id": cid,
            "body": text,
            "status": payload.get("status", "active"),
            "created_at": now,
        }

        ean = {"#c": "captures", "#id": cid}
        eav = {":cap": cap}

        return self._base_update(
            channel_id=channel_id,
            update_expression=" #c.#id = :cap",
            ean=ean,
            eav=eav,
        )

    def _archive_capture(self, *, channel_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        cid = payload.get("id")
        if not cid:
            raise ValueError("CAPTURE_ID_MISSING")

        ean = {"#c": "captures", "#id": cid, "#status": "status"}
        eav = {":arch": "archived"}

        return self._base_update(
            channel_id=channel_id,
            update_expression=" #c.#id.#status = :arch",
            ean=ean,
            eav=eav,
        )

    def _add_closeout(self, *, channel_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        close_id = payload.get("id") or f"cl{uuid.uuid4()}"
        now = int(time.time())

        closeout = {
            "id": close_id,
            "created_at": now,
            "summary": payload.get("summary", ""),
            "friction": payload.get("friction", ""),
            "confidence": payload.get("confidence", ""),
            "stable": payload.get("stable"),
            "signals": payload.get("signals", {}),
        }

        ean = {"#cl": "closeouts", "#id": close_id}
        eav = {":clo": closeout}

        return self._base_update(
            channel_id=channel_id,
            update_expression=" #cl.#id = :clo",
            ean=ean,
            eav=eav,
        )