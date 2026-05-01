import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

type ConsultaIniciarRequest = Record<string, unknown>;
type ConsultaIniciarOut = Record<string, unknown>;
type PacienteConsultaOut = Record<string, unknown>;

@Injectable({ providedIn: 'root' })
export class ConsultaService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/consulta`;

  iniciar(dados: ConsultaIniciarRequest): Observable<ConsultaIniciarOut> {
    return this.http.post<ConsultaIniciarOut>(`${this.base}/iniciar`, dados);
  }

  buscarPacientes(termo: string): Observable<PacienteConsultaOut[]> {
    return this.http.get<PacienteConsultaOut[]>(`${this.base}/pacientes/buscar`, {
      params: { q: termo },
    });
  }
}
