import hashlib
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import RoleEnum, User
from app.models.paciente import Paciente


def _hash_cpf(cpf: str) -> str:
    return hashlib.sha256((cpf + settings.secret_salt).encode()).hexdigest()


def seed():
    db = SessionLocal()

    print("Inserindo usuários...")
    usuarios = [
        {
            "nome": "João Silva",
            "email": "medico@sfha.dev",
            "senha_hash": hash_password("senha123"),
            "role": RoleEnum.MEDICO,
        },
        {
            "nome": "Maria Santos",
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
            print(f"  Criado: {dados['email']} ({dados['role'].value})")
        else:
            print(f"  Já existe: {dados['email']}")

    db.commit()

    print("\nInserindo pacientes...")
    pacientes = [
        {
            "cpf": "11122233344",
            "nome": "Ana Silva",
            "data_nascimento": date(1995, 3, 15),
            "telefone": "47991234567",
            "estado_civil": "CASADA",
            "possui_filhos": True,
            "quantidade_filhos": 1,
            "altura_cm": 162,
        },
        {
            "cpf": "55566677788",
            "nome": "Maria Oliveira",
            "data_nascimento": date(1989, 7, 22),
            "telefone": "47998765432",
            "estado_civil": "SOLTEIRA",
            "possui_filhos": False,
            "quantidade_filhos": None,
            "altura_cm": 158,
        },
        {
            "cpf": "99988877766",
            "nome": "Julia Santos",
            "data_nascimento": date(2000, 11, 5),
            "telefone": "47993456789",
            "estado_civil": "UNIAO_ESTAVEL",
            "possui_filhos": False,
            "quantidade_filhos": None,
            "altura_cm": 165,
        },
    ]

    for dados in pacientes:
        cpf_hash = _hash_cpf(dados["cpf"])
        existente = db.query(Paciente).filter(Paciente.cpf_hash == cpf_hash).first()
        if not existente:
            p = Paciente(
                cpf_hash=cpf_hash,
                nome=dados["nome"],
                data_nascimento=dados["data_nascimento"],
                telefone=dados["telefone"],
                estado_civil=dados["estado_civil"],
                possui_filhos=dados["possui_filhos"],
                quantidade_filhos=dados["quantidade_filhos"],
                altura_cm=dados["altura_cm"],
            )
            db.add(p)
            print(f"  Criado: {dados['nome']}")
        else:
            print(f"  Já existe: {dados['nome']}")

    db.commit()
    db.close()
    print("\nSeed concluído com sucesso!")
    print("\nCredenciais de acesso:")
    print("  medico@sfha.dev      / senha123  → MEDICO")
    print("  enfermeiro@sfha.dev  / senha123  → ENFERMEIRO")
    print("  admin@sfha.dev       / senha123  → ADMIN")


if __name__ == "__main__":
    seed()
