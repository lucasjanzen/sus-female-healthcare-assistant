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
import { HttpErrorResponse } from '@angular/common/http';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { NotificationService } from 'app/core/services/notification.service';
import { extrairMensagemErro } from 'app/core/utils/http-error.utils';
import { ConsultaAssumidaOut } from 'app/features/fila/models/fila.model';
import { FilaService } from 'app/features/fila/services/fila.service';
import { ResultadoIAOut } from 'app/features/consulta/models/consulta.model';
import { ConsultaService } from 'app/features/consulta/services/consulta.service';
import { RelatoService } from 'app/features/consulta/services/relato.service';
import { ResultadoService } from 'app/features/consulta/services/resultado.service';
import { ConsultaRecordingService } from 'app/features/consulta/services/consulta-recording.service';
import { HistoricoService, HistoricoPesoItem } from 'app/features/consulta/services/historico.service';
import { ConsultaTriagemComponent } from '../consulta-triagem/consulta-triagem.component';
import { ConsultaResultadoComponent } from '../consulta-resultado/consulta-resultado.component';

@Component({
  selector: 'app-step-consulta',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    ConsultaTriagemComponent,
    ConsultaResultadoComponent,
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
  private readonly historicoService = inject(HistoricoService);
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
  readonly historicoPeso = signal<HistoricoPesoItem[]>([]);
  private readonly idConsulta = computed(() => this.consultaAtiva()?.idConsulta);

  readonly form = this.fb.nonNullable.group({
    relatoTexto: ['', [Validators.minLength(20)]],
    textoClinico: [''],
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
      .subscribe((consulta) => {
        this.dadosConsulta.set(consulta);
        if (consulta?.pacienteId) {
          this.carregarHistoricoPeso(consulta.pacienteId);
        }
      });
  }

  private carregarHistoricoPeso(pacienteId: string): void {
    this.historicoService
      .obterHistoricoPeso(pacienteId, 5)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (hist) => this.historicoPeso.set(hist),
        error: (err) => console.error('[historico-peso]', err),
      });
  }

  private carregarRelato(): void {
    const id = this.idConsulta();
    if (!id) return;
    this.relatoService.obter(id).subscribe({
      next: (relato) =>
        this.form.patchValue({
          relatoTexto: relato.relatoTexto ?? '',
          textoClinico: relato.parecerMedico ?? '',
        }),
      error: (err: HttpErrorResponse) => {
        if (err.status !== 404) {
          this.notification.erro(extrairMensagemErro(err, 'Não foi possível carregar o relato anterior.'), 4000);
        }
      },
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
        error: (err: HttpErrorResponse) => this.notification.erro(extrairMensagemErro(err, 'Erro ao salvar relato')),
      });
  }

  private indicarRelatoSalvo(): void {
    this.relatoSalvo.set(true);
    this.cancelarSaveTimer();
    this.saveTimer = window.setTimeout(() => this.relatoSalvo.set(false), 2000);
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
    const id = this.idConsulta();
    if (!id) return;
    this.salvarRelato();
    this.analisando.set(true);
    const audioBlob = this.recordingService.getAudioBlob() ?? undefined;
    this.resultadoService.analisar(id, audioBlob).subscribe({
      next: (res) => {
        this.resultado.set(res);
        this.analisando.set(false);
        const textoClinico = res.textoClinico ?? res.resumoIa;
        const atual = this.form.controls.textoClinico.value.trim();
        if (atual) {
          this.snackBar
            .open('IA gerou um texto clínico. Deseja substituir?', 'Substituir', { duration: 8000 })
            .onAction()
            .subscribe(() => this.form.controls.textoClinico.setValue(textoClinico));
        } else {
          this.form.controls.textoClinico.setValue(textoClinico);
        }
      },
      error: (err: HttpErrorResponse) => {
        this.notification.erro(extrairMensagemErro(err, 'Erro ao analisar relato'));
        this.analisando.set(false);
      },
    });
  }

  tempoGravacao(): string {
    const segundos = this.segundosGravacao();
    return `${Math.floor(segundos / 60)}:${String(segundos % 60).padStart(2, '0')}`;
  }
}
