class ExtractDataPdfCapability:
    def __init__(self, pdf_integration):
        self.pdf_integration = pdf_integration

    def __call__(self, pdf_path: str) -> str:
        return self.pdf_integration.extract_data_pdf(pdf_path)