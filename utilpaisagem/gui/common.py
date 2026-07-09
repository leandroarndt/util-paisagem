from datetime import datetime
from babel.dates import LOCALTZ, format_datetime

def format_status(text:str, obj) -> str:
    return f'{format_datetime(datetime.now(), format='short')} ({obj.__class__.__name__}): {text}'