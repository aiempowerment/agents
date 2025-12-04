from agents.agent import Agent


class HelloWorldAgent(Agent):
    name = "hello_world_agent"
    required_capabilities = ["read_messages", "send_message"]

    def handle(self, context):
        
        read_messages = self.capabilities["read_messages"]
        send_message = self.capabilities["send_message"]
                                         
        phone = "5571969848"             
        identity = f"whatsapp:{phone}"
        history = read_messages(identity)
        print(history)
        
        message = "Hello world!"
        send_result = send_message(phone, message)

        return send_result