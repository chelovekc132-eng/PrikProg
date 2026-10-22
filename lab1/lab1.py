import argparse
import re
from datetime import date

BAD = "-"

NAME_RE = re.compile(r'[А-ЯЁA-Z][а-яёa-z]*(?:-[А-ЯЁA-Z][а-яёa-z]*)?')
SEX_RE = re.compile(r'([Мм](?:ужской)?)|([Жж](?:енский)?)')
DATE_RE = re.compile(r'(\d{1,2})([/.-])(\d{1,2})\2(\d{4})')
PHONE_RE = re.compile(r'(?:8|\+7) ?(?:\(\d{3}\)|\d{3}) ?\d{3}[- ]?\d{2}[- ]?\d{2}')
EMAIL_RE = re.compile(r'[A-Za-z0-9._%+-]{1,64}@(?:gmail\.com|mail\.ru|yandex\.ru)')
CITY_RE = re.compile(r'(?:г\. ?)?([А-ЯЁ][а-яё]+(?:[- ][А-ЯЁ][а-яё]+)*)')

def fix_name(s):
    return s if NAME_RE.fullmatch(s) else BAD

def fix_sex(s):
    m = SEX_RE.fullmatch(s)
    if not m: return BAD
    return "М" if m.group(1) else "Ж"

def fix_date(s):
    m = DATE_RE.fullmatch(s)
    if not m: return BAD
    day, month, year = int(m.group(1)), int(m.group(3)), int(m.group(4))
    today = date.today()
    if not 1900 <= year <= today.year: return BAD
    try:
        d = date(year, month, day)
    except ValueError:
        return BAD
    if d > today: return BAD
    return f"{day:02d}.{month:02d}.{year}"

def fix_contact(s):
    if PHONE_RE.fullmatch(s):
        digits = re.sub(r'\D', '', s)
        digits = '8' + digits[1:]
        return f"8 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    if EMAIL_RE.fullmatch(s):
        return s
    return BAD

def fix_city(s):
    m = CITY_RE.fullmatch(s)
    return f"г. {m.group(1)}" if m else BAD

FIXERS = [fix_name, fix_name, fix_sex, fix_date, fix_contact, fix_city]

def clean_line(line):
    line = line.strip()
    if ':' in line:
        parts = line.split(':', 1)
        if parts[0].strip() in ["Фамилия", "Имя", "Пол", "Дата рождения", "Номер телефона или email", "Город"]:
            return parts[1].strip()
    return line

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str)
    args = parser.parse_args()

    with open(args.filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cleaned_lines = []
    for line in lines:
        if line.strip():
            cleaned_lines.append(clean_line(line))

    records = []
    current_record = []
    
    for line in cleaned_lines:
        if re.match(r'^\d+\)', line):
            if current_record:
                records.append(current_record)
            current_record = []
        else:
            current_record.append(line)
            
    if current_record:
        records.append(current_record)

    if not records or len(records[0]) != 6:
        records = [cleaned_lines[i:i + 6] for i in range(0, len(cleaned_lines), 6)]

    result = []
    for rec in records:
        rec = rec + [BAD] * (6 - len(rec))
        fixed = [fix(field) for fix, field in zip(FIXERS, rec)]
        result.append("\n".join(fixed))

    with open("result.txt", "w", encoding="utf-8") as f:
        f.write("\n\n".join(result) + "\n")

    print(f"Обработано анкет: {len(result)}. Результат в result.txt")

if __name__ == "__main__":
    main()
