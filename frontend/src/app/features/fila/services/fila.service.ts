import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from 'environments/environment';
import { ConsultaAssumidaOut, ConsultaFilaItem, ConsultaParaFinalizarItem } from '../models/fila.model';

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

  listarParaFinalizar(): Observable<ConsultaParaFinalizarItem[]> {
    return this.http.get<ConsultaParaFinalizarItem[]>(`${this.base}/consultas/para-finalizar`);
  }

  assumir(idConsulta: string): Observable<ConsultaAssumidaOut> {
    return this.http.post<ConsultaAssumidaOut>(`${this.base}/consultas/${idConsulta}/assumir`, {});
  }
}
