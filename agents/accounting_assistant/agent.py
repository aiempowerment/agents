from agents.agent import Agent
from core.cognition.prompt_builder import PromptBuilder
from core.cognition.conversation_context_builder import ConversationContextBuilder
from pathlib import Path


class AccountingAssistantAgent(Agent):

    name = "ACCOUNTING_ASSISTANT"
    required_capabilities = ["llm_chat", "read_messages", "read_sheet_range", "send_message"]

    def handle(self, task):

        payload = {
            "task_type": task.task_type
        }

        try:
            if task.process_type=="WHATSAPP_CONVERSATION":
                if task.task_type=="ANSWER_INCOMING_WHATSAPP_MESSAGE":
                    self.answer_incoming_whatsapp_message(task)

            if task.process_type=="WHATSAPP_DOCUMENT_PIPELINE":
                if task.task_type=="VALIDATE_DOCUMENT":
                    self.validate_document(task)
                if task.task_type=="DETECT_PDF_ENCRYPTION":
                    self.detect_pdf_encryption(task)


            self.process_engine.run(
                process_type=task.process_type,
                event="TASK_SUCCEEDED",
                context=task.context_key,
                payload=payload
            )

        except Exception as e:
            print(e)
            self.process_engine.run(
                process_type=task.process_type,
                event="TASK_FAILED",
                context=task.context_key,
                payload=payload
            )

    def validate_document(self, task):

        print("validate_document")

    def detect_pdf_encryption(self, task):
        
        print("detect_pdf_encryption")

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
        print(conversation_context)

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