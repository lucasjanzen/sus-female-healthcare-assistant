-- Colunas para resultado da análise LLM (GPT-4o)
-- sentimento_voz já existe (migration 002) — não recriar
ALTER TABLE consulta_resultado
    ADD COLUMN IF NOT EXISTS sumario_estruturado   JSONB,
    ADD COLUMN IF NOT EXISTS texto_clinico         TEXT,
    ADD COLUMN IF NOT EXISTS fontes_utilizadas     JSONB,
    ADD COLUMN IF NOT EXISTS tokens_utilizados     INTEGER;

-- Histórico de peso por consulta para contexto do LLM
CREATE TABLE IF NOT EXISTS historico_peso (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    paciente_id     UUID            NOT NULL,
    id_consulta     UUID            NOT NULL,
    peso_kg         NUMERIC(5,2)    NOT NULL,
    registrado_em   TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT historico_peso_id_consulta_unique UNIQUE (id_consulta)
);

CREATE INDEX IF NOT EXISTS idx_historico_peso_paciente_id ON historico_peso(paciente_id);
