# UTF-8 bytes and a marked copy for Excel import

Small Python teaching tool. It validates UTF-8, with or without a byte-order
mark (BOM), detects the mark and prints one example line plus a labeled
Windows-1252 misreading simulation. It does not run Excel, parse CSV, detect
the actual encoding of other files or certify formula/content safety.

## Practise

Save make_sample.py, excelbom.py and test_excelbom.py in a new empty folder.
Python 3 and its standard library are enough. Substitute python3 if needed:

    python make_sample.py
    python excelbom.py sample/guests.csv
    python excelbom.py sample/guests.csv --fix
    python excelbom.py sample/guests.bom.csv
    python -m unittest -v

Setup creates a new sample folder beside its script and refuses any existing
sample path. The historical filename guests.csv contains four fictional item
records, not people. Use a different empty lesson folder if setup refuses.

Inspection only reads the source. --fix adds EF BB BF to a new .bom.csv copy
only for unmarked valid UTF-8. Invalid UTF-8 is refused even when a mark exists.
An already marked input gets no copy. Exclusive creation refuses existing
output files, directories and links. Other write errors may leave an incomplete
new copy: inspect it before retrying. Keep originals and check the import result.
Source file paths may follow links. Reports print example text: avoid private
input or sharing sensitive output. The whole source is loaded into memory.

## Evidence and limits

15 tests run in temporary fixtures. Checks cover UTF-8 validity, marks, exact
copy bytes, source bytes/mtime and directory preservation, existing output
file/directory refusal, CLI errors and setup repeat-run preservation. These
are limited fixtures, not proof across every filesystem or concurrent change.

Two GitHub-hosted Windows and two Ubuntu recordings pass all tests. Each
platform's paired outputs differ only in unittest time. Displays use the first
Windows recording with UTF-8 output enabled. No Excel application, Windows
desktop or macOS session was recorded. Repeated setup and output commands
intentionally stop with exit 1. The recorder uses only a unique temporary folder.

Microsoft documents normal opening for marked UTF-8 CSV and text/CSV import
routes for unmarked files:
https://support.microsoft.com/en-us/office/opening-csv-utf-8-files-correctly-in-excel-8a935af5-3416-4edd-ba7e-3dfd2bc4a032

The simulation is not a prediction of every version, setting or import route.
Valid UTF-8 does not mean structurally valid CSV, safe formulas or correct data.

## License

MIT (see LICENSE).
