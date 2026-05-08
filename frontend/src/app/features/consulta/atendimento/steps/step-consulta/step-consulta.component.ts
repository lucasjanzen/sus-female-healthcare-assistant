import {
  Component,
  DestroyRef,
  EventEmitter,
  OnDestroy,
  OnInit,
  Output,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError } from 'rxjs';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { NotificationService } from 'app/core/services/notification.service';

import { ConsultaAssumidaOut } from 'app/features/fila/models/fila.model';
import { FilaService } from 'app/features/fila/services/fila.service';
import { IndicadorIA, ResultadoIAOut } from 'app/features/consulta/models/consulta.model';
import { ConsultaService } from 'app/features/consulta/services/consulta.service';
import { RelatoService } from 'app/features/consulta/services/relato.service';
import { ResultadoService } from 'app/features/consulta/services/resultado.service';
import { ConsultaRecordingService } from 'app/features/consulta/services/consulta-recording.service';

@Component({
  selector: 'app-step-consulta',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatDividerModule,
    MatExpansionModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatTooltipModule,
  ],
  templateUrl: './step-consulta.component.html',
  styleUrl: './step-consulta.component.scss',
})
export class StepConsultaComponent implements OnInit, OnDestroy {
  @Output() confirmado = new EventEmitter<void>();

  private readonly fb = inject(FormBuilder);
  private readonly destroyRef = inject(DestroyRef);
  private readonly consultaService = inject(ConsultaService);
  private readonly relatoService = inject(RelatoService);
  protected readonly recordingService = inject(ConsultaRecordingService);
  private readonly resultadoService = inject(ResultadoService);
  private readonly filaService = inject(FilaService);
  private readonly snackBar = inject(MatSnackBar);
  private readonly notification = inject(NotificationService);
  private timer?: number;
  private saveTimer?: number;

  readonly consultaAtiva = computed(() => this.consultaService.consultaAtiva());
  readonly dadosConsulta = signal<ConsultaAssumidaOut | null>(null);
  readonly resultado = signal<ResultadoIAOut | null>(null);
  readonly analisando = signal(false);
  readonly segundosGravacao = signal(0);
  readonly relatoSalvo = signal(false);
  private idConsulta = computed(() => this.consultaAtiva()?.idConsulta);

  readonly form = this.fb.nonNullable.group({
    relatoTexto: ['', [Validators.minLength(20)]],
    parecerMedico: [''],
  });

  readonly indicadoresVisiveis = computed(() => {
    return (this.resultado()?.indicadores ?? []).filter(
      (i) => i.nivel === 'MODERADO' || i.nivel === 'ALTO',
    );
  });

  ngOnInit(): void {
    this.carregarDadosConsulta();
    this.carregarRelato();
  }

  ngOnDestroy(): void {
    this.cancelarTimerGravacao();
    this.cancelarSaveTimer();
    if (this.recordingService.gravando()) {
      this.recordingService.parar();
    }
  }

  private cancelarTimerGravacao(): void {
    if (this.timer) window.clearInterval(this.timer);
  }

  private cancelarSaveTimer(): void {
    if (this.saveTimer) window.clearTimeout(this.saveTimer);
  }

  private carregarDadosConsulta(): void {
    this.filaService
      .emAndamento()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((consulta) => this.dadosConsulta.set(consulta));
  }

  private carregarRelato(): void {
    const id = this.idConsulta();
    if (!id) return;
    this.relatoService.obter(id).subscribe({
      next: (relato) =>
        this.form.patchValue({
          relatoTexto: relato.relatoTexto ?? '',
          parecerMedico: relato.parecerMedico ?? '',
        }),
      error: () => this.notification.erro('Não foi possível carregar o relato anterior.', 4000),
    });
  }

  salvarRelato(): void {
    const id = this.idConsulta();
    const relatoTexto = this.form.controls.relatoTexto.value.trim();
    if (!id || relatoTexto.length < 20) return;
    this.relatoService
      .atualizar(id, { relatoTexto })
      .pipe(
        catchError(() => this.relatoService.criar(id, relatoTexto)),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: () => this.indicarRelatoSalvo(),
        error: () => this.notification.erro('Erro ao salvar relato'),
      });
  }

  private indicarRelatoSalvo(): void {
    this.relatoSalvo.set(true);
    this.cancelarSaveTimer();
    this.saveTimer = window.setTimeout(() => this.relatoSalvo.set(false), 2000);
  }

  salvarParecer(): void {
    const id = this.idConsulta();
    if (!id) return;
    this.relatoService
      .atualizar(id, { parecerMedico: this.form.controls.parecerMedico.value })
      .subscribe({
        error: () => this.notification.erro('Erro ao salvar parecer'),
      });
  }

  async iniciarGravacao(): Promise<void> {
    try {
      await this.recordingService.iniciar();
      this.segundosGravacao.set(0);
      this.timer = window.setInterval(() => this.segundosGravacao.update((v) => v + 1), 1000);
    } catch {
      this.notification.erro('Erro ao iniciar gravação. Verifique permissão do microfone.', 4000);
    }
  }

  encerrarGravacao(): void {
    this.cancelarTimerGravacao();
    this.recordingService.parar();
  }

  analisar(): void {
    if (!this.recordingService.gravacaoConcluida()) return;
    const id = this.idConsulta();
    if (!id) return;
    this.salvarRelato();
    this.analisando.set(true);
    const audioBlob = this.recordingService.getAudioBlob() ?? undefined;
    this.resultadoService.analisar(id, audioBlob).subscribe({
      next: (resultado) => {
        this.resultado.set(resultado);
        this.analisando.set(false);
        const parecerAtual = this.form.controls.parecerMedico.value.trim();
        if (parecerAtual) {
          this.snackBar
            .open('IA gerou um resumo. Deseja substituir o parecer atual?', 'Substituir', {
              duration: 8000,
            })
            .onAction()
            .subscribe(() => this.form.controls.parecerMedico.setValue(resultado.resumoIa));
        } else {
          this.form.controls.parecerMedico.setValue(resultado.resumoIa);
        }
      },
      error: () => {
        this.notification.erro('Erro ao analisar relato');
        this.analisando.set(false);
      },
    });
  }

  confirmarAnalise(): void {
    const id = this.idConsulta();
    if (!id) return;
    this.salvarParecer();
    this.resultadoService.confirmar(id).subscribe({
      next: () => this.confirmado.emit(),
      error: () => this.notification.erro('Erro ao confirmar análise'),
    });
  }

  tempoGravacao(): string {
    const segundos = this.segundosGravacao();
    return `${Math.floor(segundos / 60)}:${String(segundos % 60).padStart(2, '0')}`;
  }

  textoFaixa(resultado: ResultadoIAOut): string {
    const textos: Record<string, string> = {
      VERDE: 'Nenhum indicador significativo',
      AMARELO: 'Indicadores leves - atenção recomendada',
      LARANJA: 'Indicadores moderados - intervenção recomendada',
      VERMELHO: 'Indicadores críticos - encaminhamento imediato',
    };
    return textos[resultado.faixaRisco] ?? '';
  }

  formatarIndicador(indicador: IndicadorIA): string {
    return indicador.tipo.replaceAll('_', ' ');
  }
}
