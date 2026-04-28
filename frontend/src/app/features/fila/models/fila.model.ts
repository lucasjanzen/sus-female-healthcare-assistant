import { AlertaTriagem, TipoConsulta, TriagemResumo } from '../../consulta/models/consulta.model';

export interface ConsultaFilaItem {
  idConsulta: string;
  pacienteNome: string;
  pacienteDataNascimento: string;
  tipoConsulta: TipoConsulta;
  igSemanas?: number;
  igDias?: number;
  triagemConcluidaEm: string;
  alertasCriticos: string[];
  temAlertaCritico: boolean;
}

export interface ConsultaAssumidaOut {
  idConsulta: string;
  pacienteNome: string;
  pacienteDataNascimento: string;
  tipoConsulta: TipoConsulta;
  igSemanas?: number;
  igDias?: number;
  triagemResumo: TriagemResumo;
  alertasTriagem: AlertaTriagem[];
  assumidaEm: string;
}
