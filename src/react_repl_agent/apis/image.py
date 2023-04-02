import io
from typing import Literal, Union, get_args

import PIL.Image
import requests

ImgFileFormat = Literal["jpeg", "png"]


class Image:
    """Custom image class."""

    _pil_image: PIL.Image

    def __init__(self, image: PIL.Image) -> None:
        self._pil_image = image

    def copy(self) -> "Image":
        return Image(self._pil_image.copy())

    def as_bytes_stream(self, img_format: Union[ImgFileFormat, str]) -> io.BytesIO:
        assert img_format in get_args(ImgFileFormat)
        img_byte_stream = io.BytesIO()
        self._pil_image.save(
            img_byte_stream,
            format=img_format,
            optimize=True,
            quality=80,
        )
        img_byte_stream.flush()
        img_byte_stream.seek(0)
        return img_byte_stream

    def as_bytes(self, img_format: Union[ImgFileFormat, str]) -> bytes:
        return self.as_bytes_stream(img_format).getvalue()

    def __repr__(self):
        width, height = self._pil_image.size
        return f"<Image width={width}, height={height}>"

    def __str__(self):
        return repr(self)

    def __getattr__(self, name):
        raise AttributeError(
            f"Image.{name} does not exist! Only use `Image` as a parameter in other methods. Search for them if needed."
        )


def download_image(url: str) -> Image:
    """
    Download the image from the given URL and return as an Image object.

    Args:
            url (str): URL to download image from.

    Returns:
            Image representing the image from the given URL.
    """
    return Image(PIL.Image.open(requests.get(url, stream=True).raw))


def shrink_image(image: Image, ratio: float) -> Image:
    """
    Shrink (resize) the given image by the given ratio.

    Args:
            image (Image): Image to resize.

            ratio (float): Ratio to resize the image with. A ratio of 0.5 will shrink the image to half its original size. (0 < ratio <= 1)

    Returns:
            Given image resized by the given ratio
    """
    assert 0 < ratio <= 1, "ratio needs to be greater than 0 and smaller than 1."
    size = image._pil_image.size
    size = tuple(x * ratio for x in size)
    new_image = image.copy()
    new_image._pil_image.thumbnail(size, PIL.Image.Resampling.LANCZOS)
    return new_image
