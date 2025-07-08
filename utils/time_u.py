from datetime import datetime


def get_current_time_formatted():
    now = datetime.now()
    day = str(int(now.strftime("%d")))
    month = str(int(now.strftime("%m")))
    year = now.strftime("%y")
    hour = str(int(now.strftime("%H")))
    minute = now.strftime("%M")
    return f"{day}-{month}-{year} {hour}:{minute}"


def parse_custom_datetime(date_str):
    return datetime.strptime(date_str, "%d-%m-%y %H:%M")