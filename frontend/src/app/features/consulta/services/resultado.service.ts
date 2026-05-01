import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../../environments/environment';
import { ResultadoIAOut } from '../models/consulta.model';

@Injectable({ providedIn: 'root' })
export class ResultadoService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/consulta`;

  analisar(idConsulta: string): Observable<ResultadoIAOut> {
    return this.http.post<ResultadoIAOut>(`${this.base}/${idConsulta}/analisar`, {});
  }

  obter(idConsulta: string): Observable<ResultadoIAOut> {
    return this.http.get<ResultadoIAOut>(`${this.base}/${idConsulta}/resultado`);
  }

  confirmar(idConsulta: string): Observable<ResultadoIAOut> {
    return this.http.post<ResultadoIAOut>(`${this.base}/${idConsulta}/resultado/confirmar`, {});
  }
}
