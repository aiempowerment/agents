from agents.agent import Agent
from core.cognition.prompt_builder import PromptBuilder
from core.cognition.conversation_context_builder import ConversationContextBuilder
from pathlib import Path


class AccountingAssistantAgent(Agent):
    name = "ACCOUNTING_ASSISTANT"
    required_capabilities = ["llm_chat", "read_messages", "read_sheet_range", "send_message"]

    def handle(self, task):

        if task.process_type=="READ_INCOMING_WHATSAPP_MESSAGE":
            if task.task_type=="READ_INCOMING_WHATSAPP_MESSAGE":
                self.answer_incoming_whatsapp_message(task)

        if task.process_type=="CLIENT_BANK_STATEMENT_FOLLOW_UP":
            if task.task_type=="SEND_INITIAL_REQUEST":
                self.send_initial_request(task.context_key)

    def answer_incoming_whatsapp_message(self, task):

        read_messages = self.capabilities["read_messages"]
        llm_chat = self.capabilities["llm_chat"]
        send_message = self.capabilities["send_message"]

        identity = task.context_key
        identity_phone = identity.split(":", 1)[-1]
        history = read_messages(identity)

        context_builder = ConversationContextBuilder(max_messages=20)
        conversation_context = context_builder.build(history)


        prompt_builder = PromptBuilder(base_dir=Path(__file__).parent / "prompts")

        prompt = prompt_builder.build(
            "answer_incoming_whatsapp.txt",
            {"conversation_context": conversation_context},
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

    def send_initial_request(self, task):
        
        read_sheet_range = self.capabilities["read_sheet_range"]

        clients = read_sheet_range("clients", "A:D", True)

        pending_clients = [c for c in clients if c.get("status") == "pending"]

        return pending_clients