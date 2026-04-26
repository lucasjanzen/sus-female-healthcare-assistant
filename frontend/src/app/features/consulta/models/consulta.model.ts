export type TipoConsulta =
  | 'PRENATAL'
  | 'GINECOLOGICA'
  | 'PUERPERIO'
  | 'PLANEJAMENTO_FAMILIAR';

export type StatusConsulta = 'ABERTA' | 'EM_ATENDIMENTO' | 'ENCERRADA';

export interface PacienteConsultaOut {
  id: string;
  nome: string;
  dataNascimento: string;
  cns?: string;
}

export interface ConsultaIniciarRequest {
  pacienteId: string;
  tipoConsulta: TipoConsulta;
  dum?: string;
  tcleAssinado: boolean;
}

export interface ConsultaEtapa1Out {
  idConsulta: string;
  pacienteId: string;
  tipoConsulta: TipoConsulta;
  status: StatusConsulta;
  dum?: string;
  igSemanas?: number;
  igDias?: number;
  tcleAssinado: boolean;
  abertaEm: string;
}
