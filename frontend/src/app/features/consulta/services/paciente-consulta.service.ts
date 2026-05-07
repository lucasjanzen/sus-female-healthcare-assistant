import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from 'environments/environment';

type PacienteConsultaOut = Record<string, unknown>;

@Injectable({ providedIn: 'root' })
export class PacienteConsultaService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/consulta`;

  buscar(termo: string): Observable<PacienteConsultaOut[]> {
    return this.http.get<PacienteConsultaOut[]>(`${this.base}/pacientes/buscar`, {
      params: { q: termo },
    });
  }
}
