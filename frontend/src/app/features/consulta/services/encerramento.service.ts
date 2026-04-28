import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../../environments/environment';
import { ApiService } from '../../../core/services/api.service';
import {
  EncerramentoCreate,
  EncerramentoOut,
  ResumoPecOut,
  SugestaoEncerramentoOut,
} from '../models/consulta.model';

@Injectable({ providedIn: 'root' })
export class EncerramentoService {
  private readonly api = inject(ApiService);
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  obterSugestao(idConsulta: string): Observable<SugestaoEncerramentoOut> {
    return this.api.get<SugestaoEncerramentoOut>(
      `/consulta/${idConsulta}/encerramento/sugestao`
    );
  }

  encerrar(idConsulta: string, dados: EncerramentoCreate): Observable<EncerramentoOut> {
    return this.api.post<EncerramentoOut>(`/consulta/${idConsulta}/encerrar`, dados);
  }

  obterResumoPec(idConsulta: string): Observable<ResumoPecOut> {
    return this.api.get<ResumoPecOut>(`/consulta/${idConsulta}/resumo-pec`);
  }

  baixarResumoPdf(idConsulta: string): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/consulta/${idConsulta}/resumo-pec/pdf`, {
      responseType: 'blob',
    });
  }
}
