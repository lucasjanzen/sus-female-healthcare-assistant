-- Migration 013: fila de consultas em andamento

ALTER TABLE consultas_identidade
    ADD COLUMN IF NOT EXISTS medico_id UUID;

ALTER TABLE consultas_identidade
    ADD COLUMN IF NOT EXISTS assumida_em TIMESTAMPTZ;

ALTER TABLE consultas_identidade
    ADD COLUMN IF NOT EXISTS triagem_concluida BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE consultas_identidade
    ADD COLUMN IF NOT EXISTS triagem_concluida_em TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_consultas_fila_ubs
    ON consultas_identidade (ubs_id, triagem_concluida_em)
    WHERE status = 'EM_ATENDIMENTO'
      AND triagem_concluida = TRUE
      AND medico_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_consultas_medico_andamento
    ON consultas_identidade (medico_id, status);
