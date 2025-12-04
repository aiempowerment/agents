from services.messages_dynamodb import MessagesDynamodbService
from services.messages_print import MessagesPrintService

from integrations.messages import MessagesIntegration

from core.capabilities.read_messages import ReadMessagesCapability
from core.capabilities.send_message import SendMessageCapability

from agents.hello_world.agent import HelloWorldAgent


class HelloWorldAgentFactory:
    @staticmethod
    def build(tenant_config, messages_table, process_engine):

        tenant_id = tenant_config.get("tenant_id")
        print(f"tenant_id {tenant_id}")

        history_service = MessagesDynamodbService(messages_table)
        message_service = MessagesPrintService()

        message_integration = MessagesIntegration(history_service, message_service)

        read_messages_cap = ReadMessagesCapability(message_integration)
        send_message_cap = SendMessageCapability(message_integration)

        capabilities = {
            "read_messages": read_messages_cap,
            "send_message": send_message_cap,
        }

        agent = HelloWorldAgent(
            capabilities=capabilities,
            process_engine=process_engine,
        )

        return agent