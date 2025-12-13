from typing import Optional, Dict, Any


class ContactsIntegration:
    def __init__(self, contacts_service):
        self.contacts_service = contacts_service

    def resolve_contact_id(self, identity: str) -> Optional[str]:
        return self.contacts_service.resolve_contact_id(identity)

    def get_profile(self, contact_id: str) -> Optional[Dict[str, Any]]:
        return self.contacts_service.get_profile(contact_id)

    def get_summary_current(self, contact_id: str) -> Optional[Dict[str, Any]]:
        return self.contacts_service.get_summary_current(contact_id)