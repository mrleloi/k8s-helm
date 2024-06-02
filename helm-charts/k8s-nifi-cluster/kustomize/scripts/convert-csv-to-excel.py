import sys
import pandas as pd
from io import StringIO

def convert_csv_to_excel():
    # Read CSV data from stdin
    input_csv = sys.stdin.read()
    data = pd.read_csv(StringIO(input_csv))
    
    # Convert data to Excel and write directly to stdout.buffer using a context manager
    with pd.ExcelWriter(sys.stdout.buffer, engine='openpyxl') as writer:
        data.to_excel(writer, index=False, sheet_name='Sheet1')

if __name__ == "__main__":
    convert_csv_to_excel()
