import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiService } from '../../../core/services/api.service';

export interface EncerramentoSimplesOut {
  idConsulta: string;
  status: string;
  mensagem: string;
}

@Injectable({ providedIn: 'root' })
export class EncerramentoService {
  private readonly api = inject(ApiService);

  encerrar(idConsulta: string): Observable<EncerramentoSimplesOut> {
    return this.api.post<EncerramentoSimplesOut>(`/consulta/${idConsulta}/encerrar`, {});
  }
}
