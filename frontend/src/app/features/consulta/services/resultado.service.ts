import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, of, tap } from 'rxjs';

import { environment } from 'environments/environment';
import { ResultadoIAOut } from '../models/consulta.model';

@Injectable({ providedIn: 'root' })
export class ResultadoService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/consulta`;
  private readonly cache = new Map<string, ResultadoIAOut>();

  analisar(idConsulta: string): Observable<ResultadoIAOut> {
    return this.http
      .post<ResultadoIAOut>(`${this.base}/${idConsulta}/analisar`, {})
      .pipe(tap((r) => this.cache.set(idConsulta, r)));
  }

  obter(idConsulta: string): Observable<ResultadoIAOut> {
    const cached = this.cache.get(idConsulta);
    if (cached) return of(cached);
    return this.http
      .get<ResultadoIAOut>(`${this.base}/${idConsulta}/resultado`)
      .pipe(tap((r) => this.cache.set(idConsulta, r)));
  }

  confirmar(idConsulta: string): Observable<ResultadoIAOut> {
    return this.http
      .post<ResultadoIAOut>(`${this.base}/${idConsulta}/resultado/confirmar`, {})
      .pipe(tap((r) => this.cache.set(idConsulta, r)));
  }
}
