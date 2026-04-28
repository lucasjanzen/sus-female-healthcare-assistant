CREATE TABLE IF NOT EXISTS consulta_exames_lab (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    id_consulta         UUID        NOT NULL UNIQUE,
    hemograma           JSONB,
    tipagem_sanguinea   VARCHAR(10),
    vdrl                JSONB,
    glicemia_jejum      JSONB,
    totg                JSONB,
    urina               JSONB,
    urocultura          JSONB,
    hiv                 JSONB,
    hepatite_b          JSONB,
    hepatite_c          JSONB,
    toxoplasmose        JSONB,
    usg_obstetrica      JSONB,
    registrado_por      UUID        NOT NULL,
    registrado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
