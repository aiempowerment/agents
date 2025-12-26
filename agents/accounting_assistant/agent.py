from agents.agent import Agent
from core.cognition.prompt_builder import PromptBuilder
from core.cognition.conversation_context_builder import ConversationContextBuilder
from core.cognition.bank_statement_parser import BankStatementParser
from pathlib import Path


class AccountingAssistantAgent(Agent):

    name = "ACCOUNTING_ASSISTANT"
    required_capabilities = ["llm_chat", "read_messages", "read_sheet_range", "send_message"]

    def handle(self, task):
        payload = task.payload

        ## NACHO: ESTE IF PORQUE???
        if not isinstance(payload, dict):
            payload = {"raw_payload": payload}

        event = "TASK_SUCCEEDED"
        response = None
        try:
            if task.process_type == "WHATSAPP_CONVERSATION":
                if task.task_type == "ANSWER_INCOMING_WHATSAPP_MESSAGE":
                    response = self.answer_incoming_whatsapp_message(task)
                elif task.task_type == "SET_PASSWORD":
                    response = self.set_password(task)
                elif task.task_type == "REPROCESS_PENDING_FILES":
                    response = self.reprocess_pending_files(task)

                if isinstance(response, dict) and response.get("action"):
                    event = "LLM_ACTION_REQUESTED"
                    payload = response

            elif task.process_type == "WHATSAPP_DOCUMENT_PIPELINE":
                if task.task_type == "VALIDATE_DOCUMENT":
                    self.validate_document(task)
                elif task.task_type == "PDF_UNLOCK":
                    self.pdf_unlock(task)
                elif task.task_type == "EXTRACT_DATA":
                    self.extract_data(task)
                elif task.task_type == "SEND_WHATSAPP_MESSAGE":
                    response = self.send_whatsapp_message(task)

        except Exception as e:
            print(e)
            payload["error_type"] = str(e)
            payload["error_message"] = type(e).__name__
            event = "TASK_FAILED"

        self.process_engine.run(
            process_type=task.process_type,
            event=event,
            task_type=task.task_type,
            context=task.context_key,
            payload=payload
        )

    def extract_data(self, task):
        phone = task.payload.get("phone")
        msg_id = task.payload.get("msg_id")
        media_id = task.payload.get("media_id")

        file_key = f"whatsapp_media/{phone}/{msg_id}_{media_id}.pdf"

        extract_data_pdf_capability = self.capabilities["extract_data_pdf"]
        data_pdf = extract_data_pdf_capability(file_key)

        parser = BankStatementParser()
        result = parser.parse(data_pdf)

        bank = result["bank"]
        movements = result["movements"]

        lines = []

        for m in movements:
            lines.append(f"{m.date_op} {m.concept} {m.amount}")

        response = "\n".join(lines)

        send_message_capability = self.capabilities["send_message"]
        send_message_capability(phone, response)

    def validate_document(self, task):
        send_message_capability = self.capabilities["send_message"]

        payload = task.payload
        phone = payload["phone"]

        document = payload.get("document")
        if not document:
            send_message_capability(phone, "No se recibió ningún documento.")
            raise ValueError("DOCUMENT_MISSING")

        mime_type = document.get("mime_type")
        if mime_type != "application/pdf":
            send_message_capability(phone, "El documento debe ser en formato PDF.")
            raise ValueError(f"INVALID_MIME_TYPE")

    def pdf_unlock(self, task):

        identity = task.payload.get("identity")
        phone = task.payload.get("phone")
        msg_id = task.payload.get("msg_id")
        media_id = task.payload.get("media_id")

        get_password_capability = self.capabilities["get_password"]
        password = get_password_capability(identity)

        file_key = f"whatsapp_media/{phone}/{msg_id}_{media_id}.pdf"

        unlock_pdf_capability = self.capabilities["unlock_pdf"]
        unlock_pdf_capability(file_key, password["password"]["password"])

    def set_password(self, task):

        identity = task.context_key.get("identity")
        password = task.payload.get("password")

        set_password_capability = self.capabilities["set_password"]
        set_password_capability(identity, password)
        
        return True

    def answer_incoming_whatsapp_message(self, task):

        read_messages_capability = self.capabilities["read_messages"]
        llm_chat_capability = self.capabilities["llm_chat"]
        send_message_capability = self.capabilities["send_message"]
        get_contact_capability = self.capabilities["get_contact"]

        identity = task.context_key.get("identity")
        identity_phone = identity.split(":", 1)[-1]
        history = read_messages_capability(identity)
        contact = get_contact_capability(identity)

        context_builder = ConversationContextBuilder(max_messages=10)
        conversation_context = context_builder.build(history)

        prompt_builder = PromptBuilder(base_dir=Path(__file__).parent / "prompts")

        prompt = prompt_builder.build(
            "answer_incoming_whatsapp",
            {"conversation_context": conversation_context, "contact": contact}
        )

        system = prompt_builder.build("answer_incoming_whatsapp_system")

        llm_response = llm_chat_capability(
            prompt=prompt,
            system=system,
        )

        send_result = send_message_capability(identity_phone, llm_response["reply_text"])

        return llm_response

    def send_whatsapp_message(self, task):

        send_message_capability = self.capabilities["send_message"]

        phone = task.payload.get("phone")
        message = task.payload.get("message")

        send_result = send_message_capability(phone, message)

        return send_result
    
    def reprocess_pending_files(self, task):

        process_type = "WHATSAPP_DOCUMENT_PIPELINE"

        list_files_capability = self.capabilities["list_files"]
        get_processes_state_capability = self.capabilities["get_processes_state"]

        identity = task.context_key.get("identity")
        identity_phone = identity.split(":", 1)[-1]
        directory = f"whatsapp_media/{identity_phone}/"

        files = list_files_capability(directory, ["pdf"])
        for file in files:
            filename = file.split("/")[-1]
            msg_id, media_id = filename.split("_", 1)
            media_id = media_id.split(".")[0]
            business_key = f"{msg_id}#{media_id}"
            state = get_processes_state_capability(process_type, business_key)

            if state["state"] == "WAITING_PASSWORD":
                context_key = {
                    "msg_id": msg_id,
                    "media_id": media_id
                }
                payload = context_key
                payload["identity"] = identity
                payload["phone"] = identity_phone
                self.process_engine.run(
                    process_type=process_type,
                    event="PASSWORD_CHANGED",
                    task_type=task.task_type,
                    context=context_key,
                    payload=payload
                )

        return state