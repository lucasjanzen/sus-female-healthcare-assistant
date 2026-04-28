export type TipoConsulta =
  | "PRENATAL"
  | "GINECOLOGICA"
  | "PUERPERIO"
  | "PLANEJAMENTO_FAMILIAR";

export interface ConsultaAtiva {
  idConsulta: string;
  tipo: TipoConsulta;
}

export type StatusConsulta = "ABERTA" | "EM_ATENDIMENTO" | "ENCERRADA";

export type NivelAlerta = "INFO" | "ATENCAO" | "CRITICO";

export type TagQueixa =
  | "NAUSEA"
  | "VOMITO"
  | "DOR_CABECA"
  | "DOR_ABDOMINAL"
  | "SANGRAMENTO"
  | "EDEMA"
  | "TONTURA"
  | "FALTA_AR"
  | "ARDENCIA_URINARIA"
  | "CORRIMENTO"
  | "MOVIMENTOS_FETAIS_REDUZIDOS"
  | "SEM_QUEIXAS";

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
  alertas?: AlertaTriagem[];
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

// ── Etapa 2 — Consulta Clínica ────────────────────────────────────────────────

export interface MedicamentoItem {
  nome: string;
  dose?: string;
  frequencia?: string;
}

export interface AnamneseCreate {
  gestacoes?: number;
  partos?: number;
  abortos?: number;
  doencas?: string[];
  medicamentos?: MedicamentoItem[];
  situacaoMoradia?: string;
  situacaoRenda?: string;
  suporteFamiliar?: string;
  historicoSaudeMental?: string;
}

export interface AnamneseOut extends AnamneseCreate {
  idConsulta: string;
  registradoEm: string;
  atualizadoEm: string;
}

export interface ExameFisicoCreate {
  alturaUterinaCm?: number;
  bcfBpm?: number;
  movimentacaoFetal?: string;
  edemaGrau?: number;
  edemaLocalizacao?: string;
  apresentacaoFetal?: string;
}

export interface AlertaExame {
  tipo: string;
  descricao: string;
  nivel: NivelAlerta;
}

export interface ExameFisicoOut extends ExameFisicoCreate {
  idConsulta: string;
  alertas: AlertaExame[];
  registradoEm: string;
  atualizadoEm: string;
}

export interface ExamesLabCreate {
  hemograma?: Record<string, unknown>;
  tipagemSanguinea?: string;
  vdrl?: Record<string, unknown>;
  glicemiaJejum?: Record<string, unknown>;
  totg?: Record<string, unknown>;
  urina?: Record<string, unknown>;
  urocultura?: Record<string, unknown>;
  hiv?: Record<string, unknown>;
  hepatiteB?: Record<string, unknown>;
  hepatiteC?: Record<string, unknown>;
  toxoplasmose?: Record<string, unknown>;
  usgObstetrica?: Record<string, unknown>;
}

export interface ExamesLabOut extends ExamesLabCreate {
  idConsulta: string;
  registradoEm: string;
  atualizadoEm: string;
}

export interface RastreioCreate {
  epdsRespostas: Record<string, number>;
  gad7Respostas: Record<string, number>;
  hitsRespostas: Record<string, number>;
  situacaoSocial: Record<string, boolean>;
}

export interface RastreioOut {
  idConsulta: string;
  epdsRespostas: Record<string, number>;
  epdsScore: number;
  epdsFlag: boolean;
  gad7Respostas: Record<string, number>;
  gad7Score: number;
  gad7Flag: boolean;
  hitsRespostas: Record<string, number>;
  hitsScore: number;
  hitsFlag: boolean;
  situacaoSocial: Record<string, boolean>;
  registradoEm: string;
  atualizadoEm: string;
}

export interface ParecerCreate {
  parecerTexto?: string;
  audioParecerId?: string;
}

export interface ParecerOut extends ParecerCreate {
  idConsulta: string;
  registradoEm: string;
  atualizadoEm: string;
}

export interface AudioIniciarOut {
  audioId: string;
  status: string;
}

export interface AudioStatusOut {
  audioId: string;
  statusProcessamento: string;
  transcricao?: string;
  duracaoSegundos?: number;
}

export type NivelAlertaResultado = "INFO" | "ATENCAO" | "CRITICO";
export type OrigemAlerta = "ESTRUTURADO" | "PSICOSSOCIAL" | "AUDIO";
export type FaixaRisco = "VERDE" | "AMARELO" | "LARANJA" | "VERMELHO";

export interface AlertaResultado {
  tipo: string;
  descricao: string;
  nivel: NivelAlertaResultado;
  origem: OrigemAlerta;
}

export interface ResultadoOut {
  idConsulta: string;
  scoreGeral: number;
  faixaRisco: FaixaRisco;
  scorePsicossocial: number;
  scoreAudio?: number;
  scoreEstruturado: number;
  alertas: AlertaResultado[];
  resumoEncaminhamento?: string;
  sugestaoConduta?: string;
  transcricao?: string;
  transcricaoEditada?: string;
  statusAudio: string;
  confirmado: boolean;
  calculadoEm: string;
}
