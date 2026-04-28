import {
  Component, EventEmitter, Input, OnDestroy, Output, inject, signal,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';

import { ConsultaAtiva, Etapa1Out, ResultadoOut } from '../../../models/consulta.model';
import { AudioService } from '../../../services/audio.service';
import { ResultadoService } from '../../../services/resultado.service';

import { AnamneseComponent } from './abas/anamnese/anamnese.component';
import { ExameFisicoComponent } from './abas/exame-fisico/exame-fisico.component';
import { ExamesLabComponent } from './abas/exames-lab/exames-lab.component';
import { RastreioComponent } from './abas/rastreio/rastreio.component';
import { ParecerComponent } from './abas/parecer/parecer.component';
import { PainelIaComponent } from './painel-ia/painel-ia.component';

@Component({
  selector: 'app-step-consulta',
  standalone: true,
  imports: [
    MatCardModule, MatTabsModule, MatButtonModule, MatIconModule,
    MatDividerModule, MatExpansionModule, MatProgressSpinnerModule, MatSnackBarModule,
    AnamneseComponent, ExameFisicoComponent, ExamesLabComponent,
    RastreioComponent, ParecerComponent, PainelIaComponent,
  ],
  templateUrl: './step-consulta.component.html',
})
export class StepConsultaComponent implements OnDestroy {
  @Input() consultaAtiva!: ConsultaAtiva;
  @Input() etapa1!: Etapa1Out;
  @Output() consultaConcluida = new EventEmitter<void>();

  private readonly audioSvc = inject(AudioService);
  private readonly resultadoSvc = inject(ResultadoService);
  private readonly snack = inject(MatSnackBar);

  readonly gravando = signal(false);
  readonly calculando = signal(false);
  readonly resultado = signal<ResultadoOut | null>(null);
  readonly resultadoConfirmado = signal(false);

  readonly anamneseSalva = signal(false);
  readonly exameFisicoSalvo = signal(false);
  readonly rastreioSalvo = signal(false);

  ngOnDestroy(): void {
    if (this.gravando()) this._encerrarGravacao();
  }

  get idConsulta(): string {
    return this.consultaAtiva.idConsulta;
  }

  get igSemanas(): number | null {
    return this.etapa1.igSemanas ?? null;
  }

  get triagem() {
    return this.etapa1.triagem;
  }

  get podeMostrarBotaoCalculo(): boolean {
    return this.anamneseSalva() && this.exameFisicoSalvo() && this.rastreioSalvo();
  }

  iniciarGravacao(): void {
    this.audioSvc.iniciarGravacao(this.idConsulta).subscribe({
      next: () => {
        this.gravando.set(true);
        this.snack.open('Gravação iniciada.', 'OK', { duration: 2000 });
      },
      error: () => this.snack.open('Erro ao iniciar gravação.', 'OK', { duration: 3000 }),
    });
  }

  encerrarGravacao(): void {
    this._encerrarGravacao();
  }

  private _encerrarGravacao(): void {
    this.audioSvc.encerrarGravacao(this.idConsulta).subscribe({
      next: () => {
        this.gravando.set(false);
        this.snack.open('Gravação encerrada.', 'OK', { duration: 2000 });
      },
      error: () => {
        this.gravando.set(false);
      },
    });
  }

  calcularIA(): void {
    if (this.gravando()) {
      this._encerrarGravacao();
    }
    this.calculando.set(true);
    this.resultadoSvc.calcular(this.idConsulta).subscribe({
      next: (res) => {
        this.resultado.set(res);
        this.calculando.set(false);
      },
      error: () => {
        this.calculando.set(false);
        this.snack.open('Erro ao calcular análise IA.', 'OK', { duration: 4000 });
      },
    });
  }

  onResultadoConfirmado(): void {
    this.resultadoConfirmado.set(true);
  }

  avancarEncerramento(): void {
    this.consultaConcluida.emit();
  }
}
