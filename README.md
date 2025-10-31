# Fontaku Font Generator

Generate custom emoji fonts from PNG images for macOS. Creates TrueType fonts with SBIX bitmap tables that replace system emojis starting from U+1F600 (😀).

![Demo](docs/demo.png)

## Features

- ✅ **Replace system emojis** with your custom PNG artwork
- ✅ **Work in all applications** (text editors, messaging apps, browsers)
- ✅ **Scale properly** at all text sizes
- ✅ **Automated releases** via GitHub Actions

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Add PNG images** to the `images/` directory named like `U+E001.png`, `U+E002.png`, etc.

3. **Generate the font:**
   ```bash
   python generate.py
   ```

4. **Install the font** by double-clicking `Fontaku.ttf` and selecting "Install Font" in Font Book.

## Automated Releases

Push a version tag to automatically build and release the font:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Download pre-built fonts from the [Releases](../../releases) page.

## How It Works

The font generation process uses Apple's SBIX (Standard Bitmap Image eXtension) format:

1. **Image Processing**: PNG images are resized to multiple sizes (32, 64, 128, 256 ppem) while maintaining aspect ratio
2. **Font Metrics**: Uses metrics matching Apple Color Emoji (800 units per em, advance width of 800)
3. **Unicode Mapping**: Maps to standard emoji codepoints starting at U+1F600 (😀)
4. **SBIX Tables**: Embeds bitmap data at multiple strikes for proper scaling
5. **Glyph Centering**: Images are horizontally and vertically centered using proper origin offsets

The resulting font replaces Apple's default emojis, displaying your custom PNG artwork instead.

## Important Notes

⚠️ **Emoji Picker Limitation**: The macOS emoji picker shows Apple's default previews, but your custom emojis will render correctly in actual text when selected.

**Requirements**: Python 3.7+, FontTools, Pillow

## Image Attribution

Images by https://www.freepik.com/author/gstudioimagen
