# Inspect UTF-8 and add a BOM to a new copy

Save three source files in a NEW empty lesson folder.

    python make_sample.py
    python excelbom.py sample/guests.csv
    python excelbom.py sample/guests.csv --fix
    python -m unittest -v

Two Windows and two Ubuntu full replays run exact visible source versions. Final 32 small fixture tests pass (Unix pipe skips on Windows); symlink creation can skip where unavailable. Displayed stdout is first Windows output, not normalized or mixed. Pair differences are unittest time.
Only link/error changes: refuse input/ancestor symbolic links/reparse points, hardlinks, special files and traversal before reading. Output ancestors are checked before exclusive new-copy creation. Read/metadata/write errors remain exit 2; existing output and invalid UTF-8 remain exit 1. Setup refuses linked parents/traversal and existing sample paths, without reset/deletion.
Original UTF-8/BOM inspection and Windows-1252 misread simulation stay unchanged. --fix still writes exactly BOM plus original bytes only to a new .bom.csv path, only for unmarked valid UTF-8. No existing destination is replaced; marked input remains a no-write success. No CSV structure, formula safety or Excel import prediction was added.
Files are read into memory. No size/time/resource limit, atomic snapshot or hostile-race defense. Stop editors/sync. Output includes example lines which may be private. A write failure can leave a partial NEW file; it is not deleted. Inspect it and keep the original. Small fictional fixtures are not proof on every filesystem. No Excel/desktop Windows/macOS recording. Recorder removes only its own temporary fixture folder. Decisions/feedback are teaching text, not recorded output.

MIT code. Python separately licensed/not included.

Reference: https://docs.python.org/3/library/os.html

Windows paired run: https://github.com/faiz12321/lesson-lab/actions/runs/38977928180
Ubuntu paired run: https://github.com/faiz12321/lesson-lab/actions/runs/38977967661
