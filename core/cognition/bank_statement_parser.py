import re
from typing import List, Dict, Optional, Any


class BankStatementParser:

    def detect_bank(self, text: str) -> str:

        if "BBVA MEXICO, S.A., INSTITUCION DE BANCA MULTIPLE, GRUPO FINANCIERO BBVA MEXICO" in text:
            return "BBVA"

        return "UNKNOWN"

    def parse(self, text: str) -> Dict[str, Any]:
        bank = self.detect_bank(text)

        if bank == "BBVA":
            movements = self._parse_bbva(text)
        else:
            movements = []

        return {
            "bank": bank,
            "movements": movements
        }

    def _parse_bbva(self, full_text: str) -> List[Dict[str, Optional[str]]]:

        start = r"Detalle de Movimientos Realizados"
        end = r"Total de Movimientos"

        block_re = re.compile(
            rf"{start}(.*?){end}",
            re.DOTALL | re.IGNORECASE
        )

        match = block_re.search(full_text or "")
        if not match:
            raise ValueError("MOVEMENTS_BLOCK_NOT_FOUND")

        movimientos_text = match.group(1).strip()

        months = "ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC"

        header_re = re.compile(
            rf"^\s*(\d{{2}}/(?:{months}))\s+(\d{{2}}/(?:{months}))\s+(.+?)\s+"
            r"([-]?\d{1,3}(?:,\d{3})*\.\d{2})\s+"
            r"(\d{1,3}(?:,\d{3})*\.\d{2})"
            r"(?:\s+(\d{1,3}(?:,\d{3})*\.\d{2}))?\s*$"
        )

        lines = movimientos_text.splitlines()

        movements: List[Dict[str, Optional[str]]] = []
        current: Optional[Dict[str, Optional[str]]] = None
        detail_lines: List[str] = []

        for line in lines:
            m = header_re.match(line)
            if m:
                if current is not None:
                    current["details"] = "\n".join(detail_lines).strip()
                    movements.append(current)

                current = {
                    "date_op": m.group(1),
                    "date_val": m.group(2),
                    "concept": m.group(3).strip(),
                    "amount": m.group(4),
                    "balance": m.group(5),
                    "balance2": m.group(6),
                    "details": "",
                }
                detail_lines = []
            else:
                if current is not None:
                    detail_lines.append(line.rstrip())

        if current is not None:
            current["details"] = "\n".join(detail_lines).strip()
            movements.append(current)

        return movements