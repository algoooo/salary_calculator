from dataclasses import dataclass
from datetime import datetime
from math import isclose
import re

place_attr = ["место", "точка", "кофейня", "где"]
date_attr = ["дата", "когда", "день"]
name_attr = ["фио", "имя", "кто", "работник"]
time_attr = ["время", "со скольки"]
money_attr = {
    "cash": ["нал", "наличные"],
    "card": ["карта", "безнал", "безналичные"],
    "total": ["сумма", "общая", "всего"],
    "transfer": ["перевод", "перевод на карту"],
    "shortage": ["недостача", "недочет"],
    "encashment": ["инкассация", "инкасация"],
    "remains": ["остаток", "остаток в кассе", "в кассе", "касса"]
}
comment_attr = ["коммент", "комментарий", "заметка", "также"]
field_names = {
    *place_attr, *date_attr, *name_attr, *time_attr, *comment_attr,
    *(keyword for keywords in money_attr.values() for keyword in keywords),
}
money_pattern = re.compile(
    r"(?<!\S)(?:[0-9]{1,3}(?: [0-9]{3})+|[0-9]+)(?:[.,][0-9]+)?[рР₽]?(?!\S)"
)


class TotalErrorException(Exception):
    pass

@dataclass
class ParsedDay:

    def __str__(self):
        return (f"{self.date.strftime('%Y-%m-%d')} at {self.place_name} - {self.employee_name}: "
                f"{self.hours_formatted} in total: {self.hours} hours, "
                f"profit: {self.total_profit}, cash: {self.total_by_cash}, "
                f"transfer: {self.total_by_transfer}, card: {self.total_by_card}, "
                f"shortage: {self.shortage}, remains: {self.remains}")

    employee_name: str = "ERROR"
    hours_formatted: str = "ERROR"
    hours: int = 0
    date: datetime = datetime.now()
    place_name: str = "ERROR"

    total_profit: int | float = -1000
    total_by_card: int | float = -1000
    total_by_cash: int | float = -1000
    total_by_transfer: int | float = -1000
    shortage: int | float = -1000
    remains: int | float = -1000


def parse_message(message_text) -> ParsedDay:

    lines = message_text.split("\n")
    day = ParsedDay()
    for line in lines:
        parts = line.split()
        if not parts:
            continue

        label, separator, remainder = line.partition(":")
        arg = " ".join(label.lower().split())
        if separator and arg in field_names:
            values = remainder.split()
        else:
            arg, *values = parts
            arg = arg.lower().rstrip(":")
        day = _parse_line(day, arg, values)

    check_sum(day)
    return day


def check_sum(obj: ParsedDay):
    total = obj.total_profit

    total_claim = obj.total_by_cash + obj.total_by_card + obj.total_by_transfer

    if not isclose(total, total_claim, rel_tol=0, abs_tol=1e-9):
        raise TotalErrorException(f"Total does not match with claimed total. Total: {total}, Claimed: {total_claim}")


def _parse_line(obj: ParsedDay, arg: str, values: list[str]) -> ParsedDay:

    if arg in place_attr:
        obj.place_name = " ".join(values)

    if arg in date_attr:
        _parse_date(obj, values)

    if arg in name_attr:
        obj.employee_name = " ".join(values)

    if arg in time_attr:
        _parse_hours(obj, values)

    if arg in comment_attr:
        pass

    for category, keywords in money_attr.items():
        if arg in keywords:
            _parse_money(obj, category, values)
        else:
            continue
    return obj



def _parse_hours(obj: ParsedDay, values: list[str]) -> ParsedDay:
    """e.g. 10:00-18:00 or 10:00-11:00, 11:00-18:00 or 9-00-10-00"""


    hrs_formatted = " ".join(values)
    if hrs_formatted[-1] == ",":
        hrs_formatted = hrs_formatted[:-1]

    obj.hours_formatted = hrs_formatted


    args = "".join(values).replace(".", ":").split(",")

    for entry in args:
        times = entry.strip().split("-")
        if len(times) != 2:
            raise Exception("Time args is wrong (e.g. 10:00-11:00-12:00)")

        if ":" not in times[0] or ":" not in times[1]:
            raise Exception("Time delimiter is not :")

        t1 = datetime.strptime(times[0].replace(",", ""), "%H:%M")
        t2 = datetime.strptime(times[1].replace(",", ""), "%H:%M")

        hours: int = int((t2-t1).total_seconds() / 3600)

        obj.hours += hours

    return obj


def _parse_date(obj: ParsedDay, values: list) -> ParsedDay:
    if len(values) == 3:
        d, m, y = values[0], values[1], values[2]
        d, m, y = int(d), int(m), int(y)
    elif len(values) == 1:
        value: str = values[0]
        d, m, y = map(int, re.split(r"[./-]", value))
    else:
        raise Exception("Wrong date format given")

    if y < 100:
        y = int("20" + str(y))
    result_date = datetime(year=y, month=m, day=d)

    obj.date = result_date
    return obj

def _parse_money(obj: ParsedDay, category: str, values: list[str]) -> ParsedDay:
    amounts = money_pattern.findall(" ".join(values))
    if amounts:
        cash_arg = float(amounts[-1].rstrip("рР₽").replace(" ", "").replace(",", "."))
    elif not values or values in (["-"], ["–"], ["—"]):
        cash_arg = 0.0
    else:
        raise ValueError(f"Invalid amount for {category}")

    match category:
        case "cash":
            obj.total_by_cash = float(cash_arg)
        case "card":
            obj.total_by_card = float(cash_arg)
        case "total":
            obj.total_profit = float(cash_arg)
        case "transfer":
            obj.total_by_transfer = float(cash_arg)
        case "shortage":
            obj.shortage = float(cash_arg)
        case "encashment":
            obj.encashment = float(cash_arg)
        case "remains":
            obj.remains = float(cash_arg)
        case _:
            raise Exception("Wrong money category given")
    return obj


def test_working() -> None:
    text = """
 Дата: 19.11.26 
Точка: In Joy 
ФИО: Саша 
Время: 9:00-14:00, 15:00-18:00 
Нал: 12
Безнал: 5042 
Перевод: 332
Общая: 5386
Недостача: 80
Изъятие: 500
Остаток в кассе: 50"""
    parsed = parse_message(text)
    print(parsed)
