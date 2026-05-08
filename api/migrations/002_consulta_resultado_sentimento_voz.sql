ALTER TABLE consulta_resultado
  ADD COLUMN IF NOT EXISTS sentimento_voz JSONB DEFAULT NULL;

COMMENT ON COLUMN consulta_resultado.sentimento_voz IS
  'Resultado de análise vocal: {"dominante": "NEGATIVO"|"POSITIVO"|"NEUTRO", "scores": {"positivo": 0.0, "negativo": 0.0, "neutro": 0.0}}';
