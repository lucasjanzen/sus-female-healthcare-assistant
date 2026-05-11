-- Remove colunas obsoletas da tabela consulta_audio.
-- O processamento de áudio é síncrono: grava → transcreve → descarta.
-- Não há fila assíncrona nem retenção de áudio, portanto essas colunas não fazem sentido.

ALTER TABLE consulta_audio
    DROP COLUMN IF EXISTS status_processamento;

ALTER TABLE consulta_audio
    DROP COLUMN IF EXISTS deletar_em;

-- Estrutura final de consulta_audio:
--   id           UUID        PK
--   id_consulta  UUID        NOT NULL
--   transcricao  TEXT
--   criado_em    TIMESTAMPTZ NOT NULL DEFAULT NOW()
