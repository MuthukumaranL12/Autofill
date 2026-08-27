from fastapi import APIRouter, UploadFile, File,Depends
from fastapi.responses import FileResponse
from bson import ObjectId

from backend.services.form_filling_service import FormFillingService
from backend.auth import get_authenticated_user_id
# from backend.form_pipeline.textract_service import TextractClient
# from backend.form_pipeline.field_extractor import FieldExtractor
# from backend.form_pipeline.semantics import SemanticMatcher
# from backend.form_pipeline.autofill import AutoFill


router = APIRouter(
    prefix="/api/forms",
    tags=["Forms"]
)


# textract_service = TextractClient()
# field_extractor = FieldExtractor()
# semantic_matcher = SemanticMatcher()
# autofill_service = AutoFill()


form_filling_service = FormFillingService()


@router.post("/fill")
async def fill_form(
    form: UploadFile = File(...),
    user_id:ObjectId=Depends(get_authenticated_user_id),
):

    output_path = await form_filling_service.fill(
        uploaded_file=form,
        user_id=user_id
    )

    return FileResponse(
        path=output_path,
        media_type="image/png",
        filename="filled_form.png"
    )