import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from 'environments/environment';

export interface HistoricoPesoItem {
  pesoKg: number;
  registradoEm: string;
  idConsulta: string;
}

@Injectable({ providedIn: 'root' })
export class HistoricoService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/pacientes`;

  obterHistoricoPeso(pacienteId: string, limite: number = 5): Observable<HistoricoPesoItem[]> {
    const params = new HttpParams().set('limite', String(limite));
    return this.http.get<HistoricoPesoItem[]>(`${this.base}/${pacienteId}/historico-peso`, { params });
  }
}
