import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../../environments/environment';
import { RelatoOut } from '../models/consulta.model';

@Injectable({ providedIn: 'root' })
export class RelatoService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/consulta`;

  criar(idConsulta: string, relatoTexto: string): Observable<RelatoOut> {
    return this.http.post<RelatoOut>(`${this.base}/${idConsulta}/relato`, { relatoTexto });
  }

  atualizar(idConsulta: string, dados: { relatoTexto?: string; parecerMedico?: string }): Observable<RelatoOut> {
    return this.http.patch<RelatoOut>(`${this.base}/${idConsulta}/relato`, dados);
  }

  obter(idConsulta: string): Observable<RelatoOut> {
    return this.http.get<RelatoOut>(`${this.base}/${idConsulta}/relato`);
  }
}
