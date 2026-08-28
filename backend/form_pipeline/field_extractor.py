import re
from typing import Any

from backend.models.form_models import CellBox, FormField

MIN_BBOX_AREA = 0.00005

FIELD_KEYWORDS = {
    "email": {
        "email",
        "e-mail"
    },

    "phone": {
        "phone",
        "mobile",
        "telephone",
        "landline"
    },

    "date": {
        "date of birth",
        "dob",
        "birth date"
    },

    "photo": {
        "photo",
        "photograph"
    },

    "signature": {
        "signature"
    },

    "address_component": {
        "address",
        "street",
        "road",
        "house",
        "flat",
        "building",
        "landmark",
        "district",
        "city",
        "town",
        "village",
        "state"
    },

    "number": {
        "number",
        "pincode",
        "pin code"
    }
}

class FieldExtractor:
    def __init__(self, response: dict[str, Any]):
        self.response = response
        self.blocks, self.block_map = self._load_blocks(response)

    def extract_fields(self) -> list[FormField]:
        form_fields = []
        key_blocks = self._get_key_blocks(self.blocks)
        for block in key_blocks:
            label = self._get_text(block)

            normalized_label = self._normalize_label(label)

            value_block = self._get_value_block(block)

            value = self._get_text(value_block)

            label_bbox = self._get_bbox(block)

            value_bbox = self._get_bbox(value_block)

            field_type = self._classify_field(normalized_label)

            field = FormField(
                label=label,
                normalized_label=normalized_label,
                value=value,
                label_bbox=label_bbox,
                value_bbox=value_bbox,
                confidence=block.get("Confidence", 0),
                field_type=field_type,
                source="form"
            )

            if self._is_valid_field(field):
                form_fields.append(field)

        return form_fields

    # Backward-compatible alias expected by service layer.
    def extract(self) -> list[FormField]:
        return self.extract_fields()


    def _load_blocks(self, response: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        blocks = response.get("Blocks", [])
        block_map = {block["Id"]: block for block in blocks if "Id" in block}

        return blocks, block_map

    def _get_key_blocks(self, blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        key_blocks=[]
        for block in blocks:
            if block.get("BlockType")=="KEY_VALUE_SET" and "KEY" in block.get("EntityTypes",[]):
                key_blocks.append(block)

        return key_blocks

    def _get_text(self, block: dict[str, Any] | None) -> str:
        if not block or not block.get('Relationships'):
            return ""

        words=[]
        for rel in block["Relationships"]:
            if rel["Type"]!="CHILD":
                continue
            for cid in rel["Ids"]:
                child=self.block_map.get(cid)

                if not child:
                    continue

                if child["BlockType"]=="WORD":
                    words.append(child["Text"])

        return " ".join(words)

    def _get_value_block(self, block: dict[str, Any]) -> dict[str, Any] | None:

        value_id=None
        for rel in block.get("Relationships",[]):
            if rel["Type"]=="VALUE":
                value_id=rel["Ids"][0]
                break

        value_block=self.block_map.get(value_id) if value_id else None

        return value_block

    def _get_bbox(self, block: dict[str, Any] | None) -> dict[str, float] | None:
        if not block:
            return None

        geometry = block.get("Geometry") or {}
        bbox = geometry.get("BoundingBox")

        if not bbox:
            return None   

        return{
        "left": bbox["Left"],
        "top": bbox["Top"],
        "width": bbox["Width"],
        "height": bbox["Height"]
        }
    
    def _bbox_area(self, bbox: dict[str, float]) -> float:
        return bbox["width"] * bbox["height"]

    
    def _is_valid_field(self,field:FormField)->bool:
        if not field.label.strip():
            return False

        if not field.value_bbox:
            return False

        if self._bbox_area(field.value_bbox)<MIN_BBOX_AREA:
            return False

        return True

    def _normalize_label(self,label:str)->str:
        label=label.strip()

        unwanted_punc="*#"
        label=label.translate(str.maketrans("","",unwanted_punc))

        label=re.sub(r'\s+',' ',label)

        return label

    def _classify_field(self, label: str) -> str:
        label = label.lower()

        if any(keyword in label for keyword in FIELD_KEYWORDS["photo"]):
            return "photo"

        if any(keyword in label for keyword in FIELD_KEYWORDS["signature"]):
            return "signature"

        if any(keyword in label for keyword in FIELD_KEYWORDS["email"]):
            return "email"

        if any(keyword in label for keyword in FIELD_KEYWORDS["phone"]):
            return "phone"

        if any(keyword in label for keyword in FIELD_KEYWORDS["date"]):
            return "date"

        if any(keyword in label for keyword in FIELD_KEYWORDS["address_component"]):
            return "address_component"

        if any(keyword in label for keyword in FIELD_KEYWORDS["number"]):
            return "number"

        return "text"

    def _get_cell_blocks(self) -> list[dict]:
        cells = []

        for block in self.blocks:
            if block.get("BlockType") == "CELL":
                cells.append(block)

        return cells

    def _get_cell_bbox(self, cell: dict) -> dict[str,float] | None:

        geometry = cell.get("Geometry")

        if not geometry:
            return None

        bbox = geometry.get("BoundingBox")

        if not bbox:
            return None

        return {
        "left": bbox["Left"],
        "top": bbox["Top"],
        "width": bbox["Width"],
        "height": bbox["Height"]
    }

    def extract_cell_box(self) -> list[CellBox]:

        cells = self._get_cell_blocks()

        cell_boxes = []

        for cell in cells:

            bbox = self._get_cell_bbox(cell)

            if bbox is None:
                continue

            cell_box = CellBox(
                row=cell.get("RowIndex", 0),
                column=cell.get("ColumnIndex", 0),
                bbox=bbox
            )

            cell_boxes.append(cell_box)

        return cell_boxes

    # Backward-compatible alias with pluralized naming.
    def extract_cell_boxes(self) -> list[CellBox]:
        return self.extract_cell_box()

    def _cell_overlap_ratio(self, cell_bbox, field_bbox):

        cell_left = cell_bbox["left"]
        cell_top = cell_bbox["top"]
        cell_right = cell_left + cell_bbox["width"]
        cell_bottom = cell_top + cell_bbox["height"]

        field_left = field_bbox["left"]
        field_top = field_bbox["top"]
        field_right = field_left + field_bbox["width"]
        field_bottom = field_top + field_bbox["height"]

        intersection_left = max(cell_left, field_left)
        intersection_top = max(cell_top, field_top)
        intersection_right = min(cell_right, field_right)
        intersection_bottom = min(cell_bottom, field_bottom)

        if (
            intersection_right <= intersection_left
            or intersection_bottom <= intersection_top
        ):
            return 0.0

        intersection_area = (
            intersection_right - intersection_left
        ) * (
            intersection_bottom - intersection_top
        )

        cell_area = (
            cell_bbox["width"] *
            cell_bbox["height"]
        )

        if cell_area == 0:
            return 0.0

        return intersection_area / cell_area

    def _sort_cells(self, cells):

        return sorted(
            cells,
            key=lambda cell: (
                cell.row,
                cell.column
            )
        )
        
    def get_cells_for_field(self, field_bbox, cell_boxes):

        if field_bbox is None or not cell_boxes:
            return []

        matched_cells = []

        for cell in cell_boxes:

            overlap = self._cell_overlap_ratio(
                cell.bbox,
                field_bbox
            )

            if overlap >= 0.5:
                matched_cells.append(cell)

        return self._sort_cells(matched_cells)


    def get_reliable_cells_for_field(self, field_bbox, cell_boxes):

        cells = self.get_cells_for_field(
            field_bbox,
            cell_boxes
        )

        if len(cells) < 2:
            return []

        # Check that cells are arranged consistently
        widths = [cell.bbox["width"] for cell in cells]
        heights = [cell.bbox["height"] for cell in cells]

        avg_width = sum(widths) / len(widths)
        avg_height = sum(heights) / len(heights)

        if avg_width == 0 or avg_height == 0:
            return []

        width_variation = max(widths) / min(widths)
        height_variation = max(heights) / min(heights)

        # Reject highly inconsistent cells
        if width_variation > 2.0:
            return []

        if height_variation > 2.0:
            return []

        return cells


    def get_selection_elements(self) -> list[dict[str, Any]]:
        """
        Return all checkbox/radio selection elements detected by Textract.
        """
        selection_elements = []

        for block in self.blocks:
            if block.get("BlockType") != "SELECTION_ELEMENT":
                continue

            bbox = self._get_bbox(block)

            if bbox is None:
                continue

            selection_elements.append({
                "id": block.get("Id"),
                "status": block.get("SelectionStatus"),
                "bbox": bbox
            })

        return selection_elements

    def get_checkbox_options(
        self,
        selection_elements: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Associate each Textract checkbox with the nearest WORD.

        The label may appear either:
            Male [checkbox]
        or:
            [checkbox] Male

        Therefore both left and right sides are checked.
        """

        options = []

        # Collect all WORD blocks
        word_blocks = []

        for block in self.blocks:

            if block.get("BlockType") != "WORD":
                continue

            bbox = self._get_bbox(block)

            if bbox is None:
                continue

            word_blocks.append({
                "text": block.get("Text", ""),
                "bbox": bbox
            })

        for checkbox in selection_elements:

            checkbox_bbox = checkbox["bbox"]

            checkbox_left = checkbox_bbox["left"]
            checkbox_right = (
                checkbox_left
                + checkbox_bbox["width"]
            )

            checkbox_center_y = (
                checkbox_bbox["top"]
                + checkbox_bbox["height"] / 2
            )

            candidates = []

            for word in word_blocks:

                word_bbox = word["bbox"]

                word_left = word_bbox["left"]
                word_right = (
                    word_left
                    + word_bbox["width"]
                )

                word_center_y = (
                    word_bbox["top"]
                    + word_bbox["height"] / 2
                )

                # ---------------------------------
                # Vertical alignment
                # ---------------------------------

                vertical_distance = abs(
                    word_center_y
                    - checkbox_center_y
                )

                max_vertical_distance = max(
                    checkbox_bbox["height"] * 2,
                    word_bbox["height"] * 1.5
                )

                if vertical_distance > max_vertical_distance:
                    continue

                # ---------------------------------
                # Word is LEFT of checkbox
                # Example:
                #
                # Male [□]
                # ---------------------------------

                if word_right <= checkbox_left:

                    horizontal_distance = (
                        checkbox_left
                        - word_right
                    )

                    if horizontal_distance <= 0.08:

                        distance = (
                            horizontal_distance
                            + vertical_distance
                        )

                        candidates.append(
                            (
                                distance,
                                "left",
                                word
                            )
                        )

                # ---------------------------------
                # Word is RIGHT of checkbox
                # Example:
                #
                # [□] Male
                # ---------------------------------

                elif word_left >= checkbox_right:

                    horizontal_distance = (
                        word_left
                        - checkbox_right
                    )

                    if horizontal_distance <= 0.08:

                        distance = (
                            horizontal_distance
                            + vertical_distance
                        )

                        candidates.append(
                            (
                                distance,
                                "right",
                                word
                            )
                        )

            if not candidates:
                continue

            # ---------------------------------
            # Select closest word
            # ---------------------------------

            candidates.sort(
                key=lambda item: item[0]
            )

            nearest_word = candidates[0][2]

            options.append({
                "checkbox": checkbox,
                "label": nearest_word["text"].strip()
            })

        return options


