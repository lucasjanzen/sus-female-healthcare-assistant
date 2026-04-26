"""
Job para encerramento automático de consultas inativas.

Configuração Celery Beat (celery_app.py):
    app.conf.beat_schedule = {
        "encerrar-consultas-timeout": {
            "task": "app.tasks.consulta_timeout.encerrar_consultas_timeout",
            "schedule": crontab(minute="*/15"),  # a cada 15 min
        },
    }

Pode também ser executado diretamente via script ou cron do sistema:
    python -c "from app.tasks.consulta_timeout import encerrar_consultas_timeout; encerrar_consultas_timeout()"
"""

from datetime import datetime, timedelta, timezone

from app.db.session import SessionLocal
from app.models.consulta import ConsultaIdentidade

TIMEOUT_HORAS = 4


def encerrar_consultas_timeout() -> int:
    """Encerra consultas ABERTA/EM_ATENDIMENTO abertas há mais de 4 horas.

    Retorna o número de consultas encerradas.
    """
    limite = datetime.now(timezone.utc) - timedelta(hours=TIMEOUT_HORAS)

    with SessionLocal() as db:
        consultas = (
            db.query(ConsultaIdentidade)
            .filter(
                ConsultaIdentidade.status.in_(["ABERTA", "EM_ATENDIMENTO"]),
                ConsultaIdentidade.aberta_em < limite,
            )
            .all()
        )

        if not consultas:
            return 0

        agora = datetime.now(timezone.utc)
        for consulta in consultas:
            consulta.status = "ENCERRADA"
            consulta.encerrada_em = agora

        db.commit()
        return len(consultas)


# Registro Celery (opcional — requer celery instalado)
try:
    from celery import shared_task  # type: ignore

    @shared_task(name="app.tasks.consulta_timeout.encerrar_consultas_timeout")
    def encerrar_consultas_timeout_task() -> int:
        return encerrar_consultas_timeout()

except ImportError:
    pass
