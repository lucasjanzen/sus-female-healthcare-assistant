import { ResultadoIAOut } from '../../consulta/models/consulta.model';
import { TipoConsulta } from '../../consulta/models/consulta.types';

export type FaixaRisco = 'VERDE' | 'AMARELO' | 'LARANJA' | 'VERMELHO';

export interface AnaliseFilaItem {
  idConsulta: string;
  pacienteNome: string;
  tipoConsulta: TipoConsulta;
  igSemanas?: number;
  dataConsulta: string;
  scoreGeral: number;
  faixaRisco: FaixaRisco;
  indicadoresCriticos: string[];
  analiseConcluidaEm: string;
  temErro: boolean;
}

export interface AnaliseFilaTotais {
  total: number;
  criticos: number;
}

export interface AnaliseResultadoOut extends ResultadoIAOut {
  analiseRevisada: boolean;
  analiseRevisadaEm?: string;
  encaminhado: boolean;
  encaminhadoEm?: string;
}

export interface EncaminharRequest {
  observacao?: string;
}
