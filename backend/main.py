from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import shutil
import os
import uuid

from analyzer import ImageAnalyzer
from matcher import FurnitureMatcher

app = FastAPI(
    title="Room Furniture AI",
    description="AI-powered room analysis and furniture recommendation API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
FURNITURE_DIR = os.path.join(BASE_DIR, "data", "furniture")

os.makedirs(UPLOAD_DIR, exist_ok=True)

analyzer = ImageAnalyzer()
matcher = FurnitureMatcher(FURNITURE_DIR)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.post("/analyze", summary="Analyze room image", description="Upload a room image and get AI analysis with furniture recommendations")
async def analyze_room(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        analysis = analyzer.analyze(filepath)
        result = matcher.match(analysis)
        result["dominant_colors"] = analysis.get("dominant_colors", {})
        result["lighting_analysis"] = analysis.get("lighting_analysis", {})
        result["composition"] = analysis.get("composition", {})
        result["room_type"] = analysis.get("room_type", [])
        result["materials"] = analysis.get("materials", [])
        result["mood"] = analysis.get("mood", [])
        result["furniture_present"] = analysis.get("furniture_present", [])
        result["summary"] = analysis.get("summary", {})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/furniture", summary="List all furniture", description="Get complete furniture catalog")
async def list_furniture():
    return matcher.furniture_items

@app.get("/furniture/{item_id}", summary="Get furniture by ID", description="Get specific furniture item details")
async def get_furniture(item_id: str):
    for item in matcher.furniture_items:
        if item.get("id") == item_id:
            return item
    raise HTTPException(status_code=404, detail="Furniture not found")

@app.get("/docs-info", summary="API Documentation for Flutter Team")
async def api_docs():
    return {
        "api_base_url": "http://YOUR_IP:8001",
        "endpoints": {
            "POST /analyze": {
                "description": "Upload room image for AI analysis",
                "content_type": "multipart/form-data",
                "parameter": "file (image file)",
                "response_example": {
                    "status": "success",
                    "room_analysis": {
                        "style": "modern minimalist room",
                        "color_palette": "neutral room with white beige gray",
                        "lighting": "bright naturally lit room",
                        "space": "large spacious room"
                    },
                    "recommended_furniture": [
                        {
                            "id": "sofa-001",
                            "name": "Modern Grey Sofa",
                            "type": "sofa",
                            "style": "modern minimalist",
                            "colors": ["grey", "white"],
                            "size": "large",
                            "price": 899,
                            "model_url": "/models/sofa-001.glb",
                            "thumbnail": "/thumbs/sofa-001.jpg",
                            "dimensions": {"width": 2.2, "height": 0.9, "depth": 0.95},
                            "tags": ["modern", "minimalist", "neutral", "large space"],
                            "match_score": 70
                        }
                    ]
                }
            },
            "GET /furniture": {
                "description": "Get all furniture items",
                "response": "Array of furniture objects"
            },
            "GET /furniture/{id}": {
                "description": "Get specific furniture by ID",
                "response": "Single furniture object"
            }
        },
        "furniture_fields": {
            "id": "Unique identifier",
            "name": "Display name",
            "type": "Category (sofa, chair, table, lamp, shelf, rug, decor)",
            "style": "Design style",
            "colors": "Array of color names",
            "size": "small, medium, large",
            "price": "Price in dollars",
            "model_url": "Path to 3D model file (GLB format)",
            "thumbnail": "Path to thumbnail image",
            "dimensions": "Object with width, height, depth in meters",
            "tags": "Array of descriptive tags",
            "match_score": "AI match score (0-100)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
