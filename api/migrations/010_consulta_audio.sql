CREATE TABLE IF NOT EXISTS consulta_audio (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    id_consulta             UUID        NOT NULL,
    tipo_audio              VARCHAR(30) NOT NULL,
    duracao_segundos        INTEGER,
    transcricao             TEXT,
    status_processamento    VARCHAR(20) NOT NULL DEFAULT 'AGUARDANDO',
    criado_em               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deletar_em              TIMESTAMPTZ NOT NULL
);
