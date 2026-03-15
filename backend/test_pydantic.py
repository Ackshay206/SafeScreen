from pydantic import BaseModel
from typing import Optional

class TestModel(BaseModel):
    ref: Optional[str]

try:
    m = TestModel(ref="hello")
    print(f"Success: {m}")
except Exception as e:
    print(f"Error: {e}")
