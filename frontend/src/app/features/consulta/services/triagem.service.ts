import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { Etapa1Out, TriagemCreate } from '../models/consulta.model';

@Injectable({ providedIn: 'root' })
export class TriagemService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/consulta`;

  salvar(idConsulta: string, dados: TriagemCreate): Observable<Etapa1Out> {
    return this.http.post<Etapa1Out>(`${this.base}/${idConsulta}/triagem`, dados);
  }
}
