export interface PacienteListItem {
  id: string;
  nome: string;
  dataNascimento: string;
  cns?: string;
  ativo: boolean;
}

export interface PacienteAdminOut {
  id: string;
  cns?: string;
  nome: string;
  dataNascimento: string;
  telefone: string;
  email?: string;
  estadoCivil: string;
  possuiFilhos: boolean;
  quantidadeFilhos?: number;
  alturaCm: number;
  endereco?: string;
  ativo: boolean;
  criadoEm: string;
  atualizadoEm: string;
}

export interface PacienteAdminCreate {
  cpf: string;
  cns?: string;
  nome: string;
  dataNascimento: string;
  telefone: string;
  email?: string;
  estadoCivil: string;
  possuiFilhos: boolean;
  quantidadeFilhos?: number;
  alturaCm: number;
  endereco?: string;
}

export type PacienteAdminUpdate = Partial<Omit<PacienteAdminCreate, 'cpf'>>;

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
}
