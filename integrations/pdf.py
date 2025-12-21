class PdfIntegration:
    def __init__(self, pdf_service):
        self.pdf_service = pdf_service

    def unlock_pdf(self, pdf_path: str, password: str) -> str:
        return self.pdf_service.unlock_pdf(pdf_path, password)

    def extract_data_pdf(self, pdf_path: str) -> bool:
        return self.pdf_service.extract_data(pdf_path)