import boto3
import json
from pathlib import Path
from typing import Any

class TextractClient:
    def __init__(self):
        self.client = boto3.client("textract", region_name="us-east-1")

    def analyze_doc(self, input_path: str | Path) -> dict[str, Any]:
        with open(input_path, "rb") as f:
            image_bytes = f.read()

        return self.analyze_bytes(image_bytes)

    def analyze_bytes(self, image_bytes: bytes) -> dict[str, Any]:
        if not image_bytes:
            raise ValueError("Uploaded file is empty")

        response = self.client.analyze_document(
            Document={"Bytes": image_bytes},
            FeatureTypes=["FORMS", "TABLES"]
        )
        for block in response.get("Blocks", []):
            if block.get("BlockType") == "SELECTION_ELEMENT":
                print("\n========== CHECKBOX ==========")
                print("Status:", block.get("SelectionStatus"))
                print("Geometry:", block.get("Geometry"))
                print("==============================")
        return response

    async def extract(self, uploaded_file) -> dict[str, Any]:
        image_bytes = await uploaded_file.read()

        if hasattr(uploaded_file, "seek"):
            await uploaded_file.seek(0)

        return self.analyze_bytes(image_bytes)

    def save_response(self, response: dict[str, Any], input_path: str | Path, output_folder: str = "textractResponse") -> Path:
        form_name = Path(input_path).stem
        output_filename = f"textract_{form_name}.json"
        output_path = Path(output_folder) / output_filename

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(response, f, indent=4)

        print(f"Output saved to {output_path}")
        return output_path

if __name__ == "__main__":
    # Usage example
    client = TextractClient()
    input_path = "InputImages/doc1.jpeg"
    response = client.analyze_doc(input_path)
    client.save_response(response, input_path)


