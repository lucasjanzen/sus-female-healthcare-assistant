-- Migration 002: adiciona CNS (Cartão Nacional de Saúde) à tabela pacientes
-- CNS é o identificador oficial do paciente no SUS; pode ser preenchido após o cadastro inicial.

ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS cns VARCHAR(20) UNIQUE;

CREATE INDEX IF NOT EXISTS idx_pacientes_cns ON pacientes (cns);
