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

  encerrar(idConsulta: string, audioBlob?: Blob | null): Observable<EncerramentoSimplesOut> {
    const formData = new FormData();
    if (audioBlob) {
      formData.append('audio', audioBlob, 'recording.webm');
    }
    return this.api.post<EncerramentoSimplesOut>(`/consulta/${idConsulta}/encerrar`, formData);
  }
}
