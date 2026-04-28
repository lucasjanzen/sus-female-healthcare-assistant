import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { ResultadoOut } from '../models/consulta.model';

@Injectable({ providedIn: 'root' })
export class ResultadoService {
  constructor(private api: ApiService) {}

  calcular(idConsulta: string): Observable<ResultadoOut> {
    return this.api.post<ResultadoOut>(`/consulta/${idConsulta}/calcular-score`, {});
  }

  obter(idConsulta: string): Observable<ResultadoOut> {
    return this.api.get<ResultadoOut>(`/consulta/${idConsulta}/resultado`);
  }

  salvarTranscricao(idConsulta: string, transcricaoEditada: string): Observable<void> {
    return this.api.patch<void>(`/consulta/${idConsulta}/resultado/transcricao`, {
      transcricaoEditada,
    });
  }

  confirmar(idConsulta: string): Observable<void> {
    return this.api.post<void>(`/consulta/${idConsulta}/resultado/confirmar`, {});
  }
}
