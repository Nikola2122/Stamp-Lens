from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from report.models import StampReport


@dataclass
class ReportServiceResultDTO:
    message: str
    stamp_report: "StampReport"
