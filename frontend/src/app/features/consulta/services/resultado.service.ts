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

  reprocessar(idConsulta: string): Observable<ResultadoIAOut> {
    return this.http
      .post<ResultadoIAOut>(`${environment.apiUrl}/analises/${idConsulta}/reprocessar`, {})
      .pipe(tap((r) => { this.cache.set(idConsulta, r); this.evictIfNeeded(); }));
  }

  obter(idConsulta: string): Observable<ResultadoIAOut> {
    const cached = this.cache.get(idConsulta);
    if (cached) return of(cached);
    return this.obterFresh(idConsulta);
  }

  obterFresh(idConsulta: string): Observable<ResultadoIAOut> {
    return this.http
      .get<ResultadoIAOut>(`${this.base}/${idConsulta}/resultado`)
      .pipe(tap((r) => { this.cache.set(idConsulta, r); this.evictIfNeeded(); }));
  }

  revisar(idConsulta: string): Observable<ResultadoIAOut> {
    return this.http
      .post<ResultadoIAOut>(`${environment.apiUrl}/analises/${idConsulta}/revisar`, {})
      .pipe(tap((r) => { this.cache.set(idConsulta, r); this.evictIfNeeded(); }));
  }

  private evictIfNeeded(): void {
    if (this.cache.size > 20) {
      const oldest = this.cache.keys().next().value!;
      this.cache.delete(oldest);
    }
  }
}
