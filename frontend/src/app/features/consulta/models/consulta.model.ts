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

export interface ResultadoIAOut {
  idConsulta: string;
  scoreGeral: number;
  faixaRisco: FaixaRisco;
  indicadores: IndicadorIA[];
  resumoIa: string;
  statusAudio: string;
  confirmado: boolean;
  calculadoEm: string;
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

export interface ResumoPecOut {
  idConsulta: string;
  tipoConsulta: string;
  dataConsulta: string;
  igSemanas?: number;
  igDias?: number;
  pesoKg?: number;
  pa?: string;
  scoreRisco: number;
  faixaRisco: FaixaRisco;
  indicadores: string[];
  conduta: string;
  encaminhamentos: string[];
  dataProximoRetorno: string;
  geradoEm: string;
}
