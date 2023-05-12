# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.test import TestCase

from skipper.core.utils import image as image_util


class CutoutBoxTest(TestCase):

    def test_assert_wrong_cutout_box(self) -> None:
        try:
            image_util.calc_cutout_box_with_max_size(100, 100, image_util.CutoutSpec(
                x=10,
                y=10,
                width=0,
                height=10,
                margin=0
            ))
            self.fail("expected AssertionError")
        except AssertionError as e:
            pass

        try:
            image_util.calc_cutout_box_with_max_size(100, 100, image_util.CutoutSpec(
                x=10,
                y=10,
                width=10,
                height=0,
                margin=0
            ))
            self.fail("expected AssertionError")
        except AssertionError as e:
            pass

        try:
            image_util.calc_cutout_box_with_max_size(100, 100, image_util.CutoutSpec(
                x=10,
                y=10,
                width=-10,
                height=10,
                margin=0
            ))
            self.fail("expected AssertionError")
        except AssertionError as e:
            pass

        try:
            image_util.calc_cutout_box_with_max_size(100, 100, image_util.CutoutSpec(
                x=10,
                y=10,
                width=10,
                height=-10,
                margin=0
            ))
            self.fail("expected AssertionError")
        except AssertionError as e:
            pass

    def test_no_margin(self) -> None:
        self.assertEqual(
            (10, 10, 20, 20),
            image_util.calc_cutout_box_with_max_size(100, 100, image_util.CutoutSpec(
                x=10,
                y=10,
                width=10,
                height=10,
                margin=0
            )))

    def test_completely_too_big(self) -> None:
        self.assertEqual(
            (0, 0, 1, 2),
            image_util.calc_cutout_box_with_max_size(1, 2, image_util.CutoutSpec(
                x=-1000,
                y=-1000,
                width=1000,
                height=1000,
                margin=0
            )))

    def test_margin_too_big_in_all(self) -> None:
        self.assertEqual(
            (0, 0, 10, 10),
            image_util.calc_cutout_box_with_max_size(10, 10, image_util.CutoutSpec(
                x=0,
                y=0,
                width=10,
                height=10,
                margin=1
            )))

    def test_margin_in_bound(self) -> None:
        self.assertEqual(
            (9, 9, 21, 21),
            image_util.calc_cutout_box_with_max_size(100, 100, image_util.CutoutSpec(
                x=10,
                y=10,
                width=10,
                height=10,
                margin=0.2
            )))

    def test_margin_out_of_bounds(self) -> None:
        self.assertEqual(
            (0, 0, 11.5, 11),
            image_util.calc_cutout_box_with_max_size(100, 100, image_util.CutoutSpec(
                x=0.5,
                y=0,
                width=10,
                height=10,
                margin=0.2
            )))

        self.assertEqual(
            (0, 0, 11, 11.5),
            image_util.calc_cutout_box_with_max_size(100, 100, image_util.CutoutSpec(
                x=0,
                y=0.5,
                width=10,
                height=10,
                margin=0.2
            )))

        self.assertEqual(
            (0, 0, 11.5, 11),
            image_util.calc_cutout_box_with_max_size(11.5, 11.5, image_util.CutoutSpec(
                x=1,
                y=0,
                width=10,
                height=10,
                margin=0.2
            )))

        self.assertEqual(
            (0, 0, 11, 11.5),
            image_util.calc_cutout_box_with_max_size(11.5, 11.5, image_util.CutoutSpec(
                x=0,
                y=1,
                width=10,
                height=10,
                margin=0.2
            )))
