from services.messages_dynamodb import MessagesDynamodbService
from services.messages_print import MessagesPrintService
from services.messages_whatsapp import MessagesWhatsappService
from services.sheets_google import SheetsGoogleService
from services.llm_openai import LlmOpenaiService
from services.contacts_dynamodb import ContactsDynamodbService

from integrations.messages import MessagesIntegration
from integrations.sheets import SheetsIntegration
from integrations.llm import LlmIntegration
from integrations.contacts import ContactsIntegration

from core.capabilities.read_messages import ReadMessagesCapability
from core.capabilities.send_message import SendMessageCapability
from core.capabilities.read_sheet_range import ReadSheetRangeCapability
from core.capabilities.llm_chat import LlmChatCapability
from core.capabilities.get_contact import GetContactCapability

from agents.accounting_assistant.agent import AccountingAssistantAgent


class AccountingAssistantAgentFactory:
    @staticmethod
    def build(tenant_config, messages_table, contacts_table, process_engine):

        history_service = MessagesDynamodbService(messages_table)
        message_service = MessagesWhatsappService(tenant_config=tenant_config)
        # message_service = MessagesPrintService(tenant_config=tenant_config)
        sheets_service = SheetsGoogleService(tenant_config=tenant_config)
        llm_service = LlmOpenaiService(tenant_config=tenant_config)
        contact_service = ContactsDynamodbService(contacts_table)

        message_integration = MessagesIntegration(history_service, message_service)
        sheets_integration = SheetsIntegration(sheets_service)
        llm_integration = LlmIntegration(llm_service)
        contact_integration = ContactsIntegration(contact_service)

        read_messages_cap = ReadMessagesCapability(message_integration)
        send_message_cap = SendMessageCapability(message_integration)
        read_sheet_range_cap = ReadSheetRangeCapability(sheets_integration)
        llm_chat_cap = LlmChatCapability(llm_integration)
        get_contact_cap = GetContactCapability(contact_integration)

        capabilities = {
            "read_messages": read_messages_cap,
            "send_message": send_message_cap,
            "read_sheet_range": read_sheet_range_cap,
            "llm_chat": llm_chat_cap,
            "get_contact": get_contact_cap,
        }

        agent = AccountingAssistantAgent(
            capabilities=capabilities,
            process_engine=process_engine,
        )

        return agent