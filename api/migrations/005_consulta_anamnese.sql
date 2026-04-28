CREATE TABLE IF NOT EXISTS consulta_anamnese (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    id_consulta             UUID        NOT NULL UNIQUE,
    gestacoes               SMALLINT,
    partos                  SMALLINT,
    abortos                 SMALLINT,
    doencas                 JSONB,
    medicamentos            JSONB,
    situacao_moradia        VARCHAR(20),
    situacao_renda          VARCHAR(20),
    suporte_familiar        VARCHAR(20),
    historico_saude_mental  TEXT,
    registrado_por          UUID        NOT NULL,
    registrado_em           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
