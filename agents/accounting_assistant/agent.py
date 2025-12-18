from agents.agent import Agent
from core.cognition.prompt_builder import PromptBuilder
from core.cognition.conversation_context_builder import ConversationContextBuilder
from pathlib import Path


class AccountingAssistantAgent(Agent):

    name = "ACCOUNTING_ASSISTANT"
    required_capabilities = ["llm_chat", "read_messages", "read_sheet_range", "send_message"]

    def handle(self, task):

        try:
            if task.process_type=="READ_INCOMING_WHATSAPP_MESSAGE":
                if task.task_type=="ANSWER_INCOMING_WHATSAPP_MESSAGE":
                    self.answer_incoming_whatsapp_message(task)

            if task.process_type=="PROCESS_INCOMING_WHATSAPP_DOCUMENT":
                if task.task_type=="VALIDATE_INCOMING_WHATSAPP_DOCUMENT":
                    self.validate_incoming_whatsapp_document(task)
                if task.task_type=="DETECT_PDF_ENCRYPTION":
                    self.detect_pdf_encryption(task)

            if task.process_type=="CLIENT_BANK_STATEMENT_FOLLOW_UP":
                if task.task_type=="DETECT_PDF_ENCRYPTION":
                    self.detect_pdf_encryption(task)

            self.process_engine.run(
                process_type=task.process_type,
                event="TASK_SUCCEEDED",
                context=task.context_key
            )

        except Exception as e:

            self.process_engine.run(
                process_type=task.process_type,
                event="TASK_FAILED",
                context=task.context_key
            )

    def validate_incoming_whatsapp_document(self, task):
        send_message = self.capabilities["send_message"]

        identity = task.context_key.get("identity")
        identity_phone = identity.split(":", 1)[-1]

        message = "validate_incoming_whatsapp_document"

        send_result = send_message(identity_phone, message)

    def process_incoming_whatsapp_document(self, task):
        send_message = self.capabilities["send_message"]

        identity = task.context_key.get("identity")
        identity_phone = identity.split(":", 1)[-1]

        message = "process_incoming_whatsapp_document"

        send_result = send_message(identity_phone, message)

    def detect_pdf_encryption(self, task):
        send_message = self.capabilities["send_message"]

        identity = task.context_key.get("identity")
        identity_phone = identity.split(":", 1)[-1]

        message = "detect_pdf_encryption"

        send_result = send_message(identity_phone, message)

    def answer_incoming_whatsapp_message(self, task):

        read_messages = self.capabilities["read_messages"]
        llm_chat = self.capabilities["llm_chat"]
        send_message = self.capabilities["send_message"]
        get_contact = self.capabilities["get_contact"]

        identity = task.context_key.get("identity")
        identity_phone = identity.split(":", 1)[-1]
        history = read_messages(identity)
        contact = get_contact(identity)

        context_builder = ConversationContextBuilder(max_messages=10)
        conversation_context = context_builder.build(history)

        prompt_builder = PromptBuilder(base_dir=Path(__file__).parent / "prompts")

        prompt = prompt_builder.build(
            "answer_incoming_whatsapp",
            {"conversation_context": conversation_context, "contact": contact}
        )

        llm_response = llm_chat(
            prompt=prompt,
            system="Respondé siempre en español latino, tono profesional y cálido.",
        )

        send_result = send_message(identity_phone, llm_response)