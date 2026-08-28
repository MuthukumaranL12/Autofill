from __future__ import annotations

from typing import Any

from PIL import ImageDraw, ImageFont

from backend.models.form_models import MatchField
from backend.models.identity_profile import IdentityProfile


class AutoFill:
    """Resolves matched fields to profile values and optionally renders values on an image."""

    def __init__(self) -> None:
        self.profile: IdentityProfile | None = None

    def set_profile(self, profile: IdentityProfile) -> None:
        self.profile = profile

    # Canonical form fields are not always named exactly like the
    # IdentityProfile attributes. Keep this mapping in the final
    # resolution layer so the semantic matcher remains responsible
    # only for identifying what the form field means.
    CANONICAL_TO_PROFILE_FIELD = {
        "phone_number": "phone",
        "father_name": "guardian_name",
        "house_flat": "house_number",
    }

    def resolve_value(self, matched_field: MatchField) -> str | None:
        if not matched_field.canonical_field or self.profile is None:
            return None

        canonical_field = matched_field.canonical_field.strip().lower()

        profile_field = self.CANONICAL_TO_PROFILE_FIELD.get(
            canonical_field,
            canonical_field,
        )

        value = getattr(self.profile, profile_field, None)

        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()
            return value if value else None

        return str(value)

    def bbox_to_pixels(self, bbox: dict[str, float], image_width: int, image_height: int) -> dict[str, int]:
        return {
            "left": int(bbox["left"] * image_width),
            "top": int(bbox["top"] * image_height),
            "width": int(bbox["width"] * image_width),
            "height": int(bbox["height"] * image_height),
        }

    @staticmethod
    def _load_font(font_size: int):
        try:
            return ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            # Fallback for environments without Arial.
            return ImageFont.load_default()

    # def _draw_text(self, image: Any, value: str, bbox: dict[str, int]) -> None:
    #     if not value:
    #         return

    #     draw = ImageDraw.Draw(image)

    #     field_height = bbox["height"]
    #     if field_height >= 30:
    #         font_size = 20
    #     elif field_height >= 20:
    #         font_size = 17
    #     else:
    #         font_size = 15

    #     font = self._load_font(font_size)
    #     text_bbox = draw.textbbox((0, 0), value, font=font)
    #     text_height = text_bbox[3] - text_bbox[1]

    #     x = bbox["left"]
    #     y = bbox["top"] + (bbox["height"] - text_height) / 2

    #     draw.text((x, y), value, font=font, fill="black")

    # def _draw_text_in_cells(self, image: Any, value: str, cells: list[Any]) -> None:
    #     if not value:
    #         return

    #     draw = ImageDraw.Draw(image)
    #     font = self._load_font(20)

    #     for char, cell in zip(str(value), cells):
    #         bbox = self.bbox_to_pixels(cell.bbox, image.width, image.height)

    #         char_bbox = draw.textbbox((0, 0), char, font=font)
    #         char_width = char_bbox[2] - char_bbox[0]
    #         char_height = char_bbox[3] - char_bbox[1]

    #         x = bbox["left"] + (bbox["width"] - char_width) / 2
    #         y = bbox["top"] + (bbox["height"] - char_height) / 2

    #         draw.text((x, y), char, font=font, fill="black")

    def _draw_text(self, image: Any, value: str, bbox: dict[str, int]) -> None:
        if not value:
            return

        draw = ImageDraw.Draw(image)

        # Field dimensions
        field_width = bbox["width"]
        field_height = bbox["height"]

        # Font size limits
        max_font_size = 20
        min_font_size = 7

        # Padding so text doesn't touch the field boundaries
        horizontal_padding = 4
        vertical_padding = 2

        available_width = field_width - (horizontal_padding * 2)
        available_height = field_height - (vertical_padding * 2)

        # Start with the largest font
        font_size = max_font_size

        # Reduce font size until the complete value fits
        while font_size >= min_font_size:

            font = self._load_font(font_size)

            text_bbox = draw.textbbox(
                (0, 0),
                value,
                font=font
            )

            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            if (
                text_width <= available_width
                and text_height <= available_height
            ):
                break

            font_size -= 1

        # If even the minimum font does not fit,
        # use the minimum readable size.
        if font_size < min_font_size:
            font_size = min_font_size
            font = self._load_font(font_size)

            text_bbox = draw.textbbox(
                (0, 0),
                value,
                font=font
            )

            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

        # Center text vertically inside the field
        x = bbox["left"] + horizontal_padding

        y = (
            bbox["top"]
            + (field_height - text_height) / 2
            - text_bbox[1]
        )

        draw.text(
            (x, y),
            value,
            font=font,
            fill="black"
        )

    def fill_field(self, image: Any, matched_field: MatchField, cells: list[Any] | None = None) -> None:
        value = self.resolve_value(matched_field)
        if not value:
            return

        value_bbox = matched_field.form_field.value_bbox
        if value_bbox is None:
            return

        if cells:
            self._draw_text_in_cells(image, value, cells)
            return

        pixel_bbox = self.bbox_to_pixels(value_bbox, image.width, image.height)
        self._draw_text(image, value, pixel_bbox)

    def fill_form(
        self,
        image: Any,
        matched_fields: list[MatchField],
        cell_boxes: list[Any] | None = None,
        extractor: Any | None = None,
    ) -> Any:
        for matched_field in matched_fields:
            field_bbox = matched_field.form_field.value_bbox
            if field_bbox is None:
                continue

            cells = []
            if cell_boxes and extractor:
                cells = extractor.get_reliable_cells_for_field(field_bbox, cell_boxes)

            self.fill_field(image, matched_field, cells)

        return image

    def fill(
        self,
        image,
        textract_result,
        matched_fields,
        identity_profile,
        checkbox_options=None
    ):
        self.set_profile(identity_profile)

        print("\n========== AUTOFILL VALUES ==========")

        for matched_field in matched_fields:

            value = self.resolve_value(matched_field)

            print(
                "Label:",
                matched_field.form_field.label,
                "| Canonical:",
                matched_field.canonical_field,
                "| Value:",
                value
            )

        print("====================================\n")

        # Your existing rendering logic
        filled_image = self.fill_form(
            image,
            matched_fields
        )
        if checkbox_options:
            self.fill_checkboxes(
                filled_image,
                checkbox_options
            )

        from pathlib import Path
        from uuid import uuid4

        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)

        output_path = (
            output_dir /
            f"filled_form_{uuid4().hex}.png"
        )

        filled_image.save(output_path)

        return str(output_path)

    def _draw_checkbox(
        self,
        image: Any,
        checkbox_bbox: dict[str, int]
    ) -> None:

        draw = ImageDraw.Draw(image)

        left = checkbox_bbox["left"]
        top = checkbox_bbox["top"]
        width = checkbox_bbox["width"]
        height = checkbox_bbox["height"]

        # Draw a check mark using two lines.
        # This avoids depending on a font containing the ✓ character.

        x1 = left + width * 0.20
        y1 = top + height * 0.52

        x2 = left + width * 0.43
        y2 = top + height * 0.75

        x3 = left + width * 0.80
        y3 = top + height * 0.25

        line_width = max(
            2,
            int(min(width, height) * 0.12)
        )

        draw.line(
            [(x1, y1), (x2, y2), (x3, y3)],
            fill="black",
            width=line_width
        )


    def _normalize_option(self, value: str) -> str:
        if not value:
            return ""

        value = value.lower().strip()

        # Remove common punctuation
        value = value.replace(":", "")
        value = value.replace(".", "")
        value = value.replace("-", " ")

        # Normalize spaces
        value = " ".join(value.split())

        return value

    def _should_select_checkbox(
        self,
        label: str,
        checkbox_options: dict[str, Any]
    ) -> bool:

        if not label:
            return False

        label_normalized = self._normalize_option(label)

        # Gender
        if self.profile and self.profile.gender:

            profile_gender = self._normalize_option(
                self.profile.gender
            )

            if label_normalized == profile_gender:
                return True

        return False

    def fill_checkboxes(
        self,
        image: Any,
        checkbox_options: list[dict[str, Any]]
    ) -> None:

        for option in checkbox_options:

            label = option.get("label", "")
            checkbox = option.get("checkbox")

            if not checkbox:
                continue

            if not self._should_select_checkbox(
                label,
                checkbox
            ):
                continue

            pixel_bbox = self.bbox_to_pixels(
                checkbox["bbox"],
                image.width,
                image.height
            )

            self._draw_checkbox(
                image,
                pixel_bbox
            )