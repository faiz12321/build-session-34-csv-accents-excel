"""Create fictional UTF-8 practice CSV only in a new sample folder."""
from pathlib import Path

CSV = 'Item,City,Quantity\nCafé,Málaga,3\nCrème,Göteborg,7\nThé,København,1\nPiñata,Montréal,5\n'


def main():
    folder = Path(__file__).resolve().parent / 'sample'
    try:
        folder.mkdir()
    except FileExistsError:
        raise SystemExit('Stopped: sample already exists. Nothing was replaced or deleted.')
    with (folder / 'guests.csv').open('x', encoding='utf-8', newline='') as handle:
        handle.write(CSV)
    print('Created sample/guests.csv with 4 fictional UTF-8 records, without a BOM.')
    print('The historic filename guests.csv is kept, but the sample contains items, not people.')


if __name__ == '__main__':
    main()
