"""
Function to convert the old log txt files to sql files
"""
from pathlib import Path
from datetime import datetime

def convert_to_sql(file):
    if isinstance(file, str):
        file = Path(file)

    with open(file, 'r') as f:
        lines = f.readlines()
    sql_file = file.with_suffix('.sql')

    with open(sql_file, 'w') as f:
        for line in lines:
            indatetime, exdatetime = line[1:17], line[20:36]
            in_timestamp = int(datetime.strptime(indatetime, '%d/%m/%Y %H:%M').timestamp())
            ex_timestamp = int(datetime.strptime(exdatetime, '%d/%m/%Y %H:%M').timestamp())
            user, task = line[47:-1].split('> :: ', 1)
            f.write(f"INSERT INTO audit (userId, startTime, endTime, motivation, approved, location) VALUES ('{user}', {in_timestamp}, {ex_timestamp}, '{task}', true, 'lab');\n")
    return sql_file

if __name__ == '__main__':
    for file in Path('.').glob('*.txt'):
        convert_to_sql(file)
