import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { AudioIniciarOut, AudioStatusOut } from '../models/consulta.model';

@Injectable({ providedIn: 'root' })
export class AudioService {
  constructor(private api: ApiService) {}

  iniciarGravacao(idConsulta: string, tipoAudio = 'CONSULTA_GERAL'): Observable<AudioIniciarOut> {
    return this.api.post<AudioIniciarOut>(
      `/consulta/${idConsulta}/audio/iniciar?tipo_audio=${tipoAudio}`,
      {},
    );
  }

  encerrarGravacao(idConsulta: string): Observable<AudioStatusOut> {
    return this.api.post<AudioStatusOut>(`/consulta/${idConsulta}/audio/encerrar`, {});
  }

  obterStatus(idConsulta: string): Observable<AudioStatusOut> {
    return this.api.get<AudioStatusOut>(`/consulta/${idConsulta}/audio/status`);
  }
}
