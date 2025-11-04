# app/api/routes.py
from fastapi import APIRouter, HTTPException, Request, Body
from app.services.naming_service import NamingService
from app.services.maab_validator import MaabValidator
import os
import json
from pydantic import BaseModel
from fastapi.responses import JSONResponse

router = APIRouter()

class AbsVariableInput(BaseModel):
    module: str
    data_type: str
    data_size: str
    unit: str
    description: str

class NameInput(BaseModel):
    name: str

# helper funcs
def load_json(path: str):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_json(path: str, data: dict):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

@router.get("/formats")
def get_formats():
    naming_service = NamingService()
    naming_service.update_endpoint_count("/formats")
    base_path = os.path.join(os.getcwd(), "data/naming_conventions")
    formats = {}
    if not os.path.exists(base_path):
        return formats
    for fmt in os.listdir(base_path):
        fmt_path = os.path.join(base_path, fmt, "format.json")
        if os.path.exists(fmt_path):
            try:
                with open(fmt_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                formats[fmt] = config.get("fields", [])
            except Exception:
                formats[fmt] = []
    return formats

@router.get("/standards")
def get_standards():
    naming_service = NamingService()
    naming_service.update_endpoint_count("/standards")
    base_path = os.path.join(os.getcwd(), "data/standards")
    if not os.path.exists(base_path):
        return {"standards": []}
    try:
        return {"standards": os.listdir(base_path)}
    except Exception:
        return {"standards": []}

@router.get("/fields/{format}")
def get_format_fields(format: str):
    naming_service = NamingService()
    endpoint = f"/fields/{format}" 
    naming_service.update_endpoint_count(endpoint)
    base_path = os.path.join(os.getcwd(), f"data/naming_conventions/{format}")
    format_path = os.path.join(base_path, "format.json")
    if not os.path.exists(format_path):
        raise HTTPException(status_code=404, detail="Format not found")
    try:
        with open(format_path, "r", encoding="utf-8") as f:
            format_config = json.load(f)
    except Exception:
        raise HTTPException(status_code=500, detail="Error reading format config")
    fields = format_config.get("fields", [])
    response = {}
    for field in fields:
        options_file = os.path.join(base_path, f"{field}s.json")
        if os.path.exists(options_file):
            try:
                with open(options_file, "r", encoding="utf-8") as f:
                    options_data = json.load(f)
                response[field] = {"type": "select", "options": list(options_data.keys())}
            except Exception:
                response[field] = {"type": "string", "description": f"Enter {field}"}
        else:
            response[field] = {"type": "string", "description": f"Enter {field}"}
    return {"format": format, "fields": response}

@router.post("/generate-variable-name/{format}/{standard}")
async def gen_var_name(format: str, standard: str, request: Request):
    naming_service = NamingService()
    endpoint = f"/generate-variable-name/{format}/{standard}" 
    naming_service.update_endpoint_count(endpoint)
    try:
        user_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid input format. Must be JSON.")

    service = NamingService(format=format, standard=standard)
    try:
        result = service.gen_var_name(**user_data)
    except KeyError as e:
        raise HTTPException(status_code=422, detail=f"Missing required field: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating name: {e}")

    variable_name = result.get("variable_name") if isinstance(result, dict) else result
    autosar_matches = result.get("autosar_matches", []) if isinstance(result, dict) else []

    # Save to pending.json (preserve prior behaviour)
    pending_path = os.path.join(os.getcwd(), f"data/standards/{standard}/pending.json")
    pending = load_json(pending_path)
    pending[variable_name] = user_data.get("description", "")
    save_json(pending_path, pending)

    return {"variable_name": variable_name, "autosar_matches": autosar_matches, "status": "pending"}

@router.get("/pending/{standard}")
def get_pending_variables(standard: str):
    naming_service = NamingService()
    endpoint = f"/pending/{standard}" 
    naming_service.update_endpoint_count(endpoint)
    pending_path = os.path.join(os.getcwd(), f"data/standards/{standard}/pending.json")
    return load_json(pending_path)

@router.post("/admin/actions/{standard}")
async def admin_actions(standard: str, data: dict = Body(...)):
    naming_service = NamingService()
    endpoint = f"/admin/actions/{standard}" 
    naming_service.update_endpoint_count(endpoint)
    variables = data.get("variables", [])
    action = data.get("action", "")
    service = NamingService(standard=standard)
    if action == "approve":
        approved_items = service._approve_pending_abbreviations(standard, variables)
        if approved_items:
            return {"status": "approved", "approved": approved_items}
        else:
            return {"status": "error", "message": "No variables approved"}
    elif action == "delete":
        service._delete_pending_abbreviations(standard, variables)
        return {"status": "deleted", "deleted": variables}
    else:
        return {"status": "error", "message": "Invalid action"}

@router.get("/components")
def get_components():
    naming_service = NamingService()
    naming_service.update_endpoint_count("/components")
    base_path = os.path.join(os.getcwd(), "data", "maab")
    components_path = os.path.join(base_path, "components.json")
    if not os.path.exists(components_path):
        raise HTTPException(status_code=404, detail="components.json not found")
    try:
        with open(components_path, "r", encoding="utf-8") as f:
            components = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading components: {e}")
    return JSONResponse(content={"standards": components})

@router.post("/validate/{component}")
def validate_name(component: str, body: NameInput):
    naming_service = NamingService()
    endpoint = f"/validate/{component}" 
    naming_service.update_endpoint_count("endpoint")
    name = body.name
    try:
        validator = MaabValidator(component)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No rules found for component '{component}'")
    results = validator.validate(name)
    return {"component": component, "name": name, "results": results}
