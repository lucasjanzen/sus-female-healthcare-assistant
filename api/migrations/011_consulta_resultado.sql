CREATE TABLE IF NOT EXISTS consulta_resultado (
    id                              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    id_consulta                     UUID        NOT NULL UNIQUE,
    score_geral                     SMALLINT    NOT NULL,
    faixa_risco                     VARCHAR(10) NOT NULL,
    score_psicossocial              SMALLINT    NOT NULL,
    score_audio                     SMALLINT,
    score_estruturado               SMALLINT    NOT NULL,
    alertas                         JSONB       NOT NULL,
    resumo_encaminhamento           TEXT,
    sugestao_conduta                TEXT,
    transcricao_editada             TEXT,
    calculado_em                    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confirmado_pelo_profissional    BOOLEAN     NOT NULL DEFAULT FALSE,
    confirmado_em                   TIMESTAMPTZ
);
