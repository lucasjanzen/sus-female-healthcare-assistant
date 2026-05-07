import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

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

  obterSugestao(idConsulta: string): Observable<SugestaoEncerramentoOut> {
    return this.api.get<SugestaoEncerramentoOut>(`/consulta/${idConsulta}/encerramento/sugestao`);
  }

  encerrar(idConsulta: string, dados: EncerramentoCreate): Observable<EncerramentoOut> {
    return this.api.post<EncerramentoOut>(`/consulta/${idConsulta}/encerrar`, dados);
  }

  obterResumoPec(idConsulta: string): Observable<ResumoPecOut> {
    return this.api.get<ResumoPecOut>(`/consulta/${idConsulta}/resumo-pec`);
  }

  baixarResumoPdf(idConsulta: string): Observable<Blob> {
    return this.api.getBlob(`/consulta/${idConsulta}/resumo-pec/pdf`);
  }
}
