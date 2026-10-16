"""Inspect UTF-8 bytes and optionally add a BOM to a new copy.

This is not a CSV validator or a prediction of Excel's import settings.
"""
from pathlib import Path
import sys
import stat


def safe_input(value, directory=False):
    path = Path(value).absolute()
    if '..' in path.parts:
        raise OSError('Parent-traversal paths are unsupported.')
    for part in [*reversed(path.parents), path]:
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise OSError('Links/reparse points are unsupported.')
    info = path.lstat()
    if directory:
        if not stat.S_ISDIR(info.st_mode):
            raise NotADirectoryError('Expected an ordinary directory.')
    elif not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise OSError('Expected an ordinary singly linked file.')
    return path

def safe_output(value):
    path = Path(value).absolute()
    if '..' in path.parts:
        raise OSError('Parent-traversal paths are unsupported.')
    safe_input(path.parent, directory=True)
    return path



BOM = b'\xef\xbb\xbf'


def inspect(raw):
    marked = raw.startswith(BOM)
    body = raw[len(BOM):] if marked else raw
    text = body.decode('utf-8')  # Validate even when a BOM is present.
    example = next((line for line in text.splitlines()
                    if any(ord(char) > 127 for char in line)), '')
    misread = example.encode('utf-8').decode('cp1252', errors='replace')
    return marked, example, misread


def main(argv):
    if len(argv) not in (2, 3) or (len(argv) == 3 and argv[2] != '--fix'):
        print('Usage: python excelbom.py FILE [--fix]', file=sys.stderr)
        return 2
    if argv[1] in ('-h', '--help'):
        print('Usage: python excelbom.py FILE [--fix]')
        return 0
    path = Path(argv[1])
    try:
        raw = safe_input(path).read_bytes()
        marked, example, misread = inspect(raw)
    except OSError as error:
        print('Cannot read file: %s (%s)' % (path, (error.strerror or str(error))), file=sys.stderr)
        return 2
    except UnicodeDecodeError:
        print('Result: not valid UTF-8, even if a BOM is present.')
        print('No copy written. Identify the actual encoding before converting.')
        return 1
    print('UTF-8 byte check')
    print('File: ' + str(path))
    print('Result: valid UTF-8 %s a byte-order mark.' % ('WITH' if marked else 'WITHOUT'))
    if example:
        print('UTF-8 example: ' + example)
        print('Same bytes decoded as Windows-1252 (simulation): ' + misread)
    print('This does not verify CSV structure or predict every Excel import path.')
    if len(argv) == 2:
        print('No files written. --fix can add a BOM to a new copy of unmarked UTF-8.')
        return 0
    if marked:
        print('Already marked. No copy written.')
        return 0
    target = path.with_suffix('.bom.csv')
    try:
        with safe_output(target).open('xb') as handle:  # Never replace an existing path or link.
            handle.write(BOM + raw)
    except FileExistsError:
        print('Stopped: output already exists: ' + str(target), file=sys.stderr)
        print('No existing output was replaced.', file=sys.stderr)
        return 1
    except OSError as error:
        print('Could not write new copy: %s (%s)' % (target, (error.strerror or str(error))), file=sys.stderr)
        print('Inspect that path for an incomplete new file before trying again.', file=sys.stderr)
        return 2
    print('Wrote new marked copy: ' + str(target))
    print('Original bytes unchanged. Check the import result before using or sharing it.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
