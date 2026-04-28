import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, catchError, of } from 'rxjs';

import { environment } from '../../../../environments/environment';
import { ConsultaAssumidaOut, ConsultaFilaItem } from '../models/fila.model';

@Injectable({ providedIn: 'root' })
export class FilaService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/fila/consultas`;

  listar(): Observable<ConsultaFilaItem[]> {
    return this.http.get<ConsultaFilaItem[]>(this.base);
  }

  assumir(idConsulta: string): Observable<ConsultaAssumidaOut> {
    return this.http.post<ConsultaAssumidaOut>(`${this.base}/${idConsulta}/assumir`, {});
  }

  emAndamento(): Observable<ConsultaAssumidaOut | null> {
    return this.http.get<ConsultaAssumidaOut>(`${this.base}/em-andamento`).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status === 404) return of(null);
        throw error;
      }),
    );
  }

  obterEmAndamento(idConsulta: string): Observable<ConsultaAssumidaOut> {
    return this.http.get<ConsultaAssumidaOut>(`${this.base}/${idConsulta}/em-andamento`);
  }

  total(): Observable<{ total: number }> {
    return this.http.get<{ total: number }>(`${this.base}/total`);
  }
}
