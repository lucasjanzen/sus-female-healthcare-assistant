import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from 'environments/environment';
import {
  PacienteAdminCreate,
  PacienteAdminOut,
  PacienteAdminUpdate,
  PacienteListItem,
  PaginatedResponse,
} from '../models/paciente-admin.model';

@Injectable({ providedIn: 'root' })
export class PacienteAdminService {
  private readonly base = `${environment.apiUrl}/admin/pacientes`;

  constructor(private http: HttpClient) {}

  listar(
    page = 1,
    pageSize = 20,
    filtros: { nome?: string; ativo?: boolean } = {},
  ): Observable<PaginatedResponse<PacienteListItem>> {
    let params = new HttpParams().set('page', page).set('page_size', pageSize);
    if (filtros.nome) params = params.set('nome', filtros.nome);
    if (filtros.ativo !== undefined) params = params.set('ativo', String(filtros.ativo));
    return this.http.get<PaginatedResponse<PacienteListItem>>(this.base, { params });
  }

  buscar(termo: string): Observable<PacienteListItem[]> {
    const params = new HttpParams().set('q', termo);
    return this.http.get<PacienteListItem[]>(`${this.base}/buscar`, { params });
  }

  obter(id: string): Observable<PacienteAdminOut> {
    return this.http.get<PacienteAdminOut>(`${this.base}/${id}`);
  }

  criar(dados: PacienteAdminCreate): Observable<PacienteAdminOut> {
    return this.http.post<PacienteAdminOut>(this.base, dados);
  }

  atualizar(id: string, dados: PacienteAdminUpdate): Observable<PacienteAdminOut> {
    return this.http.put<PacienteAdminOut>(`${this.base}/${id}`, dados);
  }

  desativar(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/${id}`);
  }
}
