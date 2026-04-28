import {
  Component, EventEmitter, Input, OnChanges, OnDestroy, Output, SimpleChanges, inject, signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { AlertaResultado, FaixaRisco, ResultadoOut } from '../../../../models/consulta.model';
import { ResultadoService } from '../../../../services/resultado.service';

@Component({
  selector: 'app-painel-ia',
  standalone: true,
  imports: [
    FormsModule,
    MatButtonModule, MatIconModule, MatDividerModule,
    MatProgressBarModule, MatProgressSpinnerModule, MatSnackBarModule,
  ],
  templateUrl: './painel-ia.component.html',
})
export class PainelIaComponent implements OnChanges, OnDestroy {
  @Input() idConsulta!: string;
  @Input() resultado: ResultadoOut | null = null;
  @Output() confirmado = new EventEmitter<void>();

  private readonly svc = inject(ResultadoService);
  private readonly snack = inject(MatSnackBar);

  readonly salvandoTranscricao = signal(false);
  readonly confirmando = signal(false);
  transcricaoEditada = '';

  private _pollingInterval: ReturnType<typeof setInterval> | null = null;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['resultado'] && this.resultado) {
      this.transcricaoEditada = this.resultado.transcricaoEditada ?? this.resultado.transcricao ?? '';
      if (this.resultado.statusAudio === 'PROCESSANDO') {
        this._iniciarPolling();
      }
    }
  }

  ngOnDestroy(): void {
    this._pararPolling();
  }

  private _iniciarPolling(): void {
    this._pararPolling();
    this._pollingInterval = setInterval(() => {
      this.svc.obter(this.idConsulta).subscribe({
        next: (res) => {
          if (res.statusAudio !== 'PROCESSANDO') {
            this.resultado = res;
            this.transcricaoEditada = res.transcricaoEditada ?? res.transcricao ?? '';
            this._pararPolling();
          }
        },
        error: () => this._pararPolling(),
      });
    }, 10000);
  }

  private _pararPolling(): void {
    if (this._pollingInterval) {
      clearInterval(this._pollingInterval);
      this._pollingInterval = null;
    }
  }

  get corFaixa(): string {
    const mapa: Record<FaixaRisco, string> = {
      VERDE: '#388e3c', AMARELO: '#f9a825', LARANJA: '#e65100', VERMELHO: '#d32f2f',
    };
    return mapa[this.resultado?.faixaRisco ?? 'VERDE'];
  }

  get labelFaixa(): string {
    const mapa: Record<FaixaRisco, string> = {
      VERDE: 'Baixo risco — acompanhamento de rotina',
      AMARELO: 'Risco moderado — atenção aumentada',
      LARANJA: 'Risco elevado — intervenção recomendada',
      VERMELHO: 'Risco crítico — encaminhamento imediato',
    };
    return mapa[this.resultado?.faixaRisco ?? 'VERDE'];
  }

  get alertasCriticos(): AlertaResultado[] {
    return (this.resultado?.alertas ?? []).filter(a => a.nivel === 'CRITICO');
  }

  get alertasAtencao(): AlertaResultado[] {
    return (this.resultado?.alertas ?? []).filter(a => a.nivel === 'ATENCAO');
  }

  get alertasInfo(): AlertaResultado[] {
    return (this.resultado?.alertas ?? []).filter(a => a.nivel === 'INFO');
  }

  corBorda(nivel: string): string {
    if (nivel === 'CRITICO') return '#d32f2f';
    if (nivel === 'ATENCAO') return '#f57c00';
    return '#1976d2';
  }

  corFundo(nivel: string): string {
    if (nivel === 'CRITICO') return '#ffebee';
    if (nivel === 'ATENCAO') return '#fff3e0';
    return '#e3f2fd';
  }

  origemLabel(origem: string): string {
    const mapa: Record<string, string> = {
      ESTRUTURADO: 'Dados Clínicos', PSICOSSOCIAL: 'Psicossocial', AUDIO: 'Áudio',
    };
    return mapa[origem] ?? origem;
  }

  copiarResumo(): void {
    const texto = this.resultado?.resumoEncaminhamento ?? '';
    navigator.clipboard.writeText(texto).then(() => {
      this.snack.open('Resumo copiado.', 'OK', { duration: 2000 });
    });
  }

  salvarTranscricao(): void {
    this.salvandoTranscricao.set(true);
    this.svc.salvarTranscricao(this.idConsulta, this.transcricaoEditada).subscribe({
      next: () => {
        this.salvandoTranscricao.set(false);
        this.snack.open('Transcrição atualizada.', 'OK', { duration: 3000 });
      },
      error: () => {
        this.salvandoTranscricao.set(false);
        this.snack.open('Erro ao salvar transcrição.', 'OK', { duration: 3000 });
      },
    });
  }

  confirmarLeitura(): void {
    this.confirmando.set(true);
    this.svc.confirmar(this.idConsulta).subscribe({
      next: () => {
        this.confirmando.set(false);
        if (this.resultado) this.resultado = { ...this.resultado, confirmado: true };
        this.confirmado.emit();
        this.snack.open('Leitura do resultado confirmada.', 'OK', { duration: 3000 });
      },
      error: () => {
        this.confirmando.set(false);
        this.snack.open('Erro ao confirmar resultado.', 'OK', { duration: 3000 });
      },
    });
  }
}
