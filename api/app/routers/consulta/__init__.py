from fastapi import APIRouter

from .atendimento import router as atendimento_router
from .encerramento import router as encerramento_router
from .triagem import router as triagem_router

router = APIRouter()
router.include_router(triagem_router)
router.include_router(atendimento_router)
router.include_router(encerramento_router)
