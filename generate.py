#!/usr/bin/env python3
"""
Fontaku Font Generator
Generates a TrueType font with SBIX (bitmap emoji) tables from PNG images.
"""

import os
import glob
from pathlib import Path
from fontTools.fontBuilder import FontBuilder
from PIL import Image


def get_image_files(images_dir="images"):
    """Get all PNG files from the images directory and sort them by Unicode codepoint."""
    png_files = glob.glob(os.path.join(images_dir, "U+*.png"))
    # Sort by the hex value in the filename
    png_files.sort(key=lambda x: int(Path(x).stem.replace("U+", ""), 16))
    return png_files


def parse_codepoint(filename):
    """Extract Unicode codepoint from filename like 'U+E001.png'."""
    stem = Path(filename).stem
    hex_value = stem.replace("U+", "")
    return int(hex_value, 16)


def create_empty_glyph(glyphSet):
    """Create an empty glyph outline for use in the font."""
    from fontTools.ttLib.tables._g_l_y_f import Glyph

    glyph = Glyph()
    glyph.numberOfContours = 0
    glyph.xMin = glyph.yMin = glyph.xMax = glyph.yMax = 0
    return glyph


def read_png_data(png_path):
    """Read PNG file and return its binary data."""
    with open(png_path, "rb") as f:
        return f.read()


def get_image_size(png_path):
    """Get the dimensions of a PNG image."""
    with Image.open(png_path) as img:
        return img.size


def resize_image_to_ppem(png_path, ppem):
    """Resize a PNG image to the specified ppem size and return PNG data.
    Maintains aspect ratio and centers the image in a square canvas."""
    import io

    with Image.open(png_path) as img:
        # Get original dimensions
        orig_width, orig_height = img.size

        # Calculate the size maintaining aspect ratio
        # The image should fit within ppem x ppem
        scale = ppem / max(orig_width, orig_height)
        new_width = int(orig_width * scale)
        new_height = int(orig_height * scale)

        # Resize the image
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Create a square canvas and center the resized image
        canvas = Image.new("RGBA", (ppem, ppem), (0, 0, 0, 0))
        x_offset = (ppem - new_width) // 2
        y_offset = (ppem - new_height) // 2
        canvas.paste(
            resized, (x_offset, y_offset), resized if resized.mode == "RGBA" else None
        )

        # Save to bytes
        buffer = io.BytesIO()
        canvas.save(buffer, format="PNG")
        return buffer.getvalue()


def build_font(image_files, output_path="Fontaku.ttf"):
    """Build the TrueType font with SBIX tables.
    Maps images to standard emoji codepoints starting at U+1F600.

    Args:
        image_files: List of PNG image file paths
        output_path: Output font file path
    """

    if not image_files:
        raise ValueError("No image files found to process")

    print(f"Building font from {len(image_files)} images...")

    # Initialize font builder with EXACT Apple Color Emoji metrics
    # Apple uses 800 units per em (not 1000!)
    fb = FontBuilder(unitsPerEm=800, isTTF=True)

    # Build glyph list and cmap
    glyph_order = [".notdef"]
    cmap = {}

    # Standard emoji codepoints starting from U+1F600 (grinning face)
    emoji_codepoints_start = 0x1F600

    for i, img_file in enumerate(image_files):
        # Map to standard emoji codepoints
        codepoint = emoji_codepoints_start + i
        glyph_name = f"uni{codepoint:04X}"
        glyph_order.append(glyph_name)
        cmap[codepoint] = glyph_name
        print(f"  Mapping U+{codepoint:04X} to {glyph_name}")

    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)

    # Setup glyf table with empty outlines (for TrueType)
    # Even though we're using bitmaps, we need glyph outlines
    glyphs = {}
    for glyph_name in glyph_order:
        glyphs[glyph_name] = create_empty_glyph(None)

    fb.setupGlyf(glyphs)

    # Setup glyph metrics (must be before OS/2)
    # CRITICAL: Apple Color Emoji uses advance width equal to units per em (800)
    # This is what makes emoji properly centered!
    emoji_advance_width = 800

    metrics = {}
    for glyph_name in glyph_order:
        if glyph_name == ".notdef":
            metrics[glyph_name] = (500, 0)  # width, left side bearing
        else:
            # Advance width = units per em for proper centering
            metrics[glyph_name] = (emoji_advance_width, 0)

    fb.setupHorizontalMetrics(metrics)

    # Set basic font info
    import time

    timestamp = int(time.time())
    fb.setupHead(unitsPerEm=800, created=timestamp, modified=timestamp)

    # Use EXACT Apple Color Emoji metrics
    fb.setupHorizontalHeader(ascent=800, descent=-250)

    # OS/2 table (must be after hmtx)
    # CRITICAL: Apple sets usWinAscent and usWinDescent to 0!
    # This is key for proper centering
    fb.setupOS2(
        sTypoAscender=750,
        sTypoDescender=-250,
        usWinAscent=0,
        usWinDescent=0,
        sxHeight=500,
        sCapHeight=800,
    )

    # Name table - font metadata
    fb.setupNameTable(
        {
            "familyName": "Fontaku",
            "styleName": "Regular",
            "uniqueFontIdentifier": "Fontaku-Regular",
            "fullName": "Fontaku Regular",
            "version": "Version 1.0",
            "psName": "Fontaku-Regular",
        }
    )

    # Post table
    fb.setupPost()

    # Create the font object to manually add SBIX table
    font = fb.font

    # Setup SBIX table with bitmap data manually
    from fontTools.ttLib import newTable
    from fontTools.ttLib.tables import sbixStrike, sbixGlyph

    sbix = newTable("sbix")
    sbix.version = 1
    sbix.flags = 1
    sbix.strikes = {}

    # Define multiple strike sizes for different display resolutions
    strike_sizes = [32, 64, 128, 256]

    print("\n  Creating SBIX strikes...")
    for ppem in strike_sizes:
        print(f"    Strike {ppem} ppem")
        strike = sbixStrike.Strike()
        strike.ppem = ppem
        strike.resolution = 72
        strike.glyphs = {}

        # Add empty .notdef glyph
        notdef_glyph = sbixGlyph.Glyph()
        notdef_glyph.glyphName = ".notdef"
        notdef_glyph.graphicType = "png "
        notdef_glyph.originOffsetX = 0
        notdef_glyph.originOffsetY = 0
        notdef_glyph.imageData = b""
        strike.glyphs[".notdef"] = notdef_glyph

        # Add emoji glyphs
        for i, img_file in enumerate(image_files):
            glyph_name = glyph_order[i + 1]  # +1 to skip .notdef

            # Resize image to match ppem size
            png_data = resize_image_to_ppem(img_file, ppem)

            # Create SBIX glyph
            glyph = sbixGlyph.Glyph()
            glyph.glyphName = glyph_name
            glyph.graphicType = "png "
            # Calculate origin offsets for proper centering
            # The bitmap is placed relative to the glyph's origin point
            # X offset: center horizontally within advance width
            # Y offset: position so the image is vertically centered
            # Since we're using 800 units per em and the bitmap is ppem pixels,
            # we need to scale appropriately
            scale_factor = 800 / ppem
            glyph.originOffsetX = 0  # Already centered in resize function
            # Vertical centering: descender offset
            glyph.originOffsetY = int(-250 / scale_factor)
            glyph.imageData = png_data

            strike.glyphs[glyph_name] = glyph

        sbix.strikes[ppem] = strike

    font["sbix"] = sbix

    # Save the font
    print(f"\nSaving font to {output_path}...")
    font.save(output_path)
    print(f"Font created successfully: {output_path}")

    return output_path


def main():
    """Main entry point."""
    print("Fontaku Font Generator")
    print("=" * 50)
    print("Generating emoji font with standard Unicode codepoints")

    # Get image files
    images_dir = "images"
    if not os.path.exists(images_dir):
        print(f"Error: '{images_dir}' directory not found!")
        return

    image_files = get_image_files(images_dir)

    if not image_files:
        print(f"Error: No PNG files found in '{images_dir}' directory!")
        print("Please add PNG files named like 'U+E001.png', 'U+E002.png', etc.")
        return

    print(f"Found {len(image_files)} image files\n")

    # Build the font
    try:
        output_file = build_font(image_files, "Fontaku.ttf")
        print("\n" + "=" * 50)
        print("✓ Font generation complete!")
        print(f"\nYou can now install '{output_file}' on macOS by:")
        print("1. Double-clicking the .ttf file")
        print("2. Clicking 'Install Font' in Font Book")
        print("\n⚠️  Your custom emojis will replace system emojis:")
        print(
            f"   Starting from U+1F600 (😀) through U+{0x1F600 + len(image_files) - 1:04X}"
        )
        print("\n💡 Tip: Your emojis will appear in the emoji picker!")
    except Exception as e:
        print(f"\nError generating font: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
