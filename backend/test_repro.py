from pydantic import BaseModel
from typing import Optional

class RecommendationResponse(BaseModel):
    recommendations  : list
    candidates_count : int
    reference_film   : Optional[str]
    mode             : str

try:
    r = RecommendationResponse(
        recommendations  = [],
        candidates_count = 0,
        reference_film   = "test",
        mode             = "test"
    )
    print(f"Success: {r}")
except Exception as e:
    print(f"Error type: {type(e)}")
    print(f"Error message: {e}")
