from typing import Dict, Any


class SetPasswordCapability:
    def __init__(self, contacts_integration):
        self.contacts_integration = contacts_integration

    def __call__(self, identity: str, password: str) -> Dict[str, Any]:
        contact_id = self.contacts_integration.resolve_contact_id(identity)

        if not contact_id:
            return {
                "identity": identity,
                "contact_id": None,
                "profile": None,
                "summary": None,
            }

        password = self.contacts_integration.set_password(contact_id, password)

        return {
            "identity": identity,
            "contact_id": contact_id,
            "password": password,
        }