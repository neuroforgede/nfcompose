# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


import base64
import io

from typing import NamedTuple, Tuple, Protocol


class CutoutSpec(NamedTuple):
    x: float
    y: float
    width: float
    height: float
    margin: float


class CutoutBox(NamedTuple):
    x1: float
    y1: float
    x2: float
    y2: float


class Image(Protocol):
    width: int
    height: int
    size: Tuple[int, int]

    def crop(self, cutout_box: CutoutBox) -> 'Image':
        pass

    def save(self, buffered: io.BytesIO, format: str) -> None:
        pass


def image_as_bytes(image: Image, format: str) -> bytes:
    buffered = io.BytesIO()
    image.save(buffered, format)
    return buffered.getvalue()


def bytes_as_data_uri(bts: io.BytesIO, format: str) -> str:
    return string_to_data_uri(base64.b64encode(bts.getvalue()).decode(), format)


def string_to_data_uri(b64: str, format: str) -> str:
    return 'data:image/{};base64,{}'.format(format.lower(), b64)


def image_as_data_uri(image: Image, format: str) -> str:
    _image_as_bytes = image_as_bytes(image, format)
    return 'data:image/{};base64,{}'.format(format.lower(), base64.b64encode(_image_as_bytes).decode())


def calc_cutout_box_with_max_size(image_width: float, image_height: float, cutout: CutoutSpec) -> CutoutBox:
    assert cutout.width > 0
    assert cutout.height > 0

    additional_cutout_width: float = cutout.width * cutout.margin
    additional_cutout_height: float = cutout.height * cutout.margin

    actual_x1 = max(0.0, cutout.x - (additional_cutout_width / 2))
    actual_y1 = max(0.0, cutout.y - (additional_cutout_height / 2))
    actual_x2 = min(image_width, max(0.0, cutout.x) + cutout.width + additional_cutout_width / 2)
    actual_y2 = min(image_height, max(0.0, cutout.y) + cutout.height + additional_cutout_height / 2)

    return CutoutBox(actual_x1, actual_y1, actual_x2, actual_y2)


class Hotspot(Protocol):
    pos_x: float
    pos_y: float
    width: float
    height: float
    margin: float


def hotspot_to_cutout_spec(image: Image, hotspot: Hotspot, include_margin: bool = False) -> CutoutSpec:
    _image_width = image.width
    _image_height = image.height

    _actual_x = hotspot.pos_x * _image_width
    _actual_y = hotspot.pos_y * _image_height
    _actual_width = hotspot.width * _image_width
    _actual_height = hotspot.height * _image_height

    margin = 0.0
    if include_margin:
        margin = hotspot.margin
    return CutoutSpec(
        x=_actual_x,
        y=_actual_y,
        width=_actual_width,
        height=_actual_height,
        margin=margin
    )


def crop_by_hotspot(image: Image, hotspot: Hotspot, include_margin: bool = False) -> Image:
    return cutout_image_with_margin(image, hotspot_to_cutout_spec(image, hotspot, include_margin))


def cutout_image_with_margin(image: Image, cutout: CutoutSpec) -> Image:
    """
    cuts out an image with margin
    """
    image_width, image_height = image.size

    cutout_box = calc_cutout_box_with_max_size(image_width, image_height, cutout)

    return image.crop(cutout_box)
