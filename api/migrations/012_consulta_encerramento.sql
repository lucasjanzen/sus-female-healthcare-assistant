CREATE TABLE IF NOT EXISTS consulta_encerramento (
    id                              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    id_consulta                     UUID        NOT NULL UNIQUE,
    orientacoes                     JSONB       NOT NULL,
    vacinacao                       JSONB,
    data_proximo_retorno            DATE        NOT NULL,
    data_proximo_retorno_sugerida   DATE        NOT NULL,
    encaminhamentos                 JSONB,
    cartao_gestante_atualizado      BOOLEAN     NOT NULL DEFAULT FALSE,
    observacoes_finais              TEXT,
    encerrado_por                   UUID        NOT NULL,
    encerrado_em                    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_encerramento_consulta ON consulta_encerramento (id_consulta);
