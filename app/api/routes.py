# app/api/routes.py
from fastapi import APIRouter, HTTPException, Body
from app.services.naming_service import NamingService
from app.services.maab_validator import MaabValidator
from pydantic import BaseModel

router = APIRouter()


class NameInput(BaseModel):
    name: str

'''

depricated endpoints - added in case if we have more formats and standards

@router.get("/formats")
def get_formats():
    return {"formats": ["abs"]}

@router.get("/standards")
def get_standards():
    return {"standards": []}

'''

@router.get("/fields")
def get_format_fields():
    # Only return fields from default service
    return NamingService().get_format_fields()


@router.post("/generate-variable-name")
async def gen_var_name(body: dict = Body(...)):
    """
    format and standard will be determined by default values in the service for now, as we are only supporting one format and standard. In future, we can add these as parameters in the request body and handle them accordingly in the service. For now, we will ignore these parameters
    without format and standard.
    """
    service = NamingService()
    return service.generate(body)


@router.post("/generate-options")
async def generate_options(body: dict = Body(...)):
    """
    Fetch abbreviation options for each word in the description
    and also return metadata for other fields.
    """
    description = body.get("description", "").strip()
    if not description:
        raise HTTPException(status_code=400, detail="Description is required.")

    service = NamingService()
    try:
        words_options = service.get_options_for_description(description)
        other_fields = service.get_format_fields().get("fields", {})
        return {
            "words_options": words_options.get("words_options", {}),
            "other_fields": other_fields
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch options: {str(e)}")



@router.get("/pending")
def get_pending():
    return NamingService().get_pending()


@router.post("/admin/actions")
async def admin_actions(body: dict = Body(...)):
    return NamingService().admin_action(body)


    # ---------------------------
    # MAAB Validation Endpoint
    # ---------------------------



@router.get("/components")
def get_components():
    return MaabValidator.get_components()


@router.post("/validate/{component}")
def validate_name(component: str, body: NameInput):
    try:
        validator = MaabValidator(component)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No rules found for component '{component}'")

    results = validator.validate(body.name)
    return {"component": component, "name": body.name, "results": results}



    # ---------------------------
    # stats endpoint
    # ---------------------------



@router.get("/stats")
def get_stats():
    return NamingService().get_stats()
