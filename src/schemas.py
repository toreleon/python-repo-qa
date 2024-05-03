from pydantic import BaseModel, Field
from typing import List, Optional, Tuple

class Variable(BaseModel):
    name: str
    type: Optional[str]
    value: Optional[str]
    scope: str

class Function(BaseModel):
    name: str
    parameters: List[str]
    return_type: Optional[str]
    docstring: Optional[str]
    code_snippet: str
    line_number: int

class Class(BaseModel):
    name: str
    methods: List[Function] = []
    attributes: List[str] = []
    base_classes: List[str] = []
    docstring: Optional[str]
    is_abstract: bool

class Module(BaseModel):
    name: str
    functions: List[Function] = []
    classes: List[Class] = []
    variables: List[Variable] = []
    imported_modules: List[str] = []
    calls: List[Tuple[str, str]] = []  # List of tuples (caller, callee)
    inherits: List[Tuple[str, str]] = []  # List of tuples (subclass, superclass)
    uses: List[Tuple[str, str]] = []  # List of tuples (user, used)

class Package(BaseModel):
    name: str
    version: Optional[str]
    license: Optional[str]
