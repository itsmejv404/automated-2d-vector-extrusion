import os
import subprocess
from PIL import Image, ImageFilter
DDS_HEADER_SIZE = 128
TARGET_SIZE = 1024

def resize_to_template(input_png,output_png,template_width,template_height,bg_color=(0, 0, 0)):
    img = Image.open(input_png).convert("RGBA")

    # Preserve aspect ratio
    img.thumbnail((template_width, template_height), Image.LANCZOS)

    # Background canvas
    canvas = Image.new("RGBA", (template_width, template_height), (*bg_color, 255))

    # Center the image
    x = (template_width - img.width) // 2
    y = (template_height - img.height) // 2

    canvas.paste(img, (x, y), img)

    canvas.convert("RGB").save(output_png)
def png_to_temp_dds(png_path, mipmaps=10):
    subprocess.run(
        [
            "texconv",
            "-f", "BC1_UNORM",
            "-m", str(mipmaps),
            "-y",
            png_path
        ],
        check=True
    )
def replace_dds_pixel_data(template_dds, new_dds, output_dds):
    with open(template_dds, "rb") as f:
        template = f.read()

    with open(new_dds, "rb") as f:
        new = f.read()

    final = template[:DDS_HEADER_SIZE] + new[DDS_HEADER_SIZE:]

    with open(output_dds, "wb") as f:
        f.write(final)
def png_to_gta_dds(user_png,photopea_dds,output_dds,resize_bg=(0, 0, 0),mipmaps=10):
    # Read template DDS size
    with open(photopea_dds, "rb") as f:
        header = f.read(128)

    width = int.from_bytes(header[16:20], "little")
    height = int.from_bytes(header[12:16], "little")

    temp_png = "resized.png"
    temp_dds = "resized.dds"

    resize_to_template(user_png, temp_png, width, height, resize_bg)
    png_to_temp_dds(temp_png, mipmaps)
    replace_dds_pixel_data(photopea_dds, temp_dds, output_dds)

    print("✅ GTA-compatible DDS created:", output_dds)
def resize_png_with_transparency(img, size=TARGET_SIZE):
    """
    Resize PNG to size x size while preserving transparency
    and aspect ratio, centered on transparent canvas.
    """
    img = img.convert("RGBA")

    # Aspect-safe resize
    img.thumbnail((size, size), Image.LANCZOS)

    # Transparent canvas
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Center the image
    x = (size - img.width) // 2
    y = (size - img.height) // 2
    canvas.paste(img, (x, y), img)

    return canvas
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
        # Check alpha
        if img.mode not in ('RGBA', 'LA'):
            print("PNG without transparency → resizing only")
            img = resize_png_with_transparency(img)
            img.save(output_bw)
            return

        print("PNG with transparency detected → resizing + converting alpha to B/W")

        # Resize FIRST (important)
        img = resize_png_with_transparency(img)

        # Extract alpha channel
        _, _, _, alpha = img.split()

        # Alpha → B/W
        # Transparent (0) → white
        # Non-transparent → black
        bw = alpha.point(lambda a: 255 if a == 0 else 0, '1')

        # Save BW PNG
        bw.save(output_bw)

        # Prepare PBM-style output
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


png_to_gta_dds(user_png="input.png",photopea_dds="base.dds",output_dds="final.dds",resize_bg=(0, 0, 0),)
convert_to_bw("input.png", "resized_bw.png", "resized_bw.pbm")
png_to_svg("resized_bw.pbm", "resized_bw.svg")

