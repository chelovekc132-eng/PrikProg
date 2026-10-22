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
    if not m:
        return BAD
    return "М" if m.group(1) else "Ж"


def fix_date(s):
    m = DATE_RE.fullmatch(s)
    if not m:
        return BAD
    day, month, year = int(m.group(1)), int(m.group(3)), int(m.group(4))
    today = date.today()
    if not 1900 <= year <= today.year:
        return BAD
    try:
        d = date(year, month, day)
    except ValueError:
        return BAD
    if d > today:
        return BAD
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


def clean_field(line):
    if ':' in line:
        return line.split(':', 1)[1].strip()
    return line.strip()


def read_records(text):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return [], False

    if len(re.split(r'\s*[,;]\s*', lines[0])) == 6:
        return [re.split(r'\s*[,;]\s*', ln) for ln in lines], True

    blocks = re.split(r'^\s*\d+\)\s*$', text, flags=re.MULTILINE)

    records = []
    for block in blocks:
        fields = []
        for ln in block.splitlines():
            ln = ln.strip()
            if ln:
                fields.append(clean_field(ln))
        if fields:
            records.append(fields)

    if len(records) == 1 and len(records[0]) > 6:
        flat = records[0]
        records = [flat[i:i + 6] for i in range(0, len(flat), 6)]

    return records, False


def main():
    parser = argparse.ArgumentParser(description="Приведение анкет к единому шаблону")
    parser.add_argument("filename", type=str, help="входной файл, например data.txt")
    parser.add_argument("-o", "--output", type=str, help="куда сохранить результат")
    args = parser.parse_args()

    out_name = args.output if args.output is not None else "result.txt"

    try:
        with open(args.filename, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Файл {args.filename} не найден")
        return

    records, one_line = read_records(text)

    result = []
    for rec in records:
        rec = rec + [BAD] * (6 - len(rec))
        fixed = [fix(field) for fix, field in zip(FIXERS, rec)]
        if one_line:
            result.append(", ".join(fixed))
        else:
            result.append("\n".join(fixed))

    sep = "\n" if one_line else "\n\n"
    with open(out_name, "w", encoding="utf-8") as f:
        f.write(sep.join(result) + "\n")

    print(f"Обработано анкет: {len(result)}. Результат в {out_name}")


if __name__ == "__main__":
    main()
