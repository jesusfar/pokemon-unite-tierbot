from datetime import date

from utils import spanish_date


def test_spanish_date_uses_numeric_day_month_year() -> None:
    assert spanish_date(date(2026, 6, 16)) == "16/06/2026"
