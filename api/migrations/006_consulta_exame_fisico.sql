CREATE TABLE IF NOT EXISTS consulta_exame_fisico (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    id_consulta         UUID        NOT NULL UNIQUE,
    altura_uterina_cm   NUMERIC(4,1),
    bcf_bpm             SMALLINT,
    movimentacao_fetal  VARCHAR(20),
    edema_grau          SMALLINT,
    edema_localizacao   VARCHAR(100),
    apresentacao_fetal  VARCHAR(20),
    registrado_por      UUID        NOT NULL,
    registrado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
