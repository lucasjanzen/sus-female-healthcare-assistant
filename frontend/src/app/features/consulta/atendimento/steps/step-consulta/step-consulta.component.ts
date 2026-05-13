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
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { NotificationService } from 'app/core/services/notification.service';

import { ConsultaAssumidaOut } from 'app/features/fila/models/fila.model';
import { FilaService } from 'app/features/fila/services/fila.service';
import { IndicadorIA, IndicadorRisco, ResultadoIAOut } from 'app/features/consulta/models/consulta.model';
import { ConsultaService } from 'app/features/consulta/services/consulta.service';
import { RelatoService } from 'app/features/consulta/services/relato.service';
import { ResultadoService } from 'app/features/consulta/services/resultado.service';
import { ConsultaRecordingService } from 'app/features/consulta/services/consulta-recording.service';
import { HistoricoService, HistoricoPesoItem } from 'app/features/consulta/services/historico.service';

interface LinhaPeso {
  pesoKg: number;
  registradoEm: string;
  variacaoTexto: string;
  variacaoCor: string;
}

@Component({
  selector: 'app-step-consulta',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatDividerModule,
    MatExpansionModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatTableModule,
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
  readonly colunasPeso = ['data', 'peso', 'variacao'];
  readonly linhasPeso = computed(() => this.mapearLinhas(this.historicoPeso()));
  readonly tendenciaPeso = computed(() => this.calcularTendencia(this.historicoPeso()));
  readonly tendenciaCor = computed(() => {
    const t = this.tendenciaPeso();
    return t === 'perda progressiva' || t === 'ganho progressivo' ? '#e65100' : null;
  });
  private idConsulta = computed(() => this.consultaAtiva()?.idConsulta);

  readonly form = this.fb.nonNullable.group({
    relatoTexto: ['', [Validators.minLength(20)]],
    textoClinico: [''],
  });

  readonly indicadoresVisiveis = computed(() =>
    (this.resultado()?.sumarioEstruturado?.indicadores ?? []).filter(
      (i): i is IndicadorRisco => i.nivel === 'MODERADO' || i.nivel === 'ALTO',
    ),
  );

  readonly pontosAtencao = computed(
    () => this.resultado()?.sumarioEstruturado?.pontosAtencao ?? [],
  );

  readonly encaminhamentosSugeridos = computed(
    () => this.resultado()?.sumarioEstruturado?.encaminhamentosSugeridos ?? [],
  );

  readonly modoFallback = computed(
    () => this.resultado()?.sumarioEstruturado?.modoFallback ?? false,
  );

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
          this.notification.erro('Não foi possível carregar o relato anterior.', 4000);
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
        error: () => this.notification.erro('Erro ao salvar relato'),
      });
  }

  private indicarRelatoSalvo(): void {
    this.relatoSalvo.set(true);
    this.cancelarSaveTimer();
    this.saveTimer = window.setTimeout(() => this.relatoSalvo.set(false), 2000);
  }

  salvarTextoClinico(): void {
    const id = this.idConsulta();
    if (!id) return;
    this.relatoService
      .atualizar(id, { parecerMedico: this.form.controls.textoClinico.value })
      .subscribe({
        next: () => this.snackBar.open('Texto clínico salvo.', '', { duration: 2000 }),
        error: () => this.notification.erro('Erro ao salvar texto clínico'),
      });
  }

  copiarTextoClinico(): void {
    const texto = this.form.controls.textoClinico.value;
    if (!texto) return;
    navigator.clipboard.writeText(texto).then(
      () => this.snackBar.open('Texto copiado!', '', { duration: 2000 }),
      () => this.notification.erro('Não foi possível copiar o texto'),
    );
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
      error: () => {
        this.notification.erro('Erro ao analisar relato');
        this.analisando.set(false);
      },
    });
  }

  confirmarAnalise(): void {
    const id = this.idConsulta();
    if (!id) return;
    this.salvarTextoClinico();
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

  corFaixa(faixa: string): string {
    const mapa: Record<string, string> = {
      VERDE: '#2e7d32',
      AMARELO: '#f57f17',
      LARANJA: '#e65100',
      VERMELHO: '#b71c1c',
    };
    return mapa[faixa] ?? '#757575';
  }

  corNivel(nivel: string): string {
    const mapa: Record<string, string> = {
      BAIXO: '#2e7d32',
      MODERADO: '#e65100',
      ALTO: '#b71c1c',
    };
    return mapa[nivel] ?? '#757575';
  }

  formatarIndicador(indicador: IndicadorIA | IndicadorRisco): string {
    return indicador.tipo.replaceAll('_', ' ');
  }

  formatarEncaminhamento(valor: string): string {
    const mapa: Record<string, string> = {
      CAPS: 'CAPS',
      CVR: 'CVR',
      ASSISTENCIA_SOCIAL: 'Assistência Social',
      PSICOLOGIA: 'Psicologia',
      SERVICO_SOCIAL: 'Serviço Social',
      DELEGACIA_MULHER: 'Delegacia da Mulher',
      PRE_NATAL_ALTO_RISCO: 'Pré-natal Alto Risco',
    };
    return mapa[valor] ?? valor;
  }

  formatarDataPeso(iso: string): string {
    return new Date(iso).toLocaleDateString('pt-BR');
  }

  formatarPeso(kg: number): string {
    return kg.toFixed(1).replace('.', ',') + ' kg';
  }

  private mapearLinhas(hist: HistoricoPesoItem[]): LinhaPeso[] {
    return hist.map((item, i) => ({
      pesoKg: item.pesoKg,
      registradoEm: item.registradoEm,
      variacaoTexto: this.calcularVariacaoTexto(hist, i),
      variacaoCor: this.calcularVariacaoCor(hist, i),
    }));
  }

  private calcularVariacaoTexto(hist: HistoricoPesoItem[], index: number): string {
    if (index >= hist.length - 1) return '—';
    const diff = hist[index].pesoKg - hist[index + 1].pesoKg;
    if (diff === 0) return '—';
    const abs = Math.abs(diff).toFixed(1).replace('.', ',');
    return diff > 0 ? `▲ +${abs} kg` : `▼ −${abs} kg`;
  }

  private calcularVariacaoCor(hist: HistoricoPesoItem[], index: number): string {
    if (index >= hist.length - 1) return '';
    const diff = hist[index].pesoKg - hist[index + 1].pesoKg;
    if (diff > 5 || diff < -5) return '#b71c1c';
    if (diff > 2 || diff < -2) return '#e65100';
    return '';
  }

  private calcularTendencia(hist: HistoricoPesoItem[]): string {
    if (hist.length < 3) return '';
    const totalDiff = Math.abs(hist[0].pesoKg - hist[hist.length - 1].pesoKg);
    if (totalDiff < 1) return 'estável';
    let todosGanhos = true;
    let todasPerdas = true;
    for (let i = 0; i < hist.length - 1; i++) {
      const diff = hist[i].pesoKg - hist[i + 1].pesoKg;
      if (diff <= 0) todosGanhos = false;
      if (diff >= 0) todasPerdas = false;
    }
    if (todosGanhos) return 'ganho progressivo';
    if (todasPerdas) return 'perda progressiva';
    return 'variação irregular';
  }
}
