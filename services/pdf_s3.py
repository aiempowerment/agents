from pathlib import Path
import tempfile
import pikepdf
from pypdf import PdfReader


class PdfS3Service:

    def __init__(self, tenant_config, s3_client):
        s3_config = tenant_config.get("s3", {})
        self.bucket = s3_config.get("bucket")
        self.s3 = s3_client

    def _is_encrypted(self, pdf_path: Path) -> bool:
        try:
            with pikepdf.open(pdf_path):
                return False
        except pikepdf.PasswordError:
            return True

    def unlock_pdf(self, key: str, password: str) -> str:
        p = Path(key)
        output_key = str(p.with_name(f"{p.stem}{p.suffix}"))

        with tempfile.TemporaryDirectory() as tmpdir:
            local_in = Path(tmpdir) / "input.pdf"
            local_out = Path(tmpdir) / "output.pdf"

            self.s3.download_file(self.bucket, key, str(local_in))

            try:
                with pikepdf.open(local_in, password=password) as pdf:
                    pdf.save(local_out)
            except pikepdf.PasswordError:
                raise ValueError("WRONG_PASSWORD")

            self.s3.upload_file(
                str(local_out),
                self.bucket,
                output_key,
                ExtraArgs={"ContentType": "application/pdf"},
            )

        return output_key

    def extract_data(
        self,
        key: str,
        layout: bool = True,
        x_tolerance: int = 2,
        y_tolerance: int = 2,
        keep_blank_chars: bool = True,
    ) -> str:

        all_text: list[str] = []

        with tempfile.TemporaryDirectory() as tmpdir:
            local_pdf = Path(tmpdir) / "input.pdf"
            self.s3.download_file(self.bucket, key, str(local_pdf))

            try:
                reader = PdfReader(str(local_pdf))

                for page in reader.pages:
                    text = page.extract_text() or ""

                    if keep_blank_chars:
                        all_text.append(text)
                    else:
                        all_text.append("\n".join(line for line in text.splitlines() if line.strip()))

            except Exception:
                if self._is_encrypted(local_pdf):
                    raise ValueError("PDF_PROTECTED")
                raise

        return "\n".join(all_text)