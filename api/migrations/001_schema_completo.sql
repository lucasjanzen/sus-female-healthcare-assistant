-- ============================================================
-- 001 — Schema completo CASF
-- Centro de Assistência à Saúde Feminina
-- ============================================================

-- Usuários do sistema
CREATE TABLE usuarios (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    nome        VARCHAR     NOT NULL,
    email       VARCHAR     NOT NULL UNIQUE,
    senha_hash  VARCHAR     NOT NULL,
    role        VARCHAR     NOT NULL,
        -- MEDICO, ENFERMEIRO, ADMIN
    ativo       BOOLEAN     NOT NULL DEFAULT TRUE,
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- Pacientes (cadastro pelo Admin)
CREATE TABLE pacientes (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    cpf_hash            VARCHAR     NOT NULL UNIQUE,
    cns                 VARCHAR     UNIQUE,
    nome                VARCHAR     NOT NULL,
    data_nascimento     DATE        NOT NULL,
    telefone            VARCHAR     NOT NULL,
    email               VARCHAR,
    estado_civil        VARCHAR     NOT NULL,
        -- SOLTEIRA, CASADA, DIVORCIADA, VIUVA, UNIAO_ESTAVEL
    possui_filhos       BOOLEAN     NOT NULL DEFAULT FALSE,
    quantidade_filhos   SMALLINT,
    altura_cm           SMALLINT    NOT NULL,
    endereco            VARCHAR,
    ativo               BOOLEAN     NOT NULL DEFAULT TRUE,
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- Log de alterações de pacientes
CREATE TABLE pacientes_log (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    paciente_id     UUID        NOT NULL,
    atualizado_por  UUID        NOT NULL,
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- Ciclo de vida das consultas
CREATE TABLE consultas_identidade (
    id_consulta             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    paciente_id             UUID        NOT NULL,
    profissional_id         UUID        NOT NULL,
    ubs_id                  UUID,
    estado_id               VARCHAR(10),
    tipo_consulta           VARCHAR     NOT NULL,
        -- PRENATAL, GINECOLOGICA, PUERPERIO, PLANEJAMENTO_FAMILIAR
    status                  VARCHAR     NOT NULL DEFAULT 'ABERTA',
        -- ABERTA, EM_ATENDIMENTO, ENCERRADA
    dum                     DATE,
    ig_semanas              SMALLINT,
    ig_dias                 SMALLINT,
    triagem_concluida       BOOLEAN     NOT NULL DEFAULT FALSE,
    triagem_concluida_em    TIMESTAMPTZ,
    medico_id               UUID,
    assumida_em             TIMESTAMPTZ,
    aberta_em               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    encerrada_em            TIMESTAMPTZ,
    -- Controle de análise assíncrona pós-encerramento
    analise_concluida_em    TIMESTAMPTZ,
    analise_erro            TEXT,
    -- Revisão clínica da análise
    analise_revisada        BOOLEAN     NOT NULL DEFAULT FALSE,
    analise_revisada_em     TIMESTAMPTZ,
    analise_revisada_por    UUID,
    -- Encaminhamento da paciente
    encaminhado             BOOLEAN     NOT NULL DEFAULT FALSE,
    encaminhado_em          TIMESTAMPTZ,
    encaminhado_por         UUID
);


-- Dados de triagem (Etapa 1 — Enfermeiro)
CREATE TABLE consulta_triagem (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    id_consulta     UUID            NOT NULL UNIQUE,
    peso_kg         NUMERIC(5,2)    NOT NULL,
    pa_sistolica    SMALLINT        NOT NULL,
    pa_diastolica   SMALLINT        NOT NULL,
    registrado_por  UUID            NOT NULL,
    registrado_em   TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);


-- Relato e parecer da consulta (Etapa 2 — Médico)
CREATE TABLE consulta_relato (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    id_consulta     UUID        NOT NULL UNIQUE,
    relato_texto    TEXT,
    registrado_por  UUID        NOT NULL,
    registrado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- Resultado da análise de IA
CREATE TABLE consulta_resultado (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    id_consulta         UUID        NOT NULL UNIQUE,
    score_geral         SMALLINT    NOT NULL,
    faixa_risco         VARCHAR     NOT NULL,
        -- VERDE, AMARELO, LARANJA, VERMELHO
    indicadores         JSONB       NOT NULL,
    resumo_ia           TEXT,
    transcricao_audio   TEXT,
    sentimento_voz      JSONB,
    calculado_em        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sumario_estruturado JSONB,
    texto_clinico       TEXT,
    fontes_utilizadas   JSONB,
    tokens_utilizados   INTEGER,
    prompt_enviado      TEXT,
    resposta_bruta_llm  TEXT
);

COMMENT ON COLUMN consulta_resultado.sentimento_voz IS
    'Resultado de análise vocal: {"dominante": "NEGATIVO"|"POSITIVO"|"NEUTRO", "scores": {"positivo": 0.0, "negativo": 0.0, "neutro": 0.0}}';


-- Histórico de peso por consulta (contexto para o LLM)
CREATE TABLE historico_peso (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    paciente_id     UUID            NOT NULL,
    id_consulta     UUID            NOT NULL,
    peso_kg         NUMERIC(5,2)    NOT NULL,
    registrado_em   TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT historico_peso_id_consulta_unique UNIQUE (id_consulta)
);

CREATE INDEX idx_historico_peso_paciente_id ON historico_peso(paciente_id);


-- Auditoria imutável de acessos
CREATE TABLE audit_acessos (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    profissional_id UUID        NOT NULL,
    unidade_id      UUID,
    cpf_hash        VARCHAR,
    tipo_acesso     VARCHAR     NOT NULL,
    justificativa   TEXT
);

CREATE OR REPLACE FUNCTION bloquear_edicao_auditoria()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Registros de auditoria não podem ser alterados ou removidos.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_imutavel
BEFORE UPDATE OR DELETE ON audit_acessos
FOR EACH ROW EXECUTE FUNCTION bloquear_edicao_auditoria();
