import io

from PIL import Image

'''
Saving the graph as an image (PNG, TIFF, JPG) at a given resolution

The figure is drawn directly at its final size: never resized afterwards, which would lose resolution (a 600 DPI
export resized to the screen's pixels) or stretch the graph (a fixed size of another shape).
    the graph's size     the figure's size in inches (screen pixels / screen DPI) at the chosen DPI: the same layout
                         as on screen, sharper (640 x 480 px on screen, 600 DPI -> 3840 x 2880 px)
    a fixed size         the figure laid out for width x height pixels at the chosen DPI (width / DPI inches): text
                         keeps its size in points, as in a journal figure (8.5 cm at 600 DPI = 2008 px wide)
'''


# Size of the saved image in pixels: (width, height)
def image_pixels(figure, dpi, size_px=None):
    if size_px:
        return int(size_px[0]), int(size_px[1])
    width, height = figure.get_size_inches()
    return int(round(width * dpi)), int(round(height * dpi))


# Save the figure; size_px None: the figure's own size; grayscale: one gray channel. Returns the image's (width,
# height) in pixels.
def save_figure_image(figure, path, dpi, size_px=None, grayscale=False):
    original = figure.get_size_inches().copy()
    width, height = image_pixels(figure, dpi, size_px)
    buffer = io.BytesIO()
    try:
        # +0.5 px: the renderer truncates width x DPI, so an exact quotient could lose the last pixel to rounding
        figure.set_size_inches((width + 0.5) / dpi, (height + 0.5) / dpi, forward=False)
        figure.tight_layout()
        figure.savefig(buffer, format="png", dpi=dpi)    # lossless, in memory: the file is written once, below
    finally:
        figure.set_size_inches(original, forward=False)
        figure.tight_layout()

    buffer.seek(0)
    with Image.open(buffer) as drawn:
        image = drawn.copy()
    suffix = str(path).lower().rsplit(".", 1)[-1]
    image_format = {"jpg": "JPEG", "jpeg": "JPEG", "tif": "TIFF", "tiff": "TIFF"}.get(suffix, "PNG")
    if grayscale:
        image = image.convert("L")
    elif image_format == "JPEG":                     # JPEG has no transparency
        image = image.convert("RGB")
    image.save(path, format=image_format, dpi=(dpi, dpi))     # the resolution written in the file (journals check it)
    return image.size
