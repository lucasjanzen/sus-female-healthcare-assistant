import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  ConsultaEtapa1Out,
  ConsultaIniciarRequest,
} from '../models/consulta.model';

@Injectable({ providedIn: 'root' })
export class ConsultaService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/consulta`;

  iniciar(dados: ConsultaIniciarRequest): Observable<ConsultaEtapa1Out> {
    return this.http.post<ConsultaEtapa1Out>(`${this.base}/iniciar`, dados);
  }

  obterEtapa1(idConsulta: string): Observable<ConsultaEtapa1Out> {
    return this.http.get<ConsultaEtapa1Out>(`${this.base}/${idConsulta}/etapa1`);
  }

  atualizarEtapa1(
    idConsulta: string,
    dados: Partial<ConsultaIniciarRequest>,
  ): Observable<ConsultaEtapa1Out> {
    return this.http.patch<ConsultaEtapa1Out>(
      `${this.base}/${idConsulta}/etapa1`,
      dados,
    );
  }
}
