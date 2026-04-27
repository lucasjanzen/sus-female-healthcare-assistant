import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  ConsultaIniciarRequest,
  Etapa1Out,
} from '../models/consulta.model';

@Injectable({ providedIn: 'root' })
export class ConsultaService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/consulta`;

  iniciar(dados: ConsultaIniciarRequest): Observable<Etapa1Out> {
    return this.http.post<Etapa1Out>(`${this.base}/iniciar`, dados);
  }

  obterEtapa1(idConsulta: string): Observable<Etapa1Out> {
    return this.http.get<Etapa1Out>(`${this.base}/${idConsulta}/etapa1`);
  }

  atualizarEtapa1(
    idConsulta: string,
    dados: Partial<ConsultaIniciarRequest>,
  ): Observable<Etapa1Out> {
    return this.http.patch<Etapa1Out>(
      `${this.base}/${idConsulta}/etapa1`,
      dados,
    );
  }
}
