import csv
import os
from scheduler import scheduler
# Expected Main Data Fields
# Title | Brand | Price | Model | Year | Engine Size |

"""
unique_cols = []
    for d in data_main:
        for col in d.keys():
            if col not in unique_cols:
                unique_cols.append(col)

    for d in data_main:
        for col in unique_cols:
            if not d.get(col):
                d[col] = ''
"""

def row_gen():
    unique_cols = []
    for csv_file in os.listdir('csv_files'):
        with open(f'csv_files\\{csv_file}', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for data_row in reader:
                for col in data_row.keys():
                    if col not in unique_cols:
                        unique_cols.append(col)
    for csv_file in os.listdir('csv_files'):
        with open(f'csv_files\\{csv_file}', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for data_row in reader:
                for col in unique_cols:
                    if not data_row.get(col):
                        data_row[col] = ''
                yield data_row

def print_summary():
    for csv_file in os.listdir('csv_files'):
        with open(f'csv_files\\{csv_file}', encoding='utf-8') as f:
            #num_rows = len(f.readlines()) - 1
            num_rows = len(list(csv.DictReader(f)))
        print(csv_file.replace('.csv', '').ljust(25, '-'), str(num_rows).rjust(5, ' '))
          

def main():
    print_summary()
    with open('isle-of-man-cars.csv', 'w', encoding='utf-8', newline='') as f:
        rgen = row_gen()
        d = next(rgen)
        cols = list(d.keys())
        p_idx = cols.index('Provider')
        if p_idx < len(cols) - 1:
            cols = [cols[p_idx]] + cols[:p_idx] + cols[p_idx + 1:]
        else:
            cols = [cols[p_idx]] + cols[:p_idx]
        image_cols = {}
        new_cols = []
        for col in cols:
            if 'Image' in col:
                image_cols[int(col.replace('Image ', ''))] = col
            else:
                new_cols.append(col)
        for i in range(len(image_cols)):
            new_cols.append(image_cols[i+1])
        cols = new_cols
        writer = csv.writer(f)
        writer.writerow(cols)
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writerow(d)
        for d in rgen:
            writer.writerow(d)


if __name__ == "__main__":
    main()
