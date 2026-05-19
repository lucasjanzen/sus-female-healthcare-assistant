import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiService } from '../../../core/services/api.service';
import {
  AnaliseFilaItem,
  AnaliseFilaTotais,
  AnaliseResultadoOut,
  EncaminharRequest,
} from '../models/analise.model';

@Injectable({ providedIn: 'root' })
export class AnalisesService {
  private readonly api = inject(ApiService);
  private readonly base = '/analises';

  listarFila(): Observable<AnaliseFilaItem[]> {
    return this.api.get<AnaliseFilaItem[]>(`${this.base}/fila`);
  }

  obterTotais(): Observable<AnaliseFilaTotais> {
    return this.api.get<AnaliseFilaTotais>(`${this.base}/fila/total`);
  }

  obterResultado(idConsulta: string): Observable<AnaliseResultadoOut> {
    return this.api.get<AnaliseResultadoOut>(`${this.base}/${idConsulta}/resultado`);
  }

  revisar(idConsulta: string): Observable<void> {
    return this.api.post<void>(`${this.base}/${idConsulta}/revisar`, {});
  }

  reprocessar(idConsulta: string): Observable<void> {
    return this.api.post<void>(`${this.base}/${idConsulta}/reprocessar`, {});
  }

  encaminhar(idConsulta: string, dados: EncaminharRequest): Observable<void> {
    return this.api.post<void>(`${this.base}/${idConsulta}/encaminhar`, dados);
  }

  listarHistorico(page = 1, pageSize = 20): Observable<AnaliseFilaItem[]> {
    return this.api.get<AnaliseFilaItem[]>(`${this.base}/historico?page=${page}&page_size=${pageSize}`);
  }
}
