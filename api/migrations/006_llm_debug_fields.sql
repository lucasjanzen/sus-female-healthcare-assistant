ALTER TABLE consulta_resultado
  ADD COLUMN IF NOT EXISTS prompt_enviado TEXT,
  ADD COLUMN IF NOT EXISTS resposta_bruta_llm TEXT;
