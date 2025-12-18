from agents.agent import Agent
from core.cognition.prompt_builder import PromptBuilder
from core.cognition.conversation_context_builder import ConversationContextBuilder
from pathlib import Path


class AccountingAssistantAgent(Agent):

    name = "ACCOUNTING_ASSISTANT"
    required_capabilities = ["llm_chat", "read_messages", "read_sheet_range", "send_message"]

    def handle(self, task):

        if task.process_type=="READ_INCOMING_WHATSAPP_MESSAGE":
            if task.task_type=="ANSWER_INCOMING_WHATSAPP_MESSAGE":
                self.answer_incoming_whatsapp_message(task)
            if task.task_type=="PROCESS_INCOMING_WHATSAPP_DOCUMENT":
                self.process_incoming_whatsapp_document(task)

        if task.process_type=="PROCESS_INCOMING_WHATSAPP_DOCUMENT":
            if task.task_type=="DETECT_PDF_ENCRYPTION":
                self.detect_pdf_encryption(task)

        if task.process_type=="CLIENT_BANK_STATEMENT_FOLLOW_UP":
            if task.task_type=="DETECT_PDF_ENCRYPTION":
                self.detect_pdf_encryption(task)

    def process_incoming_whatsapp_document(self, task):
        send_message = self.capabilities["send_message"]

        identity = task.context_key
        identity_phone = identity.split(":", 1)[-1]

        response = "PROCESS_INCOMING_WHATSAPP_DOCUMENT OK"

        print(response)

        client_id = ctx["client_id"]
        year = ctx["year"]
        month = ctx["month"]
        bank = ctx["bank"]   

        context = {}

        result = self.process_engine.run(
            process_type="CLIENT_BANK_STATEMENT_FOLLOW_UP",
            event=event,
            context=context,
        )

        return {
            "phone": identity_phone,
            "result": result,
        }

    def detect_pdf_encryption(self, task):
        send_message = self.capabilities["send_message"]

        identity = task.context_key
        identity_phone = identity.split(":", 1)[-1]

        response = "DETECT_PDF_ENCRYPTION OK"

        print(response)

        client_id = ctx["client_id"]
        year = ctx["year"]
        month = ctx["month"]
        bank = ctx["bank"]   

        context = {}

        result = self.process_engine.run(
            process_type="CLIENT_BANK_STATEMENT_FOLLOW_UP",
            event=event,
            context=context,
        )

        return {
            "phone": identity_phone,
            "result": result,
        }

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

        return {
            "phone": identity_phone,
            "history": history,
            "llm_prompt": prompt,
            "llm_response": llm_response,
            "send_result": send_result,
        }