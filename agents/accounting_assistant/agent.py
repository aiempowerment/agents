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

        try:
            if task.process_type == "WHATSAPP_CONVERSATION":
                if task.task_type == "ANSWER_INCOMING_WHATSAPP_MESSAGE":
                    self.answer_incoming_whatsapp_message(task)

            if task.process_type == "WHATSAPP_DOCUMENT_PIPELINE":

                if task.task_type == "VALIDATE_DOCUMENT":
                    self.validate_document(task)
                if task.task_type == "SET_PASSWORD":
                    self.set_password(task)
                if task.task_type == "PDF_UNLOCK":
                    self.pdf_unlock(task)
                if task.task_type == "EXTRACT_DATA":
                    self.extract_data(task)

            #self.process_engine.run(
             #   process_type=task.process_type,
              #  event="TASK_SUCCEEDED",
               # task_type=task.task_type,
                #context=task.context_key,
               # payload=payload
            #)

        except Exception as e:
            print(e)
            payload["error_type"] = str(e)

            self.process_engine.run(
                process_type=task.process_type,
                event="TASK_FAILED",
                task_type=task.task_type,
                context=task.context_key,
                payload=payload
            )

    def extract_data(self, task):
        phone = task.payload.get("phone")
        timestamp_epoch = task.payload.get("timestamp_epoch")
        document_id = task.payload.get("document_id")

        file_key = f"whatsapp_media/{phone}/{timestamp_epoch}_{document_id}.pdf"

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

        send_message_capability(phone, "Muy bien, el documento es un PDF válido.")

    def pdf_unlock(self, task):

        identity = task.payload.get("identity")
        phone = task.payload.get("phone")
        timestamp_epoch = task.payload.get("timestamp_epoch")
        document_id = task.payload.get("document_id")

        get_password_capability = self.capabilities["get_password"]
        password = get_password_capability(identity)

        file_key = f"whatsapp_media/{phone}/{timestamp_epoch}_{document_id}.pdf"

        unlock_pdf_capability = self.capabilities["unlock_pdf"]
        unlock_pdf_capability(file_key, password["password"]["password"])

    def set_password(self, task):

        identity = task.payload.get("identity")

        set_password_capability = self.capabilities["set_password"]
        set_password_capability(identity, "sfdgdfg")
        

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

        llm_response = llm_chat_capability(
            prompt=prompt,
            system="Respondé siempre en español latino, tono profesional y cálido.",
        )

        send_result = send_message_capability(identity_phone, llm_response)