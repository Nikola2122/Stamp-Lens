import unittest

import cv2
import numpy as np

from extraction.services._surface_processor import SurfaceProcessor


class SurfaceProcessorTests(unittest.TestCase):
    @staticmethod
    def _encode(image: np.ndarray) -> bytes:
        success, encoded = cv2.imencode(".png", image)
        if not success:
            raise AssertionError("Test image could not be encoded.")
        return encoded.tobytes()

    def test_crops_stamp_from_non_white_uniform_surface(self):
        image = np.full((500, 700, 3), (60, 120, 180), dtype=np.uint8)
        image[140:380, 210:470] = (225, 225, 220)
        image[190:260, 270:410] = (20, 50, 160)

        result = SurfaceProcessor().process(self._encode(image))

        self.assertEqual(result.stamp_box.x, 210)
        self.assertEqual(result.stamp_box.y, 140)
        self.assertEqual(result.stamp_box.width, 260)
        self.assertEqual(result.stamp_box.height, 240)
        self.assertEqual(result.background_color, "#b4783c")
        self.assertEqual(result.width_mm, 0.0)
        self.assertGreater(result.cropped_stamp.shape[0], 240)

    def test_rejects_non_uniform_background(self):
        rng = np.random.default_rng(7)
        image = rng.integers(0, 256, (400, 600, 3), dtype=np.uint8)

        with self.assertRaisesRegex(ValueError, "not uniform enough"):
            SurfaceProcessor().process(self._encode(image))

    def test_rejects_image_without_stamp(self):
        image = np.full((400, 600, 3), 200, dtype=np.uint8)

        with self.assertRaisesRegex(ValueError, "No isolated stamp"):
            SurfaceProcessor().process(self._encode(image))
