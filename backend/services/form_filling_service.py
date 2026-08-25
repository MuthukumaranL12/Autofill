from io import BytesIO

from PIL import Image

from backend.models.identity_profile import IdentityProfile
from backend.profile.profile_repository import ProfileRepository
from backend.security.decryption import decrypt_field

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
            identity_profile=identity_profile
        )

        return output_path

    def _build_identity_profile(self, profile):

        return IdentityProfile(
            name=decrypt_field(
                profile.get("name_enc")
            ),

            dob=decrypt_field(
                profile.get("dob_enc")
            ),

            address=decrypt_field(
                profile.get("address_enc")
            ),

            guardian_name=decrypt_field(
                profile.get("guardian_name_enc")
            ),

            place_of_birth=decrypt_field(
                profile.get("place_of_birth_enc")
            ),

            gender=profile.get("gender") or "",

            year_of_birth=profile.get(
                "year_of_birth"
            ),

            aadhaar_number=profile.get(
                "aadhaar_token"
            ),

            voter_id=profile.get(
                "voter_id_token"
            ),

            birth_registration_number=profile.get(
                "birth_reg_token"
            )
        )