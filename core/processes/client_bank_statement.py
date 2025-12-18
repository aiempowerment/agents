from core.process_registry import ProcessRegistry


class ClientBankStatementProcess:
    PROCESS_TYPE = "CLIENT_BANK_STATEMENT_FOLLOW_UP"

    def build_business_key(ctx: dict) -> str:
        client_id = ctx["contact_id"]
        year = ctx["year"]
        month = ctx["month"]
        bank = ctx["bank"]      

        return f"{client_id}#{bank}#{year}#{month}"

    def apply_transition(state: str, event: str, data: dict) -> tuple[str, list[dict]]:
        tasks: list[dict] = []

        # ===== INIT → request statement (optional if your system already requested) =====
        if state == "INIT" and event == "BANK_STATEMENT_REQUESTED":
            return "STATEMENT_REQUESTED", [
                {
                    "task_type": "SEND_BANK_STATEMENT_REQUEST",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "payload": data,
                }
            ]

        # ===== file received =====
        if state in ["INIT", "STATEMENT_REQUESTED"] and event == "BANK_STATEMENT_FILE_RECEIVED":
            # data must include: { "file": { "s3_bucket": "...", "s3_key": "...", "filename": "..."} }
            return "STATEMENT_RECEIVED", [
                {
                    "task_type": "DETECT_PDF_ENCRYPTION",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "payload": data,
                }
            ]

        # ===== invalid file =====
        if state == "STATEMENT_RECEIVED" and event == "FILE_INVALID":
            return "INVALID_FILE", [
                {
                    "task_type": "NOTIFY_INVALID_FILE",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "payload": data,
                }
            ]

        # ===== encrypted? =====
        if state == "STATEMENT_RECEIVED" and event == "FILE_IS_ENCRYPTED":
            return "PASSWORD_REQUIRED", [
                {
                    "task_type": "REQUEST_BANK_STATEMENT_PASSWORD",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "payload": data,
                }
            ]

        if state == "STATEMENT_RECEIVED" and event == "FILE_NOT_ENCRYPTED":
            return "READY_TO_ANALYZE", [
                {
                    "task_type": "ANALYZE_BANK_STATEMENT",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "payload": data,
                }
            ]

        # ===== password flow =====
        if state in ["PASSWORD_REQUIRED", "WAITING_PASSWORD"] and event == "PASSWORD_RECEIVED":
            # initialize attempt counter if missing
            meta = data.get("meta", {}) or {}
            attempts = int(meta.get("password_attempts", 0))
            meta["password_attempts"] = attempts
            data["meta"] = meta

            return "PASSWORD_PROVIDED", [
                {
                    "task_type": "UNLOCK_BANK_STATEMENT_PDF",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "payload": data,
                }
            ]

        if state == "PASSWORD_REQUIRED" and event == "PASSWORD_TIMEOUT":
            return "WAITING_PASSWORD", []

        if state == "PASSWORD_PROVIDED" and event == "PASSWORD_INVALID":
            meta = data.get("meta", {}) or {}
            attempts = int(meta.get("password_attempts", 0)) + 1
            meta["password_attempts"] = attempts
            data["meta"] = meta

            if attempts >= ClientBankStatementProcess.MAX_PASSWORD_ATTEMPTS:
                return "FAILED_AUTH", [
                    {
                        "task_type": "NOTIFY_PASSWORD_FAILED",
                        "agent_type": "ACCOUNTING_ASSISTANT",
                        "payload": data,
                    }
                ]

            return "PASSWORD_REQUIRED", [
                {
                    "task_type": "REQUEST_BANK_STATEMENT_PASSWORD",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "payload": data,
                }
            ]

        if state == "PASSWORD_PROVIDED" and event == "PASSWORD_VALID":
            return "FILE_UNLOCKED", [
                {
                    "task_type": "ANALYZE_BANK_STATEMENT",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "payload": data,
                }
            ]

        # ===== analyze results =====
        if state in ["READY_TO_ANALYZE", "FILE_UNLOCKED"] and event == "FORMAT_UNKNOWN":
            return "MANUAL_REVIEW", [
                {
                    "task_type": "ESCALATE_MANUAL_REVIEW",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "payload": data,
                }
            ]

        if state in ["READY_TO_ANALYZE", "FILE_UNLOCKED"] and event == "ANALYSIS_SUCCESS":
            return "COMPLETED", [
                {
                    "task_type": "STORE_BANK_MOVEMENTS",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "payload": data,
                }
            ]

        if state in ["READY_TO_ANALYZE", "FILE_UNLOCKED"] and event == "ANALYSIS_FAILED":
            return "FAILED_ANALYSIS", [
                {
                    "task_type": "NOTIFY_ANALYSIS_FAILED",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "payload": data,
                }
            ]

        # ===== cancellation =====
        if event == "CLIENT_REFUSES":
            return "CANCELLED", [
                {
                    "task_type": "NOTIFY_CANCELLED",
                    "agent_type": "ACCOUNTING_ASSISTANT",
                    "payload": data,
                }
            ]

        return state, tasks

# Registrar proceso en el registry
ProcessRegistry.register(ClientBankStatementProcess)