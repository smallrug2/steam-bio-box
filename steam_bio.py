"""ASCII-art bordered bio/profile box generator.

Builds a bordered header/footer box (box-drawing characters) plus plain
body lines, suitable for Steam or other profile bios with char limits.

Usage examples:
    python steam_bio.py --title "MY PROFILE" --title "v2026.10" --line "[ GAMES ]" --line "  RPGs, Simulators"
    python steam_bio.py --title "HELLO" --input bio_lines.txt --width 58 --output bio.txt
    type lines.txt | python steam_bio.py --title "TITLE" --width 60

Platform notes:
    Windows + Linux. Forces UTF-8 on stdout where possible so box
    characters render correctly on all consoles.

Dependencies:
    Standard library only (argparse, sys, pathlib).
"""

import argparse
import sys
from pathlib import Path

DEFAULT_WIDTH = 58


def ensure_utf8_stdout():
    """Best-effort UTF-8 reconfigure of stdout (Windows-safe)."""
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass  # fall back to default encoding


def fit(text, width):
    """Pad or truncate a single line to exactly `width` display chars."""
    # NOTE: len() counts code points, not East-Asian wide cells.
    if len(text) > width:
        return text[:width]
    return text + " " * (width - len(text))


def make_box(lines, width):
    """Wrap lines in a ╔═╗ / ║ ║ / ╚═╝ box of inner width `width`."""
    inner = width + 2  # one space of padding on each side
    top = "\u2554" + "\u2550" * inner + "\u2557"
    bottom = "\u255a" + "\u2550" * inner + "\u255d"
    out = [top]
    for line in lines:
        out.append("\u2551 " + fit(line, width) + " \u2551")
    out.append(bottom)
    return out


def read_input_lines(path, use_stdin):
    """Collect body lines from --input file and/or piped stdin."""
    lines = []
    if path:
        lines.extend(Path(path).read_text(encoding="utf-8").splitlines())
    if use_stdin or (not path and not sys.stdin.isatty()):
        # Read piped stdin when requested or when data is piped in.
        data = sys.stdin.read()
        if data:
            lines.extend(data.splitlines())
    return lines


def build_parser():
    p = argparse.ArgumentParser(description="Generate a bordered ASCII-art bio box.")
    p.add_argument("--title", action="append", default=[],
                   help="Title line for the top box (repeatable).")
    p.add_argument("--status", action="append", default=[],
                   help="Status line for the bottom box (repeatable).")
    p.add_argument("--line", action="append", default=[],
                   help="Body/content line (repeatable).")
    p.add_argument("--input", default=None,
                   help="Text file with extra body lines (one per line).")
    p.add_argument("--stdin", action="store_true",
                   help="Also read body lines from stdin.")
    p.add_argument("--width", type=int, default=DEFAULT_WIDTH,
                   help="Inner text width (default: %(default)s).")
    p.add_argument("--output", default=None,
                   help="Write result to this file (UTF-8). Default: stdout only.")
    return p


def main(argv=None):
    ensure_utf8_stdout()
    args = build_parser().parse_args(argv)

    if args.width < 10 or args.width > 200:
        print("error: --width must be between 10 and 200", file=sys.stderr)
        return 2

    body = list(args.line)
    body.extend(read_input_lines(args.input, args.stdin))

    titles = args.title if args.title else ["TITLE"]
    out_lines = []
    out_lines += make_box(titles, args.width)
    out_lines.append("")
    out_lines += body
    if body and body[-1] != "":
        out_lines.append("")
    if args.status:
        out_lines += make_box(args.status, args.width)

    bio = "\n".join(out_lines)

    # Sanity checks: box rows share one width; body rows fit inside it.
    box_widths = {len(x) for x in out_lines if x and x[0] in "\u2554\u2551\u255a"}
    content_widths = [len(x) for x in out_lines if x and x[0] not in "\u2554\u2551\u255a"]
    if len(box_widths) != 1:
        print("warning: box misaligned: %s" % sorted(box_widths), file=sys.stderr)
    if content_widths and max(content_widths) > max(box_widths or [0]):
        print("warning: a body line exceeds the box width", file=sys.stderr)

    print("chars: %d" % len(bio))
    print()
    print(bio)

    if args.output:
        Path(args.output).write_text(bio, encoding="utf-8")
        print("\nsaved to: %s" % args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
