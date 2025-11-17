import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Category, AffiliateProduct, Click

app = FastAPI(title="Affiliate Coffee Gear API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_doc(doc):
    d = dict(doc)
    if d.get("_id"):
        d["id"] = str(d.pop("_id"))
    # convert any ObjectId inside nested fields if present
    for k, v in list(d.items()):
        if isinstance(v, ObjectId):
            d[k] = str(v)
    return d


@app.get("/")
def read_root():
    return {"message": "Affiliate Coffee Gear API is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            response["connection_status"] = "Connected"
            collections = db.list_collection_names()
            response["collections"] = collections[:10]
            response["database"] = "✅ Connected & Working"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# Category endpoints
@app.post("/api/categories", response_model=dict)
def create_category(payload: Category):
    # ensure slug unique
    existing = db["category"].find_one({"slug": payload.slug}) if db else None
    if existing:
        raise HTTPException(status_code=400, detail="Category slug already exists")
    inserted_id = create_document("category", payload)
    return {"id": inserted_id}


@app.get("/api/categories")
def list_categories():
    docs = get_documents("category", {}, None)
    # sort by name
    docs = sorted(docs, key=lambda x: x.get("name", ""))
    return [serialize_doc(d) for d in docs]


# Product endpoints
@app.post("/api/products", response_model=dict)
def create_product(payload: AffiliateProduct):
    # optional: validate category exists
    if payload.category:
        cat = db["category"].find_one({"slug": payload.category}) if db else None
        if not cat:
            raise HTTPException(status_code=400, detail="Category not found")
    inserted_id = create_document("affiliateproduct", payload)
    return {"id": inserted_id}


@app.get("/api/products")
def list_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    featured: Optional[bool] = None,
    limit: Optional[int] = Query(default=None, ge=1, le=100)
):
    filt = {}
    if category:
        filt["category"] = category
    if featured is not None:
        filt["featured"] = featured
    if search:
        # basic case-insensitive regex match on title, description, tags
        filt["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}},
        ]
    docs = get_documents("affiliateproduct", filt, limit)
    # simple order: featured first, then title
    docs.sort(key=lambda x: (not x.get("featured", False), x.get("title", "")))
    return [serialize_doc(d) for d in docs]


# Click tracking + redirect
@app.post("/api/clicks", response_model=dict)
def record_click(payload: Click):
    inserted_id = create_document("click", payload)
    return {"id": inserted_id}


@app.get("/r/{product_id}")
def redirect_to_affiliate(product_id: str, source: Optional[str] = None):
    doc = db["affiliateproduct"].find_one({"_id": ObjectId(product_id)}) if db else None
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    # record click
    try:
        create_document("click", {"product_id": product_id, "source": source or "direct"})
    except Exception:
        pass
    return RedirectResponse(url=doc.get("affiliate_url"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
