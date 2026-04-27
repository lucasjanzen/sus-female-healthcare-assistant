export type TipoConsulta =
  'PRENATAL' | 'GINECOLOGICA' | 'PUERPERIO' | 'PLANEJAMENTO_FAMILIAR';

export type StatusConsulta = 'ABERTA' | 'EM_ATENDIMENTO' | 'ENCERRADA';

export type NivelAlerta = 'INFO' | 'ATENCAO' | 'CRITICO';

export type TagQueixa =
  'NAUSEA' | 'VOMITO' | 'DOR_CABECA' | 'DOR_ABDOMINAL' | 'SANGRAMENTO' |
  'EDEMA' | 'TONTURA' | 'FALTA_AR' | 'ARDENCIA_URINARIA' | 'CORRIMENTO' |
  'MOVIMENTOS_FETAIS_REDUZIDOS' | 'SEM_QUEIXAS';

export interface PacienteConsultaOut {
  id: string;
  nome: string;
  dataNascimento: string;
  cns?: string;
  alturaCm: number;
}

export interface AlertaTriagem {
  tipo: string;
  descricao: string;
  nivel: NivelAlerta;
}

export interface TriagemCreate {
  pesoKg: number;
  paSistolica: number;
  paDiastolica: number;
  temperaturaC: number;
  queixasTexto?: string;
  queixasTags?: TagQueixa[];
}

export interface TriagemResumo {
  pesoKg: number;
  imc: number;
  paSistolica: number;
  paDiastolica: number;
  temperaturaC: number;
  queixasTexto?: string;
  queixasTags?: TagQueixa[];
  alertas: AlertaTriagem[];
}

export interface ConsultaIniciarRequest {
  pacienteId: string;
  tipoConsulta: TipoConsulta;
  dum?: string;
  tcleAssinado: boolean;
}

export interface Etapa1Out {
  idConsulta: string;
  pacienteId: string;
  tipoConsulta: TipoConsulta;
  status: StatusConsulta;
  dum?: string;
  igSemanas?: number;
  igDias?: number;
  tcleAssinado: boolean;
  triagemConcluida: boolean;
  triagem?: TriagemResumo;
  abertaEm: string;
  triagemConcluidaEm?: string;
}

// Alias para compatibilidade com código existente
export type ConsultaEtapa1Out = Etapa1Out;
