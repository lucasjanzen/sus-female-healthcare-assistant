CREATE TABLE IF NOT EXISTS consulta_rastreio_psicossocial (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    id_consulta         UUID        NOT NULL UNIQUE,
    epds_respostas      JSONB       NOT NULL,
    epds_score          SMALLINT    NOT NULL,
    epds_flag           BOOLEAN     NOT NULL,
    gad7_respostas      JSONB       NOT NULL,
    gad7_score          SMALLINT    NOT NULL,
    gad7_flag           BOOLEAN     NOT NULL,
    hits_respostas      JSONB       NOT NULL,
    hits_score          SMALLINT    NOT NULL,
    hits_flag           BOOLEAN     NOT NULL,
    situacao_social     JSONB       NOT NULL,
    registrado_por      UUID        NOT NULL,
    registrado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
