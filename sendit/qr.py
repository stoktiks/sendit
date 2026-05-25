"""QR code display for terminal — Unicode half-block rendering."""

import sys


def print_qr(url):
    """Print a QR code for the URL in the terminal using Unicode half-blocks."""
    try:
        import qrcode
    except ImportError:
        print("  (install 'qrcode' for QR: pip install qrcode)")
        return

    qr = qrcode.QRCode(border=2, box_size=1)
    qr.add_data(url)
    qr.make(fit=True)
    matrix = qr.get_matrix()

    # Colors: cyan foreground
    F = "\033[36m"   # cyan
    R = "\033[0m"    # reset
    DIM = "\033[2m"  # dim for quiet zone

    rows = len(matrix)
    # Each output row covers 2 QR rows (top and bottom half of ▀/▄/█)
    out_rows = []

    for y in range(0, rows, 2):
        line_chars = []
        has_top = y < rows
        has_bot = (y + 1) < rows
        for x in range(rows):
            top = matrix[y][x] if has_top else False
            bot = matrix[y + 1][x] if has_bot else False
            if top and bot:
                line_chars.append("█")  # full block
            elif top and not bot:
                line_chars.append("▀")  # top half
            elif not top and bot:
                line_chars.append("▄")  # bottom half
            else:
                line_chars.append(" ")
        out_rows.append("".join(line_chars))

    # Remove empty leading/trailing rows for compactness
    # (quiet zone is already 2 chars thick from QRCode(border=2))
    label = "📱 Scan QR"
    # Print with a single ANSI color block
    sys.stdout.write("\n")
    for row in out_rows:
        sys.stdout.write(f"  {F}{row}{R}\n")
    sys.stdout.write(f"  {DIM}{label}{R}\n")
    sys.stdout.write("\n")
    sys.stdout.flush()
