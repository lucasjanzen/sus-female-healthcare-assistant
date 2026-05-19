import { Component, DestroyRef, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError } from 'rxjs';
import { HttpErrorResponse } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { NotificationService } from 'app/core/services/notification.service';
import { extrairMensagemErro } from 'app/core/utils/http-error.utils';
import { ConsultaAssumidaOut } from 'app/features/fila/models/fila.model';
import { FilaService } from 'app/features/fila/services/fila.service';
import { ConsultaService } from '../services/consulta.service';
import { RelatoService } from '../services/relato.service';
import { EncerramentoService } from '../services/encerramento.service';
import { ConsultaRecordingService } from '../services/consulta-recording.service';
import { HistoricoService, HistoricoPesoItem } from '../services/historico.service';
import { ConsultaTriagemComponent } from './componentes/consulta-triagem/consulta-triagem.component';
import { ConfirmarEncerramentoAtendimentoDialogComponent } from './componentes/confirmar-encerramento-atendimento-dialog.component';

@Component({
  selector: 'app-atendimento',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    ConsultaTriagemComponent,
  ],
  templateUrl: './atendimento.component.html',
  styleUrl: './atendimento.component.scss',
})
export class AtendimentoComponent implements OnInit, OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly destroyRef = inject(DestroyRef);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly consultaService = inject(ConsultaService);
  private readonly relatoService = inject(RelatoService);
  private readonly encerramentoService = inject(EncerramentoService);
  protected readonly recordingService = inject(ConsultaRecordingService);
  private readonly filaService = inject(FilaService);
  private readonly historicoService = inject(HistoricoService);
  private readonly notification = inject(NotificationService);
  private readonly dialog = inject(MatDialog);
  private timer?: number;
  private saveTimer?: number;

  readonly consultaAtiva = computed(() => this.consultaService.consultaAtiva());
  readonly dadosConsulta = signal<ConsultaAssumidaOut | null>(null);
  readonly segundosGravacao = signal(0);
  readonly relatoSalvo = signal(false);
  readonly historicoPeso = signal<HistoricoPesoItem[]>([]);
  readonly encerrando = signal(false);
  readonly encerrado = signal(false);

  private readonly idConsulta = computed(() => this.consultaAtiva()?.idConsulta);

  readonly form = this.fb.nonNullable.group({
    relatoTexto: ['', [Validators.minLength(20)]],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.consultaService.obterTriagem(id).subscribe((etapa) => {
      this.consultaService.definirConsultaAtiva({ idConsulta: id, tipo: etapa.tipoConsulta });
      this.carregarDadosConsulta();
      this.carregarRelato();
    });
  }

  ngOnDestroy(): void {
    this.cancelarTimerGravacao();
    this.cancelarSaveTimer();
    this.recordingService.limpar();
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
      next: (relato) => this.form.patchValue({ relatoTexto: relato.relatoTexto ?? '' }),
      error: (err: HttpErrorResponse) => {
        if (err.status !== 404) {
          this.notification.erro(
            extrairMensagemErro(err, 'Não foi possível carregar o relato anterior.'),
            4000,
          );
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
        error: (err: HttpErrorResponse) =>
          this.notification.erro(extrairMensagemErro(err, 'Erro ao salvar relato')),
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

  onAudioUpload(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    this.recordingService.setAudioBlob(file);
  }

  tempoGravacao(): string {
    const segundos = this.segundosGravacao();
    return `${Math.floor(segundos / 60)}:${String(segundos % 60).padStart(2, '0')}`;
  }

  confirmarEncerramento(): void {
    const ref = this.dialog.open(ConfirmarEncerramentoAtendimentoDialogComponent, { width: '420px' });
    ref.afterClosed().subscribe((confirmado: boolean) => {
      if (confirmado) this.encerrar();
    });
  }

  private encerrar(): void {
    const id = this.idConsulta();
    if (!id) return;
    this.salvarRelato();
    this.encerrando.set(true);
    const audioBlob = this.recordingService.getAudioBlob();
    this.encerramentoService.encerrar(id, audioBlob).subscribe({
      next: () => {
        this.encerrando.set(false);
        this.encerrado.set(true);
      },
      error: (err: HttpErrorResponse) => {
        this.encerrando.set(false);
        this.notification.erro(extrairMensagemErro(err, 'Erro ao encerrar a consulta'));
      },
    });
  }

  irParaInicio(): void {
    this.router.navigate(['/home']);
  }

  irParaAnalises(): void {
    this.router.navigate(['/analises']);
  }
}
