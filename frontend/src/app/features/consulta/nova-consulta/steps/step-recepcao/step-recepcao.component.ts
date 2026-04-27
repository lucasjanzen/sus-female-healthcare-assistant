import { Component, EventEmitter, Output, inject } from '@angular/core';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import {
  AlertaTriagem,
  Etapa1Out,
  TipoConsulta,
} from '../../../models/consulta.model';
import {
  BlocoIdentificacaoComponent,
  IdentificacaoConcluida,
} from './blocos/bloco-identificacao/bloco-identificacao.component';
import { BlocoTriagemComponent } from './blocos/bloco-triagem/bloco-triagem.component';

type Fase = 'identificacao' | 'triagem' | 'confirmacao';

@Component({
  selector: 'app-step-recepcao',
  standalone: true,
  imports: [
    MatButtonModule,
    MatCardModule,
    MatDividerModule,
    MatIconModule,
    BlocoIdentificacaoComponent,
    BlocoTriagemComponent,
  ],
  templateUrl: './step-recepcao.component.html',
})
export class StepRecepcaoComponent {
  @Output() recepcaoConcluida = new EventEmitter<Etapa1Out>();

  private router = inject(Router);

  fase: Fase = 'identificacao';

  idConsulta: string | null = null;
  tipoConsulta: TipoConsulta | null = null;
  igSemanas: number | null = null;
  igDias: number | null = null;
  alturaCm: number | null = null;
  etapa1Result: Etapa1Out | null = null;

  get alertas(): AlertaTriagem[] {
    return this.etapa1Result?.triagem?.alertas ?? [];
  }

  get alertasAtencao(): AlertaTriagem[] {
    return this.alertas.filter((a) => a.nivel === 'ATENCAO');
  }

  get alertasCriticos(): AlertaTriagem[] {
    return this.alertas.filter((a) => a.nivel === 'CRITICO');
  }

  onIdentificacaoConcluida(event: IdentificacaoConcluida): void {
    this.idConsulta = event.idConsulta;
    this.tipoConsulta = event.tipo;
    this.igSemanas = event.igSemanas;
    this.igDias = event.igDias;
    this.alturaCm = event.alturaCm;
    this.fase = 'triagem';
  }

  onTriagemConcluida(resultado: Etapa1Out): void {
    this.etapa1Result = resultado;
    this.fase = 'confirmacao';
    this.recepcaoConcluida.emit(resultado);
  }

  iniciarNovaConsulta(): void {
    this.fase = 'identificacao';
    this.idConsulta = null;
    this.tipoConsulta = null;
    this.igSemanas = null;
    this.igDias = null;
    this.alturaCm = null;
    this.etapa1Result = null;
  }

  voltarHome(): void {
    this.router.navigate(['/home']);
  }
}
