import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  ConsultaIniciada,
  PacienteCreate,
  PacienteOut,
  PacienteUpdate,
} from '../models/paciente.model';

@Injectable({ providedIn: 'root' })
export class PacienteService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/pacientes`;

  buscar(termo: string): Observable<PacienteOut[]> {
    return this.http.get<PacienteOut[]>(`${this.base}/buscar`, {
      params: { q: termo },
    });
  }

  criar(dados: PacienteCreate): Observable<ConsultaIniciada> {
    return this.http.post<ConsultaIniciada>(this.base, dados);
  }

  atualizar(id: string, dados: PacienteUpdate): Observable<ConsultaIniciada> {
    return this.http.put<ConsultaIniciada>(`${this.base}/${id}`, dados);
  }
}
