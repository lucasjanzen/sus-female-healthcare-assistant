-- Migration 004: triagem da consulta
-- Banco A — adiciona colunas de triagem em consultas_identidade e cria consulta_triagem

ALTER TABLE consultas_identidade
    ADD COLUMN IF NOT EXISTS triagem_concluida    BOOLEAN     NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS triagem_concluida_em TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS medico_id            UUID,
    ADD COLUMN IF NOT EXISTS assumida_em          TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS consulta_triagem (
    id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    id_consulta   UUID         NOT NULL UNIQUE,
    peso_kg       NUMERIC(5,2) NOT NULL,
    imc           NUMERIC(4,2) NOT NULL,
    pa_sistolica  SMALLINT     NOT NULL,
    pa_diastolica SMALLINT     NOT NULL,
    temperatura_c NUMERIC(4,1) NOT NULL,
    queixas_texto TEXT,
    queixas_tags  JSONB,
    alertas       JSONB,
    registrado_por UUID        NOT NULL,
    registrado_em TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_consulta_triagem_id_consulta
    ON consulta_triagem (id_consulta);
