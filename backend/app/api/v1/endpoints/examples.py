from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.application.example_usecase import ExampleUseCase
from app.core.database import get_db
from app.infrastructure.repositories.example_repository import ExampleRepository
from app.schemas.example import ExampleCreate, ExampleResponse

router = APIRouter()


@router.post("/", response_model=ExampleResponse, status_code=201)
def create_example(data: ExampleCreate, db: Session = Depends(get_db)):
    """サンプル作成"""
    repository = ExampleRepository(db)
    usecase = ExampleUseCase(repository)
    example = usecase.create_example(data)
    return example


@router.get("/{example_id}", response_model=ExampleResponse)
def get_example(example_id: int, db: Session = Depends(get_db)):
    """サンプル取得"""
    repository = ExampleRepository(db)
    usecase = ExampleUseCase(repository)
    example = usecase.get_example(example_id)
    if example is None:
        raise HTTPException(status_code=404, detail="Example not found")
    return example


@router.get("/", response_model=list[ExampleResponse])
def list_examples(db: Session = Depends(get_db)):
    """サンプル一覧"""
    repository = ExampleRepository(db)
    usecase = ExampleUseCase(repository)
    examples = usecase.list_examples()
    return examples
