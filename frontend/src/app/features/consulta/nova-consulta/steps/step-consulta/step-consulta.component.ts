import {
  Component,
  EventEmitter,
  OnDestroy,
  OnInit,
  Output,
  computed,
  inject,
  signal,
} from '@angular/core';
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

import { ConsultaAssumidaOut } from '../../../../fila/models/fila.model';
import { FilaService } from '../../../../fila/services/fila.service';
import { IndicadorIA, ResultadoIAOut } from '../../../models/consulta.model';
import { AudioService } from '../../../services/audio.service';
import { ConsultaService } from '../../../services/consulta.service';
import { RelatoService } from '../../../services/relato.service';
import { ResultadoService } from '../../../services/resultado.service';

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
  private readonly consultaService = inject(ConsultaService);
  private readonly relatoService = inject(RelatoService);
  private readonly audioService = inject(AudioService);
  private readonly resultadoService = inject(ResultadoService);
  private readonly filaService = inject(FilaService);
  private readonly snackBar = inject(MatSnackBar);

  readonly consultaAtiva = computed(() => this.consultaService.consultaAtiva());
  readonly dadosConsulta = signal<ConsultaAssumidaOut | null>(null);
  readonly resultado = signal<ResultadoIAOut | null>(null);
  readonly analisando = signal(false);
  readonly gravando = signal(false);
  readonly audioStatus = signal('AGUARDANDO');
  readonly segundosGravacao = signal(0);

  private timer?: number;
  private polling?: number;

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
    if (!id) return;
    this.relatoService.obter(id).subscribe({
      next: (relato) =>
        this.form.patchValue({
          relatoTexto: relato.relatoTexto ?? '',
          parecerMedico: relato.parecerMedico ?? '',
        }),
      error: () => undefined,
    });
  }

  ngOnDestroy(): void {
    if (this.timer) window.clearInterval(this.timer);
    if (this.polling) window.clearInterval(this.polling);
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
        error: () =>
          this.snackBar.open('Erro ao salvar parecer', 'Fechar', {
            duration: 3000,
          }),
      });
  }

  iniciarGravacao(): void {
    const id = this.consultaAtiva()?.idConsulta;
    if (!id) return;
    this.audioService.iniciar(id).subscribe({
      next: () => {
        this.gravando.set(true);
        this.segundosGravacao.set(0);
        this.timer = window.setInterval(() => this.segundosGravacao.update((v) => v + 1), 1000);
      },
      error: () =>
        this.snackBar.open('Erro ao iniciar gravação', 'Fechar', {
          duration: 3000,
        }),
    });
  }

  encerrarGravacao(): void {
    const id = this.consultaAtiva()?.idConsulta;
    if (!id) return;
    if (this.timer) window.clearInterval(this.timer);
    this.gravando.set(false);
    this.audioStatus.set('PROCESSANDO');
    this.audioService.encerrar(id).subscribe({
      next: () => this.iniciarPollingAudio(id),
      error: () =>
        this.snackBar.open('Erro ao encerrar gravação', 'Fechar', {
          duration: 3000,
        }),
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
        this.snackBar.open('Erro ao analisar relato', 'Fechar', {
          duration: 3000,
        });
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
      error: () =>
        this.snackBar.open('Erro ao confirmar análise', 'Fechar', {
          duration: 3000,
        }),
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

  private iniciarPollingAudio(id: string): void {
    this.audioStatus.set('Áudio enviado para transcrição...');
    this.polling = window.setInterval(() => {
      this.audioService.status(id).subscribe((status) => {
        this.audioStatus.set(status.status_processamento);
        if (status.status_processamento === 'CONCLUIDO' && status.transcricao) {
          window.clearInterval(this.polling);
          const atual = this.form.controls.relatoTexto.value;
          this.form.controls.relatoTexto.setValue(
            `${atual}\n\n--- Transcrição do áudio ---\n${status.transcricao}`.trim(),
          );
        }
      });
    }, 10000);
  }
}
