import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import {
  AnamneseCreate, AnamneseOut,
  ExameFisicoCreate, ExameFisicoOut,
  ExamesLabCreate, ExamesLabOut,
  RastreioCreate, RastreioOut,
  ParecerCreate, ParecerOut,
} from '../models/consulta.model';

@Injectable({ providedIn: 'root' })
export class ConsultaClinicaService {
  constructor(private api: ApiService) {}

  salvarAnamnese(idConsulta: string, dados: AnamneseCreate): Observable<AnamneseOut> {
    return this.api.post<AnamneseOut>(`/consulta/${idConsulta}/anamnese`, dados);
  }

  atualizarAnamnese(idConsulta: string, dados: AnamneseCreate): Observable<AnamneseOut> {
    return this.api.patch<AnamneseOut>(`/consulta/${idConsulta}/anamnese`, dados);
  }

  obterAnamnese(idConsulta: string): Observable<AnamneseOut> {
    return this.api.get<AnamneseOut>(`/consulta/${idConsulta}/anamnese`);
  }

  salvarExameFisico(idConsulta: string, dados: ExameFisicoCreate): Observable<ExameFisicoOut> {
    return this.api.post<ExameFisicoOut>(`/consulta/${idConsulta}/exame-fisico`, dados);
  }

  atualizarExameFisico(idConsulta: string, dados: ExameFisicoCreate): Observable<ExameFisicoOut> {
    return this.api.patch<ExameFisicoOut>(`/consulta/${idConsulta}/exame-fisico`, dados);
  }

  obterExameFisico(idConsulta: string): Observable<ExameFisicoOut> {
    return this.api.get<ExameFisicoOut>(`/consulta/${idConsulta}/exame-fisico`);
  }

  salvarExamesLab(idConsulta: string, dados: ExamesLabCreate): Observable<ExamesLabOut> {
    return this.api.post<ExamesLabOut>(`/consulta/${idConsulta}/exames-lab`, dados);
  }

  atualizarExamesLab(idConsulta: string, dados: ExamesLabCreate): Observable<ExamesLabOut> {
    return this.api.patch<ExamesLabOut>(`/consulta/${idConsulta}/exames-lab`, dados);
  }

  obterExamesLab(idConsulta: string): Observable<ExamesLabOut> {
    return this.api.get<ExamesLabOut>(`/consulta/${idConsulta}/exames-lab`);
  }

  salvarRastreio(idConsulta: string, dados: RastreioCreate): Observable<RastreioOut> {
    return this.api.post<RastreioOut>(`/consulta/${idConsulta}/rastreio`, dados);
  }

  atualizarRastreio(idConsulta: string, dados: RastreioCreate): Observable<RastreioOut> {
    return this.api.patch<RastreioOut>(`/consulta/${idConsulta}/rastreio`, dados);
  }

  obterRastreio(idConsulta: string): Observable<RastreioOut> {
    return this.api.get<RastreioOut>(`/consulta/${idConsulta}/rastreio`);
  }

  salvarParecer(idConsulta: string, dados: ParecerCreate): Observable<ParecerOut> {
    return this.api.post<ParecerOut>(`/consulta/${idConsulta}/parecer`, dados);
  }

  atualizarParecer(idConsulta: string, dados: ParecerCreate): Observable<ParecerOut> {
    return this.api.patch<ParecerOut>(`/consulta/${idConsulta}/parecer`, dados);
  }

  obterParecer(idConsulta: string): Observable<ParecerOut> {
    return this.api.get<ParecerOut>(`/consulta/${idConsulta}/parecer`);
  }
}
