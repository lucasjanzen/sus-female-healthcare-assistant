export type UserRole = 'MEDICO' | 'ENFERMEIRO' | 'ADMIN';

export interface JwtPayload {
  sub: string;
  nome: string;
  role: UserRole;
  exp: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserOut {
  id: string;
  nome: string;
  email: string;
  role: UserRole;
  ativo: boolean;
  criado_em: string;
}
