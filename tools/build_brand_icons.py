"""Rebuild the 52at52 app icons. Requires Pillow (not needed for migration)."""
from pathlib import Path
from PIL import Image
from project_paths import SITE, ensure_new_site


def main():
    ensure_new_site()
    source = SITE / "assets/brand-shield.png"
    if not source.is_file():
        raise SystemExit("Approved shield logo is missing. No icons changed.")
    logo = Image.open(source).convert("RGBA")
    image = Image.new("RGBA", (512, 512), "#ffffff")
    logo.thumbnail((456, 456), Image.Resampling.LANCZOS)
    image.alpha_composite(logo, ((512 - logo.width) // 2, (512 - logo.height) // 2))
    directory = SITE / "icons"
    directory.mkdir(parents=True, exist_ok=True)
    for pixels in (192, 512):
        image.resize((pixels, pixels), Image.Resampling.LANCZOS).save(directory / f"icon-{pixels}.png")
    print("Built 192px and 512px icons from the approved 52at52 shield. Archive untouched.")


if __name__ == "__main__":
    main()
