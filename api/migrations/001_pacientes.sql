-- Migration 001: tabelas de pacientes, log e peso por consulta
-- Banco A — dados de identidade e cadastro
-- LGPD: cpf_hash usa SHA-256 com SECRET_SALT; CPF puro nunca é armazenado

CREATE TABLE IF NOT EXISTS pacientes (
    id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    cpf_hash          VARCHAR(64)  NOT NULL UNIQUE,
    nome              VARCHAR(255) NOT NULL,
    telefone          VARCHAR(20)  NOT NULL,
    email             VARCHAR(255),
    estado_civil      VARCHAR(20)  NOT NULL
                          CHECK (estado_civil IN ('SOLTEIRA','CASADA','DIVORCIADA','VIUVA','UNIAO_ESTAVEL')),
    data_nascimento   DATE         NOT NULL,
    possui_filhos     BOOLEAN      NOT NULL DEFAULT FALSE,
    quantidade_filhos SMALLINT,
    altura_cm         SMALLINT     NOT NULL,
    endereco          VARCHAR(500),
    ativo             BOOLEAN      NOT NULL DEFAULT TRUE,
    criado_em         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    atualizado_em     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pacientes_log (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    paciente_id     UUID        NOT NULL REFERENCES pacientes(id),
    atualizado_por  UUID        NOT NULL,
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS consulta_peso (
    id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    id_consulta   UUID          NOT NULL,
    paciente_id   UUID          NOT NULL REFERENCES pacientes(id),
    peso_kg       NUMERIC(5,2)  NOT NULL,
    registrado_em TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pacientes_nome           ON pacientes     (nome);
CREATE INDEX IF NOT EXISTS idx_pacientes_ativo          ON pacientes     (ativo);
CREATE INDEX IF NOT EXISTS idx_pacientes_log_paciente   ON pacientes_log (paciente_id);
CREATE INDEX IF NOT EXISTS idx_consulta_peso_consulta   ON consulta_peso (id_consulta);
CREATE INDEX IF NOT EXISTS idx_consulta_peso_paciente   ON consulta_peso (paciente_id);
