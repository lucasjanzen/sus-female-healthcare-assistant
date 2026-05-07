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

import { ConsultaAssumidaOut } from 'app/features/fila/models/fila.model';
import { FilaService } from 'app/features/fila/services/fila.service';
import { IndicadorIA, ResultadoIAOut } from 'app/features/consulta/models/consulta.model';
import { ConsultaService } from 'app/features/consulta/services/consulta.service';
import { RelatoService } from 'app/features/consulta/services/relato.service';
import { ResultadoService } from 'app/features/consulta/services/resultado.service';
import { AzureSpeechRecognitionService } from 'app/core/services/azure-speech-recognition.service';

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
  private readonly speechService = inject(AzureSpeechRecognitionService);
  private readonly resultadoService = inject(ResultadoService);
  private readonly filaService = inject(FilaService);
  private readonly snackBar = inject(MatSnackBar);

  readonly consultaAtiva = computed(() => this.consultaService.consultaAtiva());
  readonly dadosConsulta = signal<ConsultaAssumidaOut | null>(null);
  readonly resultado = signal<ResultadoIAOut | null>(null);
  readonly analisando = signal(false);
  readonly gravando = signal(false);
  readonly segundosGravacao = signal(0);
  /** Texto sendo reconhecido em tempo real (resultado parcial — ainda pode mudar). */
  readonly textoParcial = signal('');

  private timer?: number;

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
    this.filaService.emAndamento().subscribe((consulta) => {
      this.dadosConsulta.set(consulta);
    });

    const id = this.consultaAtiva()?.idConsulta;
    if (id) {
      this.relatoService.obter(id).subscribe({
        next: (relato) =>
          this.form.patchValue({
            relatoTexto: relato.relatoTexto ?? '',
            parecerMedico: relato.parecerMedico ?? '',
          }),
        error: () => undefined,
      });
    }

    // Resultados do Azure Speech SDK:
    // - 'partial': atualiza preview em tempo real (não grava no textarea ainda)
    // - 'final': acumula frase completa no campo de relato
    this.speechService.result$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((result) => {
      if (result.type === 'partial') {
        this.textoParcial.set(result.text);
      } else {
        this.textoParcial.set('');
        const atual = this.form.controls.relatoTexto.value;
        const separador = atual.trim() ? ' ' : '';
        this.form.controls.relatoTexto.setValue(`${atual}${separador}${result.text}`);
      }
    });

    this.speechService.error$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((msg) => {
      this.snackBar.open(msg, 'Fechar', { duration: 5000 });
      this.gravando.set(false);
      if (this.timer) window.clearInterval(this.timer);
    });
  }

  ngOnDestroy(): void {
    if (this.timer) window.clearInterval(this.timer);
    // Libera microfone e fecha socket do Azure Speech
    this.speechService.destroy();
  }

  salvarRelato(): void {
    const id = this.consultaAtiva()?.idConsulta;
    const relatoTexto = this.form.controls.relatoTexto.value.trim();
    if (!id || relatoTexto.length < 20) return;
    this.relatoService.atualizar(id, { relatoTexto }).subscribe({
      error: () => this.relatoService.criar(id, relatoTexto).subscribe(),
    });
  }

  salvarParecer(): void {
    const id = this.consultaAtiva()?.idConsulta;
    if (!id) return;
    this.relatoService
      .atualizar(id, { parecerMedico: this.form.controls.parecerMedico.value })
      .subscribe({
        error: () => this.snackBar.open('Erro ao salvar parecer', 'Fechar', { duration: 3000 }),
      });
  }

  iniciarGravacao(): void {
    this.speechService.iniciar().subscribe({
      next: () => {
        this.gravando.set(true);
        this.segundosGravacao.set(0);
        this.timer = window.setInterval(() => this.segundosGravacao.update((v) => v + 1), 1000);
      },
      error: () => {
        this.snackBar.open('Erro ao iniciar reconhecimento de voz', 'Fechar', { duration: 4000 });
      },
    });
  }

  encerrarGravacao(): void {
    if (this.timer) window.clearInterval(this.timer);
    this.gravando.set(false);
    this.speechService.parar().then(() => {
      this.textoParcial.set('');
    });
  }

  analisar(): void {
    const id = this.consultaAtiva()?.idConsulta;
    if (!id) return;
    this.salvarRelato();
    this.analisando.set(true);
    this.resultadoService.analisar(id).subscribe({
      next: (resultado) => {
        this.resultado.set(resultado);
        this.form.controls.parecerMedico.setValue(resultado.resumoIa);
        this.analisando.set(false);
      },
      error: () => {
        this.snackBar.open('Erro ao analisar relato', 'Fechar', { duration: 3000 });
        this.analisando.set(false);
      },
    });
  }

  confirmarAnalise(): void {
    const id = this.consultaAtiva()?.idConsulta;
    if (!id) return;
    this.salvarParecer();
    this.resultadoService.confirmar(id).subscribe({
      next: () => this.confirmado.emit(),
      error: () => this.snackBar.open('Erro ao confirmar análise', 'Fechar', { duration: 3000 }),
    });
  }

  tempoGravacao(): string {
    const segundos = this.segundosGravacao();
    return `${Math.floor(segundos / 60)}:${String(segundos % 60).padStart(2, '0')}`;
  }

  textoFaixa(resultado: ResultadoIAOut): string {
    const textos = {
      VERDE: 'Nenhum indicador significativo',
      AMARELO: 'Indicadores leves - atenção recomendada',
      LARANJA: 'Indicadores moderados - intervenção recomendada',
      VERMELHO: 'Indicadores críticos - encaminhamento imediato',
    };
    return textos[resultado.faixaRisco];
  }

  formatarIndicador(indicador: IndicadorIA): string {
    return indicador.tipo.replaceAll('_', ' ');
  }
}
