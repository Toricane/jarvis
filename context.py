from datetime import datetime

context = {
    "location": "Vancouver, BC, Canada",
    "date": datetime.now().strftime("%Y-%m-%d"),
    "time": datetime.now().strftime("%H:%M"),
}


def get_context():
    global context
    context["date"] = datetime.now().strftime("%Y-%m-%d")
    context["time"] = datetime.now().strftime("%H:%M")
    string: str = ""
    for key, value in context.items():
        string += f"{key.capitalize()}: {value}\n"
    return string[:-1]
