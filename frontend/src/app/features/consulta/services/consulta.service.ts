import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../../environments/environment';
import {
  Etapa1Out,
  PacienteConsultaOut,
  TipoConsulta,
  TriagemResumo,
} from '../models/consulta.model';

interface ConsultaIniciarRequest {
  pacienteId: string;
  tipoConsulta: TipoConsulta;
  dum?: string | null;
}

@Injectable({ providedIn: 'root' })
export class ConsultaService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/consulta`;
  private readonly _consultaAtiva = signal<{ idConsulta: string; tipo: TipoConsulta } | null>(null);

  readonly consultaAtiva = computed(() => this._consultaAtiva());

  definirConsultaAtiva(consulta: { idConsulta: string; tipo: TipoConsulta } | null): void {
    this._consultaAtiva.set(consulta);
  }

  iniciar(dados: ConsultaIniciarRequest): Observable<Etapa1Out> {
    return this.http.post<Etapa1Out>(`${this.base}/iniciar`, dados);
  }

  buscarPacientes(termo: string): Observable<PacienteConsultaOut[]> {
    return this.http.get<PacienteConsultaOut[]>(`${this.base}/pacientes/buscar`, {
      params: { q: termo },
    });
  }

  salvarTriagem(idConsulta: string, triagem: TriagemResumo): Observable<Etapa1Out> {
    return this.http.post<Etapa1Out>(`${this.base}/${idConsulta}/triagem`, triagem);
  }

  obterEtapa1(idConsulta: string): Observable<Etapa1Out> {
    return this.http.get<Etapa1Out>(`${this.base}/${idConsulta}/etapa1`);
  }
}
