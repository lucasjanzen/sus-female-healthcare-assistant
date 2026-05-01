"""
Placeholder para tarefas futuras relacionadas a consultas.

O Celery Beat pode continuar configurado no projeto, mas a lógica de timeout
foi removida junto com o fluxo anterior.
"""


def encerrar_consultas_timeout() -> int:
    return 0


try:
    from celery import shared_task  # type: ignore

    @shared_task(name="app.tasks.consulta_timeout.encerrar_consultas_timeout")
    def encerrar_consultas_timeout_task() -> int:
        return encerrar_consultas_timeout()

except ImportError:
    pass
