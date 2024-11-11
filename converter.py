"""
Function to convert the old log txt files to sql files
"""

from datetime import datetime
from pathlib import Path
import traceback


def convert_to_sql(file):
    if isinstance(file, str):
        file = Path(file)

    with open(file, "r") as f:
        lines = f.readlines()

    sql_file = file.with_suffix(".sql")
    new_lines = []
    for i, line in enumerate(lines):
        try:
            indatetime, exdatetime = line[1:17], line[20:36]
            in_timestamp = int(
                datetime.strptime(indatetime, "%d/%m/%Y %H:%M").timestamp()
            )
            ex_timestamp = int(
                datetime.strptime(exdatetime, "%d/%m/%Y %H:%M").timestamp()
            )
            user, task = line[47:-1].split("> :: ", 1)
            new_lines.append(
                f"INSERT INTO audit (userId, startTime, endTime, motivation, approved, location) VALUES ('{user}', {in_timestamp}, {ex_timestamp}, '{task}', true, 'lab');\n"
            )
        except ValueError:
            print(f"Error in {file} at line {i}: {line}")
            print(traceback.format_exc(0))
            break
    else:
        with open(sql_file, "w") as f:
            f.writelines(new_lines)


if __name__ == "__main__":
    for file in Path(".").glob("log*.txt"):
        convert_to_sql(file)
