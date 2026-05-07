import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from 'environments/environment';
import { ConsultaAssumidaOut, ConsultaFilaItem } from '../models/fila.model';

@Injectable({ providedIn: 'root' })
export class FilaService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/fila`;

  listar(): Observable<ConsultaFilaItem[]> {
    return this.http.get<ConsultaFilaItem[]>(`${this.base}/consultas`);
  }

  emAndamento(): Observable<ConsultaAssumidaOut | null> {
    return this.http.get<ConsultaAssumidaOut | null>(`${this.base}/consultas/em-andamento`);
  }

  assumir(idConsulta: string): Observable<ConsultaAssumidaOut> {
    return this.http.post<ConsultaAssumidaOut>(`${this.base}/consultas/${idConsulta}/assumir`, {});
  }
}
