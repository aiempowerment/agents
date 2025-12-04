from core.process_registry import ProcessRegistry


class ClientBankStatementProcess:
    PROCESS_TYPE = "CLIENT_BANK_STATEMENT_FOLLOW_UP"

    def build_business_key(ctx: dict) -> str:
        """
        Define la unicidad del proceso:
        Un proceso por cliente + año + mes.
        """
        client_id = ctx["client_id"]          # requerido
        year = ctx["year"]                    # requerido
        month = ctx["month"]                  # requerido

        return f"{client_id}#{year}#{month}"

    def apply_transition(state: str, event: str, data: dict) -> tuple[str, list[dict]]:

        if state == "INIT" and event == "WHATSAPP_FILE_RECEIVED":
            return "PENDING_REQUEST", [
                {
                    "task_type": "SE_ADELANTO",
                    "agent_type": "ACCOUNTING_JUNIOR",
                    "payload": {},
                }
            ]

        if state == "INIT" and event == "CRON_MONTHLY_RUN":
            return "PENDING_REQUEST", [
                {
                    "task_type": "SEND_INITIAL_REQUEST",
                    "agent_type": "ACCOUNTING_JUNIOR",
                    "payload": {},
                }
            ]

        if state == "PENDING_REQUEST" and event == "TASK_COMPLETED_SEND_INITIAL_REQUEST":
            return "WAITING_CLIENT", []

        if state == "WAITING_CLIENT" and event == "WHATSAPP_FILE_RECEIVED":
            return "STATEMENT_RECEIVED", [
                {
                    "task_type": "PARSE_BANK_STATEMENT_PDF",
                    "agent_type": "ACCOUNTING_JUNIOR",
                    "payload": {"file_id": data["file_id"]},
                }
            ]

        if state == "STATEMENT_RECEIVED" and event == "TASK_COMPLETED_PARSE_PDF":
            return "PROCESSED", [
                {
                    "task_type": "UPLOAD_MOVEMENTS",
                    "agent_type": "ACCOUNTING_JUNIOR",
                    "payload": {"movements": data["movements"]},
                }
            ]

        if state == "PROCESSED" and event == "TASK_COMPLETED_UPLOAD_MOVEMENTS":
            return "COMPLETED", []

        return state, []

# Registrar proceso en el registry
ProcessRegistry.register(ClientBankStatementProcess)