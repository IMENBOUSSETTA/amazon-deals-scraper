from typing import Any, Dict
def build_filters(q=None, category=None, brand=None, min_price=None, max_price=None,
                  min_discount=None, min_rating=None) -> Dict[str, Any]:
    filters: Dict[str, Any] = {}
    if q: filters["$text"] = {"$search": q}
    if category: filters["category"] = {"$regex": f"^{category}$", "$options": "i"}
    if brand: filters["brand"] = {"$regex": f"^{brand}$", "$options": "i"}
    if min_price is not None or max_price is not None:
        rng = {}
        if min_price is not None: rng["$gte"] = float(min_price)
        if max_price is not None: rng["$lte"] = float(max_price)
        filters["price"] = rng
    if min_discount is not None: filters["discount_pct"] = {"$gte": float(min_discount)}
    if min_rating is not None: filters["rating"] = {"$gte": float(min_rating)}
    return filters
SORT_FIELDS = {"price": "price", "discount": "discount_pct", "rating": "rating"}