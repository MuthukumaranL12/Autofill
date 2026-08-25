from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from backend.form_pipeline.autofill import AutoFill
from backend.form_pipeline.field_extractor import FieldExtractor
from backend.form_pipeline.semantics import SemanticMatcher
from backend.form_pipeline.textract_service import TextractClient
from backend.models.identity_profile import IdentityProfile


def main() -> None:
    input_image = Path("InputImages/form5.jpg")
    textract_dump = Path("textractResponse/textract_form5.json")

    if textract_dump.exists():
        response = json.loads(textract_dump.read_text(encoding="utf-8"))
    elif input_image.exists():
        client = TextractClient()
        response = client.analyze_doc(input_image)
        client.save_response(response, input_image)
    else:
        raise FileNotFoundError("Neither textract response JSON nor input image was found")

    extractor = FieldExtractor(response=response)
    fields = extractor.extract_fields()
    cell_boxes = extractor.extract_cell_box()

    matcher = SemanticMatcher()
    matches = matcher.match(fields=fields)

    profile = IdentityProfile(
        name="Abhiram Raghunand",
        gender="MALE",
        dob="26/11/2004",
        guardian_name="Guardian Name",
        address="Example Street, Bengaluru, Karnataka 560094",
        place_of_birth="Bengaluru",
        year_of_birth="2004",
    )

    if not input_image.exists():
        print("No source image available. Printing matched fields only.")
        for match in matches:
            print(match)
        return

    image = Image.open(input_image)

    autofill = AutoFill()
    autofill.set_profile(profile)

    filled_image = autofill.fill_form(
        image=image,
        matched_fields=matches,
        cell_boxes=cell_boxes,
        extractor=extractor,
    )

    output_path = Path("outputImages/filled_form5.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filled_image.save(output_path)

    print(f"Form filled successfully: {output_path}")


if __name__ == "__main__":
    main()
