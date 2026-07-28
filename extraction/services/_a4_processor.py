import cv2
import numpy as np
from PIL import Image

from extraction.constants import (
    A4_LONG_SIDE_MM,
    A4_SHORT_SIDE_MM,
    EXTRACTION_MODEL_VERSION,
)
from extraction.dtos import A4ExtractionDTO, StampBoxDTO


class A4Processor:
    _MIN_PAGE_AREA_RATIO = 0.20
    _MIN_STAMP_AREA_RATIO = 0.0005
    _MAX_STAMP_SIDE_RATIO = 0.65
    _PAGE_INSET_RATIO = 0.04

    def process(self, image_bytes: bytes) -> A4ExtractionDTO:
        image = self._decode_image(image_bytes)
        page_corners = self._find_page_corners(image)
        corrected_page, page_width_mm, page_height_mm = self._warp_page(
            image,
            page_corners,
        )
        stamp_box = self._find_stamp_box(corrected_page)
        cropped_stamp = self._crop_stamp(corrected_page, stamp_box)

        x, y, width, height = stamp_box
        stamp_width_mm = width * page_width_mm / corrected_page.shape[1]
        stamp_height_mm = height * page_height_mm / corrected_page.shape[0]

        return A4ExtractionDTO(
            cropped_stamp=cropped_stamp,
            width_mm=round(stamp_width_mm, 2),
            height_mm=round(stamp_height_mm, 2),
            dominant_colors=self._dominant_colors(cropped_stamp),
            model_version=EXTRACTION_MODEL_VERSION,
            a4_corners=page_corners.round(2).tolist(),
            a4_width_mm=page_width_mm,
            a4_height_mm=page_height_mm,
            corrected_page_width_px=corrected_page.shape[1],
            corrected_page_height_px=corrected_page.shape[0],
            stamp_box=StampBoxDTO(
                x=x,
                y=y,
                width=width,
                height=height,
            ),
        )

    @staticmethod
    def _decode_image(image_bytes: bytes) -> np.ndarray:
        encoded = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("The uploaded file could not be decoded as an image.")
        return image

    def _find_page_corners(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        edges = cv2.morphologyEx(
            edges,
            cv2.MORPH_CLOSE,
            np.ones((7, 7), dtype=np.uint8),
        )

        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        minimum_area = image.shape[0] * image.shape[1] * self._MIN_PAGE_AREA_RATIO

        for contour in sorted(contours, key=cv2.contourArea, reverse=True):
            if cv2.contourArea(contour) < minimum_area:
                break

            perimeter = cv2.arcLength(contour, True)
            polygon = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            if len(polygon) == 4 and cv2.isContourConvex(polygon):
                return self._order_corners(polygon.reshape(4, 2).astype(np.float32))

        raise ValueError(
            "Could not detect the complete A4 sheet. Keep all four edges and "
            "corners visible with some background around them."
        )

    @staticmethod
    def _order_corners(points: np.ndarray) -> np.ndarray:
        ordered = np.zeros((4, 2), dtype=np.float32)
        coordinate_sum = points.sum(axis=1)
        coordinate_difference = np.diff(points, axis=1).reshape(-1)

        ordered[0] = points[np.argmin(coordinate_sum)]
        ordered[2] = points[np.argmax(coordinate_sum)]
        ordered[1] = points[np.argmin(coordinate_difference)]
        ordered[3] = points[np.argmax(coordinate_difference)]
        return ordered

    @staticmethod
    def _warp_page(
        image: np.ndarray,
        corners: np.ndarray,
    ) -> tuple[np.ndarray, float, float]:
        top_left, top_right, bottom_right, bottom_left = corners
        measured_width = max(
            np.linalg.norm(top_right - top_left),
            np.linalg.norm(bottom_right - bottom_left),
        )
        measured_height = max(
            np.linalg.norm(bottom_left - top_left),
            np.linalg.norm(bottom_right - top_right),
        )

        if measured_width <= measured_height:
            page_width_mm = A4_SHORT_SIDE_MM
            page_height_mm = A4_LONG_SIDE_MM
            output_width = max(1, round(measured_width))
            output_height = max(
                1,
                round(output_width * A4_LONG_SIDE_MM / A4_SHORT_SIDE_MM),
            )
        else:
            page_width_mm = A4_LONG_SIDE_MM
            page_height_mm = A4_SHORT_SIDE_MM
            output_width = max(1, round(measured_width))
            output_height = max(
                1,
                round(output_width * A4_SHORT_SIDE_MM / A4_LONG_SIDE_MM),
            )

        destination = np.array(
            [
                [0, 0],
                [output_width - 1, 0],
                [output_width - 1, output_height - 1],
                [0, output_height - 1],
            ],
            dtype=np.float32,
        )
        transform = cv2.getPerspectiveTransform(corners, destination)
        corrected = cv2.warpPerspective(
            image,
            transform,
            (output_width, output_height),
        )
        return corrected, page_width_mm, page_height_mm

    def _find_stamp_box(self, page: np.ndarray) -> tuple[int, int, int, int]:
        height, width = page.shape[:2]
        inset_x = max(1, round(width * self._PAGE_INSET_RATIO))
        inset_y = max(1, round(height * self._PAGE_INSET_RATIO))
        interior = page[inset_y : height - inset_y, inset_x : width - inset_x]

        border_pixels = np.concatenate(
            (
                interior[: max(1, interior.shape[0] // 20)].reshape(-1, 3),
                interior[-max(1, interior.shape[0] // 20) :].reshape(-1, 3),
                interior[:, : max(1, interior.shape[1] // 20)].reshape(-1, 3),
                interior[:, -max(1, interior.shape[1] // 20) :].reshape(-1, 3),
            ),
            axis=0,
        )
        background_color = np.median(border_pixels, axis=0)
        difference = np.linalg.norm(
            interior.astype(np.float32) - background_color,
            axis=2,
        )
        mask = np.where(difference > 25, 255, 0).astype(np.uint8)

        kernel_size = max(3, round(min(interior.shape[:2]) * 0.015))
        if kernel_size % 2 == 0:
            kernel_size += 1
        kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            np.ones((3, 3), dtype=np.uint8),
        )

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        page_area = width * height
        candidates = []
        for contour in contours:
            x, y, box_width, box_height = cv2.boundingRect(contour)
            area_ratio = box_width * box_height / page_area
            if area_ratio < self._MIN_STAMP_AREA_RATIO:
                continue
            if (
                box_width > width * self._MAX_STAMP_SIDE_RATIO
                or box_height > height * self._MAX_STAMP_SIDE_RATIO
            ):
                continue
            candidates.append((x, y, box_width, box_height))

        if not candidates:
            raise ValueError(
                "The A4 sheet was detected, but the stamp could not be isolated."
            )

        x, y, box_width, box_height = max(
            candidates,
            key=lambda box: box[2] * box[3],
        )
        return x + inset_x, y + inset_y, box_width, box_height

    @staticmethod
    def _crop_stamp(
        page: np.ndarray,
        stamp_box: tuple[int, int, int, int],
    ) -> np.ndarray:
        x, y, width, height = stamp_box
        padding = max(2, round(min(width, height) * 0.02))
        left = max(0, x - padding)
        top = max(0, y - padding)
        right = min(page.shape[1], x + width + padding)
        bottom = min(page.shape[0], y + height + padding)
        return page[top:bottom, left:right].copy()

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
