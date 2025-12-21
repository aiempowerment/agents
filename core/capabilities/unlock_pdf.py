class UnlockPdfCapability:
    def __init__(self, pdf_integration):
        self.pdf_integration = pdf_integration

    def __call__(self, pdf_path: str, password: str) -> str:
        return self.pdf_integration.unlock_pdf(pdf_path, password)