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

  encerrar(idConsulta: string, audioBlob?: Blob): Observable<EncerramentoSimplesOut> {
    if (audioBlob) {
      const uploadBlob = audioBlob.type ? audioBlob : new Blob([audioBlob], { type: 'audio/webm' });
      const formData = new FormData();
      const filename = uploadBlob.type.includes('ogg') ? 'consulta.ogg' : 'consulta.webm';
      formData.append('audio', uploadBlob, filename);
      return this.api.post<EncerramentoSimplesOut>(
        `/consulta/${idConsulta}/encerrar-com-audio`,
        formData,
      );
    }

    return this.api.post<EncerramentoSimplesOut>(`/consulta/${idConsulta}/encerrar`, {});
  }
}
