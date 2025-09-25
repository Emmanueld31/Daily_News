#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path
from typing import List
from pypdf import PdfReader, PdfWriter

def natural_key(s: str) -> list:
    """Sort helper: file2 before file10."""
    return [int(t) if t.isdigit() else t.lower() for t in re.findall(r"\d+|\D+", s)]

def gather_sources(folder: Path, pattern: str, out_base: Path) -> List[Path]:
    """
    Collect input PDFs matching pattern, exclude any previous outputs:
    - exact output name
    - '<stem> - Part N.pdf' from prior runs
    """
    files = sorted(folder.glob(pattern), key=lambda p: natural_key(p.name))

    # exclude the "single file" name (if present) and any chunked outputs from prior runs
    stem = out_base.stem
    excludes = {out_base}
    excludes |= set(folder.glob(f"{stem} - Part *.pdf"))

    files = [f for f in files if f.resolve() not in {e.resolve() for e in excludes}]
    return files

def write_chunk(writer: PdfWriter, out_base: Path, part_idx: int) -> Path:
    """
    Write current writer to '<stem> - Part {part_idx}.pdf' next to out_base.
    """
    stem = out_base.stem
    out_path = out_base.with_name(f"{stem} - Part {part_idx}.pdf")
    with out_path.open("wb") as fh:
        writer.write(fh)
    return out_path

def main():
    ap = argparse.ArgumentParser(description="Merge many PDFs in one folder, splitting into chunks by page count.")
    ap.add_argument("folder", nargs="?", default=".", help="Folder containing PDFs (default: current)")
    ap.add_argument("-o", "--output", default="merged.pdf",
                    help="Output base filename (default: merged.pdf). "
                         "Chunks will be '<stem> - Part N.pdf'.")
    ap.add_argument("--pattern", default="*.pdf", help="Glob, e.g. 'Report*.pdf' (default: *.pdf)")
    ap.add_argument("--skip-encrypted", action="store_true", help="Skip encrypted PDFs instead of aborting")
    ap.add_argument("--max-pages", type=int, default=1000, help="Max pages per output PDF (default: 1000)")
    args = ap.parse_args()

    folder = Path(args.folder).resolve()
    out_base = (folder / args.output).resolve()
    max_pages = max(1, int(args.max_pages))

    sources = gather_sources(folder, args.pattern, out_base)
    if not sources:
        print("No PDFs found.", file=sys.stderr)
        sys.exit(1)

    writer = PdfWriter()
    pages_in_writer = 0
    added_files = 0
    part_idx = 1
    written_paths: List[Path] = []

    for f in sources:
        try:
            r = PdfReader(str(f))
            if r.is_encrypted:
                if args.skip_encrypted:
                    print(f"Skipping encrypted: {f.name}")
                    continue
                else:
                    print(f"Encrypted: {f.name} (use --skip-encrypted to ignore)", file=sys.stderr)
                    sys.exit(2)

            # Append pages, flushing to a new chunk whenever we hit max_pages
            for page in r.pages:
                writer.add_page(page)
                pages_in_writer += 1
                if pages_in_writer >= max_pages:
                    out_path = write_chunk(writer, out_base, part_idx)
                    written_paths.append(out_path)
                    writer = PdfWriter()
                    pages_in_writer = 0
                    part_idx += 1

            added_files += 1

        except Exception as e:
            print(f"Skipping {f.name}: {e}", file=sys.stderr)

    # Flush remainder
    if pages_in_writer > 0:
        out_path = write_chunk(writer, out_base, part_idx)
        written_paths.append(out_path)

    if added_files == 0:
        print("Nothing merged.", file=sys.stderr)
        sys.exit(3)

    if not written_paths:
        print("No output written (unexpected).", file=sys.stderr)
        sys.exit(4)

    print(f"Merged {added_files} file(s) into {len(written_paths)} part(s):")
    for p in written_paths:
        print("  ", p)

if __name__ == "__main__":
    main()
