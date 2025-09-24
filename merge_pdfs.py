#!/usr/bin/env python3
import argparse, re, sys
from pathlib import Path
from pypdf import PdfReader, PdfWriter

def natural_key(s:str):  # file2 before file10
    return [int(t) if t.isdigit() else t.lower() for t in re.findall(r'\d+|\D+', s)]

def main():
    ap = argparse.ArgumentParser(description="Merge many PDFs in one folder.")
    ap.add_argument("folder", nargs="?", default=".", help="Folder containing PDFs (default: current)")
    ap.add_argument("-o", "--output", default="merged.pdf", help="Output file name (default: merged.pdf)")
    ap.add_argument("--pattern", default="*.pdf", help="Glob, e.g. 'Report*.pdf'")
    ap.add_argument("--skip-encrypted", action="store_true", help="Skip encrypted PDFs")
    args = ap.parse_args()

    folder = Path(args.folder).resolve()
    out = (folder / args.output).resolve()
    files = sorted(folder.glob(args.pattern), key=lambda p: natural_key(p.name))
    files = [f for f in files if f != out]  # don’t self-include

    if not files:
        print("No PDFs found.", file=sys.stderr)
        sys.exit(1)

    writer = PdfWriter()
    added = 0
    for f in files:
        try:
            r = PdfReader(str(f))
            if r.is_encrypted:
                if args.skip_encrypted:
                    print(f"Skipping encrypted: {f.name}")
                    continue
                else:
                    print(f"Encrypted: {f.name} (use --skip-encrypted to ignore)", file=sys.stderr)
                    sys.exit(2)
            for p in r.pages:
                writer.add_page(p)
            added += 1
        except Exception as e:
            print(f"Skipping {f.name}: {e}", file=sys.stderr)

    if added == 0:
        print("Nothing merged.", file=sys.stderr); sys.exit(3)
    with open(out, "wb") as fh:
        writer.write(fh)
    print(f"Merged {added} file(s) → {out}")

if __name__ == "__main__":
    main()