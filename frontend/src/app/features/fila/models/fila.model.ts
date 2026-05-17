import { TriagemResumo } from '../../consulta/models/consulta.model';
import { FaixaRisco, TipoConsulta } from '../../consulta/models/consulta.types';

export interface ConsultaFilaItem {
  idConsulta: string;
  pacienteNome: string;
  pacienteDataNascimento: string;
  tipoConsulta: TipoConsulta;
  igSemanas?: number;
  igDias?: number;
  triagemConcluidaEm: string;
}

export interface ConsultaParaFinalizarItem {
  idConsulta: string;
  pacienteNome: string;
  pacienteDataNascimento: string;
  tipoConsulta: TipoConsulta;
  igSemanas?: number;
  igDias?: number;
  scoreRisco: number;
  faixaRisco: FaixaRisco;
  concluidaEm: string;
}

export interface ConsultaAssumidaOut {
  idConsulta: string;
  pacienteId: string;
  pacienteNome: string;
  pacienteDataNascimento: string;
  tipoConsulta: TipoConsulta;
  igSemanas?: number;
  igDias?: number;
  triagemResumo: TriagemResumo;
  assumidaEm: string;
}
