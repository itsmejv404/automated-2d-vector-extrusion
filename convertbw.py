from PIL import Image, ImageFilter
import subprocess
import os

def convert_to_bw(input_img, output_bw, output_pbm):
    img = Image.open(input_img)
    ext = os.path.splitext(input_img)[1].lower()

    # CASE 1: JPEG → leave unchanged
    if ext in ['.jpg', '.jpeg']:
        print("JPEG detected → leaving image unchanged")
        img.save(output_bw)
        return

    # CASE 2: PNG
    if ext == '.png':
        # Check if PNG has alpha channel
        if img.mode not in ('RGBA', 'LA'):
            print("PNG without transparency → leaving unchanged")
            img.save(output_bw)
            return

        print("PNG with transparency detected → converting alpha to B/W")

        # Ensure RGBA
        img = img.convert("RGBA")

        # Extract alpha channel
        _, _, _, alpha = img.split()

        # Convert alpha to pure B/W:
        # Transparent (alpha=0)   → white
        # Non-transparent (>0)    → black
        bw = alpha.point(lambda a: 255 if a == 0 else 0, '1')

        bw.save(output_bw)
        bw = bw.convert("L")
        bw = bw.filter(ImageFilter.MaxFilter(3))
        bw = bw.filter(ImageFilter.MinFilter(3))
        bw.save(output_pbm)
        return


def png_to_svg(bw_png, output_svg):
    subprocess.run([
        r"potrace\potrace",
        bw_png,
        "-s",
        "--turdsize", "10",     # removes tiny artifacts
        "--alphamax", "1.0",   # smoother curves
        "--opttolerance", "0.2",
        "-o",
        output_svg
    ], check=True)


# Example usage
convert_to_bw("input.png", "bw.png", "bw.pbm")
png_to_svg("bw.pbm", "output.svg")
