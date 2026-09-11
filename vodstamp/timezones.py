"""City-based timezones: the stream date determines daylight-saving time."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, available_timezones

def gmt(seconds):
    minutes = int(seconds // 60)
    return f"GMT{'+' if minutes >= 0 else '-'}{abs(minutes)//60:02d}:{abs(minutes)%60:02d}"

def choices(year=None):
    year = year or datetime.now().year
    entries = []
    for name in available_timezones():
        if name.split('/')[0] not in {'Africa', 'America', 'Antarctica', 'Asia', 'Atlantic', 'Australia', 'Europe', 'Indian', 'Pacific'}:
            continue
        zone = ZoneInfo(name)
        offsets = sorted({int(datetime(year, month, 15, tzinfo=timezone.utc).astimezone(zone).utcoffset().total_seconds()) for month in range(1, 13)})
        city = name.rsplit('/', 1)[-1].replace('_', ' ')
        label = f"{' / '.join(gmt(value) for value in offsets)} — {city} ({name})"
        entries.append((offsets[0], label, name))
    # Cover every whole-hour fixed offset, including uninhabited GMT-12.
    for hour in range(-12, 15):
        name = 'Etc/GMT' if hour == 0 else f"Etc/GMT{'-' if hour > 0 else '+'}{abs(hour)}"
        entries.append((hour*3600, f'{gmt(hour*3600)} — Fixed offset (no daylight saving)', name))
    return {label: name for _, label, name in sorted(entries)}

OPTIONS = choices()
DEFAULT = next(label for label, zone in OPTIONS.items() if zone == 'Europe/Rome')

def resolve(value):
    return ZoneInfo(OPTIONS.get(value, value))
