import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models.user import RoleEnum, User


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    usuarios = [
        {
            "nome": "Dr. João Silva",
            "email": "medico@sfha.dev",
            "senha_hash": hash_password("senha123"),
            "role": RoleEnum.MEDICO,
        },
        {
            "nome": "Enf. Maria Santos",
            "email": "enfermeiro@sfha.dev",
            "senha_hash": hash_password("senha123"),
            "role": RoleEnum.ENFERMEIRO,
        },
        {
            "nome": "Admin Sistema",
            "email": "admin@sfha.dev",
            "senha_hash": hash_password("senha123"),
            "role": RoleEnum.ADMIN,
        },
    ]

    for dados in usuarios:
        existente = db.query(User).filter(User.email == dados["email"]).first()
        if not existente:
            db.add(User(**dados))
            print(f"Criado: {dados['email']} ({dados['role'].value})")
        else:
            print(f"Já existe: {dados['email']}")

    db.commit()
    db.close()
    print("\nSeed concluído com sucesso!")


if __name__ == "__main__":
    seed()
