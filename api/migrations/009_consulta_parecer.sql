CREATE TABLE IF NOT EXISTS consulta_parecer (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    id_consulta         UUID        NOT NULL UNIQUE,
    parecer_texto       TEXT,
    audio_parecer_id    UUID,
    registrado_por      UUID        NOT NULL,
    registrado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
