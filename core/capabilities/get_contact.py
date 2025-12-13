from typing import Dict, Any, Optional


class GetContactCapability:
    def __init__(self, contacts_integration):
        self.contacts_integration = contacts_integration

    def __call__(self, identity: str) -> Dict[str, Any]:
        contact_id = self.contacts_integration.resolve_contact_id(identity)

        if not contact_id:
            return {
                "identity": identity,
                "contact_id": None,
                "profile": None,
                "summary": None,
            }

        profile = self.contacts_integration.get_profile(contact_id)
        summary_item = self.contacts_integration.get_summary_current(contact_id)

        summary = None
        if isinstance(summary_item, dict):
            summary = summary_item.get("summary")

        return {
            "identity": identity,
            "contact_id": contact_id,
            "profile": profile,
            "summary": summary,
        }