import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../../environments/environment';

export interface AudioStatus {
  status_processamento: string;
  transcricao?: string;
}

@Injectable({ providedIn: 'root' })
export class AudioService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/consulta`;

  iniciar(idConsulta: string): Observable<{ audioId: string }> {
    return this.http.post<{ audioId: string }>(`${this.base}/${idConsulta}/audio/iniciar`, {});
  }

  encerrar(idConsulta: string): Observable<AudioStatus> {
    return this.http.post<AudioStatus>(`${this.base}/${idConsulta}/audio/encerrar`, {});
  }

  status(idConsulta: string): Observable<AudioStatus> {
    return this.http.get<AudioStatus>(`${this.base}/${idConsulta}/audio/status`);
  }
}
