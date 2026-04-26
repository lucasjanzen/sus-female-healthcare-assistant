-- Migration 003: consultas_identidade e consulta_tcle_log
-- Banco A — dados de identidade da consulta
-- LGPD: paciente_id referência interna; CPF nunca persiste nesta tabela

CREATE TABLE IF NOT EXISTS consultas_identidade (
    id_consulta      UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    paciente_id      UUID         NOT NULL,
    profissional_id  UUID         NOT NULL,
    ubs_id           UUID,
    estado_id        VARCHAR(2),
    tipo_consulta    VARCHAR(30)  NOT NULL
                         CHECK (tipo_consulta IN ('PRENATAL','GINECOLOGICA','PUERPERIO','PLANEJAMENTO_FAMILIAR')),
    status           VARCHAR(20)  NOT NULL DEFAULT 'ABERTA'
                         CHECK (status IN ('ABERTA','EM_ATENDIMENTO','ENCERRADA')),
    dum              DATE,
    ig_semanas       SMALLINT,
    ig_dias          SMALLINT,
    tcle_assinado    BOOLEAN      NOT NULL DEFAULT FALSE,
    tcle_assinado_em TIMESTAMPTZ,
    aberta_em        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    encerrada_em     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS consulta_tcle_log (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    id_consulta     UUID        NOT NULL,
    paciente_id     UUID        NOT NULL,
    profissional_id UUID        NOT NULL,
    assinado_em     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_origem       VARCHAR(45)
);

CREATE INDEX IF NOT EXISTS idx_consultas_paciente       ON consultas_identidade (paciente_id);
CREATE INDEX IF NOT EXISTS idx_consultas_profissional   ON consultas_identidade (profissional_id);
CREATE INDEX IF NOT EXISTS idx_consultas_status         ON consultas_identidade (status);
CREATE INDEX IF NOT EXISTS idx_consultas_aberta_em      ON consultas_identidade (aberta_em);
CREATE INDEX IF NOT EXISTS idx_tcle_log_consulta        ON consulta_tcle_log    (id_consulta);
