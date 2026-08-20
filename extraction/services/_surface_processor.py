import cv2
import numpy as np
from PIL import Image

from extraction.constants import (
    BACKGROUND_BORDER_RATIO,
    BACKGROUND_COLOR_THRESHOLD,
    BACKGROUND_UNIFORM_RATIO,
    EXTRACTION_MODEL_VERSION,
    MAX_STAMP_AREA_RATIO,
    MIN_STAMP_AREA_RATIO,
)
from extraction.dtos import StampBoxDTO, SurfaceExtractionDTO


class SurfaceProcessor:
    """Find one stamp lying on a mostly single-colour background."""

    def process(self, image_bytes: bytes) -> SurfaceExtractionDTO:
        image = self._decode_image(image_bytes)
        background, uniform_ratio = self._validate_background(image)
        mask = self._foreground_mask(image, background)
        stamp_box = self._find_stamp_box(mask, image.shape[:2])
        cropped_stamp = self._crop_stamp(image, stamp_box)

        height, width = image.shape[:2]
        return SurfaceExtractionDTO(
            cropped_stamp=cropped_stamp,
            # A plain surface provides no real-world scale. These legacy model
            # fields therefore intentionally carry "unknown" as zero.
            width_mm=0.0,
            height_mm=0.0,
            dominant_colors=self._dominant_colors(cropped_stamp),
            model_version=EXTRACTION_MODEL_VERSION,
            image_width_px=width,
            image_height_px=height,
            background_color=self._hex_color(background),
            background_uniform_ratio=round(uniform_ratio, 4),
            stamp_box=StampBoxDTO(*stamp_box),
        )

    @staticmethod
    def _decode_image(image_bytes: bytes) -> np.ndarray:
        encoded = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("The uploaded file could not be decoded as an image.")
        return image

    @staticmethod
    def _border_pixels(image: np.ndarray) -> np.ndarray:
        height, width = image.shape[:2]
        border = max(2, round(min(height, width) * BACKGROUND_BORDER_RATIO))
        return np.concatenate(
            (
                image[:border].reshape(-1, 3),
                image[-border:].reshape(-1, 3),
                image[border:-border, :border].reshape(-1, 3),
                image[border:-border, -border:].reshape(-1, 3),
            ),
            axis=0,
        )

    def _validate_background(self, image: np.ndarray) -> tuple[np.ndarray, float]:
        border_pixels = self._border_pixels(image).astype(np.float32)
        background = np.median(border_pixels, axis=0)
        distances = np.linalg.norm(border_pixels - background, axis=1)
        uniform_ratio = float(np.mean(distances <= BACKGROUND_COLOR_THRESHOLD))
        if uniform_ratio < BACKGROUND_UNIFORM_RATIO:
            raise ValueError(
                "The background is not uniform enough. Put one stamp on a "
                "plain, single-colour surface with clear space around every edge."
            )
        return background, uniform_ratio

    @staticmethod
    def _foreground_mask(image: np.ndarray, background: np.ndarray) -> np.ndarray:
        distances = np.linalg.norm(
            image.astype(np.float32) - background,
            axis=2,
        )
        mask = np.where(distances > BACKGROUND_COLOR_THRESHOLD, 255, 0).astype(
            np.uint8
        )
        kernel_size = max(3, round(min(image.shape[:2]) * 0.01))
        if kernel_size % 2 == 0:
            kernel_size += 1
        kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        return cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            np.ones((3, 3), dtype=np.uint8),
        )

    @staticmethod
    def _find_stamp_box(
        mask: np.ndarray,
        image_shape: tuple[int, int],
    ) -> tuple[int, int, int, int]:
        height, width = image_shape
        image_area = height * width
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        candidates = []
        for contour in contours:
            x, y, box_width, box_height = cv2.boundingRect(contour)
            area_ratio = box_width * box_height / image_area
            touches_image_edge = (
                x == 0
                or y == 0
                or x + box_width >= width
                or y + box_height >= height
            )
            if (
                MIN_STAMP_AREA_RATIO <= area_ratio <= MAX_STAMP_AREA_RATIO
                and not touches_image_edge
            ):
                candidates.append((x, y, box_width, box_height))

        if not candidates:
            raise ValueError(
                "No isolated stamp was found. Keep the whole stamp visible with "
                "plain background around it."
            )

        # Reading candidates left-to-right gives a deterministic left edge;
        # area then selects the complete object instead of small specks/noise.
        candidates.sort(key=lambda box: box[0])
        return max(candidates, key=lambda box: box[2] * box[3])

    @staticmethod
    def _crop_stamp(
        image: np.ndarray,
        stamp_box: tuple[int, int, int, int],
    ) -> np.ndarray:
        x, y, width, height = stamp_box
        padding = max(2, round(min(width, height) * 0.02))
        left = max(0, x - padding)
        top = max(0, y - padding)
        right = min(image.shape[1], x + width + padding)
        bottom = min(image.shape[0], y + height + padding)
        return image[top:bottom, left:right].copy()

    @staticmethod
    def _dominant_colors(image: np.ndarray) -> list[str]:
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        pil_image.thumbnail((200, 200))
        quantized = pil_image.quantize(colors=3)
        color_counts = quantized.getcolors() or []
        palette = quantized.getpalette() or []
        colors = []
        for _, palette_index in sorted(color_counts, reverse=True):
            offset = palette_index * 3
            red, green, blue = palette[offset : offset + 3]
            colors.append(f"#{red:02x}{green:02x}{blue:02x}")
        return colors

    @staticmethod
    def _hex_color(bgr_color: np.ndarray) -> str:
        blue, green, red = np.rint(bgr_color).astype(np.uint8)
        return f"#{red:02x}{green:02x}{blue:02x}"
