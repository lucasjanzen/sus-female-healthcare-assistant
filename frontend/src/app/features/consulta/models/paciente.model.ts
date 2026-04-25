export interface PacienteOut {
  id: string;
  nome: string;
  telefone: string;
  email?: string;
  estadoCivil: string;
  dataNascimento: string;
  possuiFilhos: boolean;
  quantidadeFilhos?: number;
  alturaCm: number;
  endereco?: string;
}

export interface PacienteCreate {
  cpf: string;
  nome: string;
  telefone: string;
  email?: string;
  estadoCivil: string;
  dataNascimento: string;
  possuiFilhos: boolean;
  quantidadeFilhos?: number;
  alturaCm: number;
  pesoKg: number;
  endereco?: string;
}

export type PacienteUpdate = Partial<Omit<PacienteCreate, 'cpf'>> & { pesoKg: number };

export interface ConsultaIniciada {
  paciente: PacienteOut;
  idConsulta: string;
}
