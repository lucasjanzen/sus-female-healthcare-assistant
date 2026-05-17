import { FaixaRisco, NivelIndicador, StatusConsulta, TipoConsulta, TipoIndicador } from './consulta.types';

export interface PacienteConsultaOut {
  id: string;
  nome: string;
  dataNascimento: string;
  cns?: string;
}

export interface TriagemResumo {
  pesoKg: number;
  paSistolica: number;
  paDiastolica: number;
}

export interface Etapa1Out {
  idConsulta: string;
  pacienteId: string;
  tipoConsulta: TipoConsulta;
  status: StatusConsulta;
  dum?: string;
  igSemanas?: number;
  igDias?: number;
  triagemConcluida: boolean;
  triagem?: TriagemResumo;
  abertaEm: string;
  triagemConcluidaEm?: string;
}

export interface IndicadorIA {
  tipo: TipoIndicador;
  nivel: NivelIndicador;
  descricao: string;
  origem: string;
}

export interface IndicadorRisco {
  tipo: string;
  nivel: 'BAIXO' | 'MODERADO' | 'ALTO';
  evidencias: string[];
  recomendacao: string;
}

export interface SumarioEstruturado {
  indicadores: IndicadorRisco[];
  scoreGeral: number;
  faixaRisco: FaixaRisco;
  pontosAtencao: string[];
  encaminhamentosSugeridos: string[];
  contextoHistorico: string;
  modoFallback: boolean;
}

export interface SentimentoVozOut {
  dominante: 'POSITIVO' | 'NEGATIVO' | 'NEUTRO';
  scores: { positivo: number; negativo: number; neutro: number };
}

export interface FontesUtilizadas {
  relato: boolean;
  transcricao: boolean;
  sentimentoVoz: boolean;
  dadosConsulta: boolean;
  historico: boolean;
}

export interface ResultadoIAOut {
  idConsulta: string;
  scoreGeral: number;
  faixaRisco: FaixaRisco;
  indicadores: IndicadorIA[];
  resumoIa: string;
  confirmado: boolean;
  calculadoEm: string;
  sentimentoVoz?: SentimentoVozOut;
  sumarioEstruturado?: SumarioEstruturado;
  textoClinico?: string;
  fontesUtilizadas?: FontesUtilizadas;
  tokensUtilizados?: number;
  promptEnviado?: string;
  respostaBrutaLlm?: string;
}

export interface RelatoOut {
  idConsulta: string;
  relatoTexto?: string;
  parecerMedico?: string;
  registradoEm: string;
  atualizadoEm: string;
}

export interface SugestaoEncerramentoOut {
  dataSugerida: string;
  encaminhamentosSugeridos: string[];
  condutaSugerida: string;
}

export interface EncerramentoCreate {
  conduta: string;
  encaminhamentos?: string[];
  dataProximoRetorno: string;
  observacoes?: string;
}

export interface EncerramentoOut {
  idConsulta: string;
  conduta: string;
  encaminhamentos?: string[];
  dataProximoRetorno: string;
  observacoes?: string;
  encerradoEm: string;
}
