from services.messages_dynamodb import MessagesDynamodbService
from services.messages_print import MessagesPrintService
from services.messages_whatsapp import MessagesWhatsappService
from services.sheets_google import SheetsGoogleService
from services.llm_openai import LlmOpenaiService
from services.contacts_dynamodb import ContactsDynamodbService
from services.pdf_s3 import PdfS3Service

from integrations.messages import MessagesIntegration
from integrations.sheets import SheetsIntegration
from integrations.llm import LlmIntegration
from integrations.contacts import ContactsIntegration
from integrations.pdf import PdfIntegration

from core.capabilities.read_messages import ReadMessagesCapability
from core.capabilities.send_message import SendMessageCapability
from core.capabilities.read_sheet_range import ReadSheetRangeCapability
from core.capabilities.llm_chat import LlmChatCapability
from core.capabilities.get_contact import GetContactCapability
from core.capabilities.get_password import GetPasswordCapability
from core.capabilities.unlock_pdf import UnlockPdfCapability
from core.capabilities.extract_data_pdf import ExtractDataPdfCapability

from agents.accounting_assistant.agent import AccountingAssistantAgent


class AccountingAssistantAgentFactory:
    @staticmethod
    def build(tenant_config, messages_table, contacts_table, process_engine, s3_client):

        history_service = MessagesDynamodbService(messages_table)
        message_service = MessagesWhatsappService(tenant_config=tenant_config)
        # message_service = MessagesPrintService(tenant_config=tenant_config)
        sheets_service = SheetsGoogleService(tenant_config=tenant_config)
        llm_service = LlmOpenaiService(tenant_config=tenant_config)
        contact_service = ContactsDynamodbService(contacts_table)
        pdf_service = PdfS3Service(tenant_config, s3_client)

        message_integration = MessagesIntegration(history_service, message_service)
        sheets_integration = SheetsIntegration(sheets_service)
        llm_integration = LlmIntegration(llm_service)
        contact_integration = ContactsIntegration(contact_service)
        pdf_integration = PdfIntegration(pdf_service)

        read_messages_capability = ReadMessagesCapability(message_integration)
        send_message_capability = SendMessageCapability(message_integration)
        read_sheet_range_capability = ReadSheetRangeCapability(sheets_integration)
        llm_chat_capability = LlmChatCapability(llm_integration)
        get_contact_capability = GetContactCapability(contact_integration)
        get_password_capability = GetPasswordCapability(contact_integration)
        unlock_pdf_capability = UnlockPdfCapability(pdf_integration)
        extract_data_pdf_capability = ExtractDataPdfCapability(pdf_integration)

        capabilities = {
            "read_messages": read_messages_capability,
            "send_message": send_message_capability,
            "read_sheet_range": read_sheet_range_capability,
            "llm_chat": llm_chat_capability,
            "get_contact": get_contact_capability,
            "get_password": get_password_capability,
            "unlock_pdf": unlock_pdf_capability,
            "extract_data_pdf": extract_data_pdf_capability,
        }

        agent = AccountingAssistantAgent(
            capabilities=capabilities,
            process_engine=process_engine,
        )

        return agent