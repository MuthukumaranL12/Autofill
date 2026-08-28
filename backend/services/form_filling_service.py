from io import BytesIO

from PIL import Image

from backend.models.identity_profile import IdentityProfile
from backend.repositories.profile_repository import ProfileRepository
# from backend.security.decryption import decrypt_field

from backend.form_pipeline.textract_service import TextractClient
from backend.form_pipeline.field_extractor import FieldExtractor
from backend.form_pipeline.semantics import SemanticMatcher
from backend.form_pipeline.autofill import AutoFill


class FormFillingService:

    def __init__(self):

        self.textract_service = TextractClient()
        self.semantic_matcher = SemanticMatcher()
        self.autofill_service = AutoFill()

        self.profile_repository = ProfileRepository()

    async def fill(self, uploaded_file, user_id):

        # 1. Existing Textract pipeline
        textract_result = await self.textract_service.extract(
            uploaded_file
        )

        # 2. Reset file because Textract already read it
        await uploaded_file.seek(0)

        # 3. Read original image for AutoFill
        image_bytes = await uploaded_file.read()

        image = Image.open(
            BytesIO(image_bytes)
        ).convert("RGB")

        # 4. Existing FieldExtractor interface
        field_extractor = FieldExtractor(
            textract_result
        )

        detected_fields = field_extractor.extract()

       
        # ---------------------------------------
        # Detect checkbox / selection elements
        # ---------------------------------------

        selection_elements = (
            field_extractor.get_selection_elements()
        )

        checkbox_options = (
            field_extractor.get_checkbox_options(
                selection_elements
            )
        )

        # ---------------------------------------
        # Remove checkbox labels from normal
        # semantic field matching
        # ---------------------------------------

        checkbox_labels = {
            option["label"].strip().lower()
            for option in checkbox_options
            if option.get("label")
        }

        detected_fields = [
            field
            for field in detected_fields
            if field.label.strip().lower()
            not in checkbox_labels
        ]

        print("\n========== CHECKBOX OPTIONS ==========")

        for option in checkbox_options:
            print(
                "Checkbox:",
                option["checkbox"]["status"],
                "| Label:",
                option["label"],
                "| BBox:",
                option["checkbox"]["bbox"]
            )

        print("======================================\n")

        # 5. Existing semantic matching
        matched_fields = self.semantic_matcher.match(
            detected_fields
        )

        print("\n========== MATCHED FIELDS ==========")

        for field in matched_fields:
            print(
                "Form label:",
                field.form_field.label,
                "| Canonical:",
                field.canonical_field,
                "| Score:",
                field.similarity_score
            )

        print("====================================\n")

        # 6. Retrieve profile
        profile_doc = self.profile_repository.get_by_user_id(
            user_id
        )

        # 7. Build identity profile
        identity_profile = self._build_identity_profile(
            profile_doc
        )

        print("\n========== DECRYPTED IDENTITY PROFILE ==========")

        print("Name:", identity_profile.name)
        print("DOB:", identity_profile.dob)
        print("Address:", identity_profile.address)
        print("Guardian Name:", identity_profile.guardian_name)
        print("Place of Birth:", identity_profile.place_of_birth)
        print("Gender:", identity_profile.gender)
        print("Year of Birth:", identity_profile.year_of_birth)
        print("Aadhaar Number:", identity_profile.aadhaar_number)
        print("Voter ID:", identity_profile.voter_id)
        print(
            "Birth Registration Number:",
            identity_profile.birth_registration_number
        )

        print("================================================\n")

        # 8. AutoFill
        output_path = self.autofill_service.fill(
            image=image,
            textract_result=textract_result,
            matched_fields=matched_fields,
            identity_profile=identity_profile,
            checkbox_options=checkbox_options
        )

        return output_path

    def _build_identity_profile(self, profile):

        identity_profile = IdentityProfile(

            name=profile.get("name", ""),

            first_name=profile.get(
                "first_name", ""
            ),

            middle_name=profile.get(
                "middle_name", ""
            ),

            last_name=profile.get(
                "last_name", ""
            ),

            phone=profile.get(
                "phone",""
            ),

            dob=profile.get(
                "dob", ""
            ),

            address=profile.get(
                "address", ""
            ),

            house_number=profile.get(
                "house_number", ""
            ),

            street=profile.get(
                "street", ""
            ),

            locality=profile.get(
                "locality", ""
            ),

            city=profile.get(
                "city", ""
            ),

            state=profile.get(
                "state", ""
            ),

            pincode=profile.get(
                "pincode", ""
            ),

            guardian_name=profile.get(
                "guardian_name", ""
            ),

            place_of_birth=profile.get(
                "place_of_birth", ""
            ),

            gender=profile.get(
                "gender", ""
            ),

            year_of_birth=profile.get(
                "year_of_birth", ""
            ),

            aadhaar_number=profile.get(
                "aadhaar_number", ""
            ),

            voter_id=profile.get(
                "voter_id", ""
            ),

            birth_registration_number=profile.get(
                "birth_registration_number", ""
            ),
        )

        return identity_profile