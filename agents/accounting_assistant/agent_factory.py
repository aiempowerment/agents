from services.messages_dynamodb import MessagesDynamodbService
from services.messages_whatsapp import MessagesWhatsappService
from services.llm_openai import LlmOpenaiService
from services.contacts_dynamodb import ContactsDynamodbService
from services.pdf_s3 import PdfS3Service
from services.files_s3 import FilesS3Service
from services.processes_dynamodb import ProcessesDynamodbService
from services.channel_slack import ChannelSlackService
from services.memory_dynamodb import MemoryDynamodbService

from integrations.messages import MessagesIntegration
from integrations.llm import LlmIntegration
from integrations.contacts import ContactsIntegration
from integrations.pdf import PdfIntegration
from integrations.files import FilesIntegration
from integrations.processes import ProcessesIntegration
from integrations.channel import ChannelIntegration
from integrations.memory import MemoryIntegration

from core.capabilities.read_messages import ReadMessagesCapability
from core.capabilities.send_message import SendMessageCapability
from core.capabilities.llm_chat import LlmChatCapability
from core.capabilities.get_contact import GetContactCapability
from core.capabilities.get_password import GetPasswordCapability
from core.capabilities.unlock_pdf import UnlockPdfCapability
from core.capabilities.extract_data_pdf import ExtractDataPdfCapability
from core.capabilities.set_password import SetPasswordCapability
from core.capabilities.list_files import ListFilesCapability
from core.capabilities.get_process_state import GetProcessStateCapability
from core.capabilities.send_message_channel import SendMessageChannelCapability
from core.capabilities.get_memory_state import GetMemoryStateCapability
from core.capabilities.update_memory_state import UpdateMemoryStateCapability

from agents.accounting_assistant.agent import AccountingAssistantAgent


class AccountingAssistantAgentFactory:
    @staticmethod
    def build(tenant_config, messages_table, contacts_table, processes_table, memory_table, process_engine, s3_client):

        history_service = MessagesDynamodbService(messages_table)
        message_service = MessagesWhatsappService(tenant_config=tenant_config)
        llm_service = LlmOpenaiService(tenant_config=tenant_config)
        contact_service = ContactsDynamodbService(contacts_table)
        pdf_service = PdfS3Service(tenant_config, s3_client)
        files_service = FilesS3Service(tenant_config, s3_client)
        processes_service = ProcessesDynamodbService(processes_table)
        channel_service = ChannelSlackService(tenant_config)
        memory_service = MemoryDynamodbService(memory_table)

        message_integration = MessagesIntegration(history_service, message_service)
        llm_integration = LlmIntegration(llm_service)
        contact_integration = ContactsIntegration(contact_service)
        pdf_integration = PdfIntegration(pdf_service)
        files_integration = FilesIntegration(files_service)
        processes_integration = ProcessesIntegration(processes_service)
        channel_integration = ChannelIntegration(channel_service)
        memory_integration = MemoryIntegration(memory_service)

        read_messages_capability = ReadMessagesCapability(message_integration)
        send_message_capability = SendMessageCapability(message_integration)
        llm_chat_capability = LlmChatCapability(llm_integration)
        get_contact_capability = GetContactCapability(contact_integration)
        get_password_capability = GetPasswordCapability(contact_integration)
        unlock_pdf_capability = UnlockPdfCapability(pdf_integration)
        extract_data_pdf_capability = ExtractDataPdfCapability(pdf_integration)
        set_password_capability = SetPasswordCapability(contact_integration)
        list_files_capability = ListFilesCapability(files_integration)
        get_processes_state_capability = GetProcessStateCapability(processes_integration)
        send_message_channel_capability = SendMessageChannelCapability(channel_integration)
        get_memory_state_capability = GetMemoryStateCapability(memory_integration)
        update_memory_state_capability = UpdateMemoryStateCapability(memory_integration)

        capabilities = {
            "read_messages": read_messages_capability,
            "send_message": send_message_capability,
            "llm_chat": llm_chat_capability,
            "get_contact": get_contact_capability,
            "get_password": get_password_capability,
            "unlock_pdf": unlock_pdf_capability,
            "extract_data_pdf": extract_data_pdf_capability,
            "set_password": set_password_capability,
            "list_files": list_files_capability,
            "get_processes_state": get_processes_state_capability,
            "send_message_channel": send_message_channel_capability,
            "get_memory_state": get_memory_state_capability,
            "update_memory_state": update_memory_state_capability,
        }

        agent = AccountingAssistantAgent(
            capabilities=capabilities,
            process_engine=process_engine,
        )

        return agent