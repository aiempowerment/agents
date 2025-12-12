from agents.agent import Agent


class AccountingAssistantAgent(Agent):
    name = "ACCOUNTING_ASSISTANT_AGENT"
    required_capabilities = ["llm_chat", "read_messages", "read_sheet_range", "send_message"]

    def handle(self, task):

        if task.process_type=="CLIENT_BANK_STATEMENT_FOLLOW_UP":
            if task.task_type=="SEND_INITIAL_REQUEST":
                self.send_initial_request(task.context_key)
            if task.task_type=="SE_ADELANTO":
                print("COMPLETOOOOOO")

    def send_initial_request(self, task):
        
        read_sheet_range = self.capabilities["read_sheet_range"]
        read_messages = self.capabilities["read_messages"]
        llm_chat = self.capabilities["llm_chat"]
        send_message = self.capabilities["send_message"]

        clients = read_sheet_range("clients", "A:D", True)

        pending_clients = [c for c in clients if c.get("status") == "pending"]

        results = []

        for client in pending_clients:
            phone = client.get("phone")
            client_name = client.get("name")
            identity = f"whatsapp:{phone}"

            if not phone:
                continue

            # Retrieve normalized message history for this client
            # history format (from ReadMessagesCapability):
            # [
            #     {"direction": "in" | "out", "text": "<string>"},
            # ]
            history = read_messages(identity)

            # Build a plain-text representation of the conversation for the LLM
            history_lines = []
            for msg in history:
                direction = msg.get("direction")
                text = msg.get("text", "")

                if direction == "in":
                    speaker = "Cliente"
                elif direction == "out":
                    speaker = "Agente"
                else:
                    speaker = "Otro"

                history_lines.append(f"{speaker}: {text}")

            # Optionally limit history length (e.g., last 20 lines)
            conversation_context = "\n".join(history_lines[-20:])

            # Build dynamic LLM prompt using conversation history + client info
            prompt = (
                "Este es el historial reciente de la conversación con el cliente:\n\n"
                f"{conversation_context}\n\n"
                "Ahora, genera un nuevo mensaje amable para el cliente "
                f"llamado {client_name}, que tiene un estado pendiente. "
                "El mensaje debe ser breve, claro y cordial."
            )

            # Query the LLM with context
            llm_response = llm_chat(
                prompt=prompt,
                system="Respondé siempre en español latino, tono profesional y cálido.",
            )

            # Send the generated message
            send_result = send_message(phone, llm_response)

            results.append({
                "client": client,
                "history": history,
                "llm_prompt": prompt,
                "llm_response": llm_response,
                "send_result": send_result,
            })

        # === Build final result ===
        return results