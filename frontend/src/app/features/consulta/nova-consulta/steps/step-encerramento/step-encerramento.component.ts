import { Component, effect, inject, input, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { forkJoin } from 'rxjs';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipListboxChange, MatChipsModule } from '@angular/material/chips';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { IndicadorIA, ResultadoIAOut, EncerramentoCreate, EncerramentoOut } from '../../../models/consulta.model';
import { ConsultaService } from '../../../services/consulta.service';
import { EncerramentoService } from '../../../services/encerramento.service';
import { ResultadoService } from '../../../services/resultado.service';
import { ConfirmarEncerramentoDialogComponent } from './confirmar-encerramento-dialog.component';

interface OpcaoEncaminhamento {
  valor: string;
  label: string;
}

@Component({
  selector: 'app-step-encerramento',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatDatepickerModule,
    MatDialogModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
  ],
  templateUrl: './step-encerramento.component.html',
  styles: [`
    .container { padding: 24px 0; max-width: 800px; }
    .section { margin-bottom: 20px; }
    .resultado-card { margin-bottom: 24px; }
    .score-display { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
    .score-num { font-size: 28px; font-weight: 700; line-height: 1; }
    .faixa-badge {
      padding: 4px 12px; border-radius: 16px; color: #fff;
      font-size: 13px; font-weight: 600;
    }
    .indicadores { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
    .indicador-chip {
      padding: 4px 10px; border-radius: 12px;
      font-size: 12px; font-weight: 500; background: rgba(0,0,0,.06);
    }
    .full-width { width: 100%; }
    .alerta-card { margin-bottom: 12px; }
    .alerta-card mat-card-content {
      display: flex; align-items: center; gap: 8px; font-weight: 500;
    }
    .encaminhamentos-label { font-weight: 500; margin-bottom: 8px; color: rgba(0,0,0,.6); }
    .chips-wrap { display: flex; flex-wrap: wrap; gap: 8px; }
    .actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 8px; }
    .conclusao {
      display: flex; flex-direction: column; align-items: center;
      gap: 16px; padding: 40px 0; text-align: center;
    }
    .conclusao .check-icon { font-size: 72px; width: 72px; height: 72px; color: #2e7d32; }
    .conclusao h2 { margin: 0; font-size: 22px; }
    .score-final { display: flex; flex-direction: column; align-items: center; gap: 4px; }
    .score-final .num { font-size: 40px; font-weight: 700; line-height: 1; }
    .score-final .label { font-size: 16px; font-weight: 500; }
    .conclusao-actions { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; }
    .loading { display: flex; align-items: center; gap: 16px; padding: 32px 0; }
  `],
})
export class StepEncerramentoComponent {
  readonly pronto = input(false);

  private readonly fb = inject(FormBuilder);
  private readonly consultaService = inject(ConsultaService);
  private readonly resultadoService = inject(ResultadoService);
  private readonly encerramentoService = inject(EncerramentoService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  private readonly router = inject(Router);

  readonly carregando = signal(false);
  readonly salvando = signal(false);
  readonly encerrado = signal(false);

  resultado: ResultadoIAOut | null = null;
  encerramento: EncerramentoOut | null = null;

  readonly encaminhamentosSelecionados = signal<string[]>([]);
  readonly minData = new Date();

  readonly form = this.fb.group({
    conduta: ['', [Validators.required, Validators.minLength(10)]],
    dataProximoRetorno: [null as Date | null, Validators.required],
    observacoes: [''],
  });

  readonly encaminhamentosDisponiveis: OpcaoEncaminhamento[] = [
    { valor: 'CAPS', label: 'CAPS' },
    { valor: 'CVR', label: 'CVR' },
    { valor: 'ASSISTENCIA_SOCIAL', label: 'Assistência Social' },
    { valor: 'PSICOLOGIA', label: 'Psicologia' },
    { valor: 'SERVICO_SOCIAL', label: 'Serviço Social' },
    { valor: 'DELEGACIA_MULHER', label: 'Delegacia da Mulher' },
    { valor: 'PRE_NATAL_ALTO_RISCO', label: 'Pré-natal Alto Risco' },
    { valor: 'OUTRO', label: 'Outro' },
  ];

  private inicializado = false;

  constructor() {
    effect(() => {
      if (this.pronto() && !this.inicializado) {
        const ativa = this.consultaService.consultaAtiva();
        if (ativa) {
          this.inicializado = true;
          this.inicializar(ativa.idConsulta);
        }
      }
    });
  }

  private inicializar(idConsulta: string): void {
    this.carregando.set(true);
    forkJoin({
      resultado: this.resultadoService.obter(idConsulta),
      sugestao: this.encerramentoService.obterSugestao(idConsulta),
    }).subscribe({
      next: ({ resultado, sugestao }) => {
        this.resultado = resultado;
        this.encaminhamentosSelecionados.set(sugestao.encaminhamentosSugeridos);

        const [ano, mes, dia] = sugestao.dataSugerida.split('-').map(Number);
        this.form.patchValue({
          conduta: sugestao.condutaSugerida,
          dataProximoRetorno: new Date(ano, mes - 1, dia),
        });
        this.carregando.set(false);
      },
      error: () => {
        this.carregando.set(false);
        this.snackBar.open('Erro ao carregar dados da consulta.', 'Fechar', { duration: 4000 });
      },
    });
  }

  onEncaminhamentosChange(event: MatChipListboxChange): void {
    this.encaminhamentosSelecionados.set(event.value ?? []);
  }

  isEncSelecionado(valor: string): boolean {
    return this.encaminhamentosSelecionados().includes(valor);
  }

  confirmarEncerramento(): void {
    if (this.form.invalid) return;
    const ref = this.dialog.open(ConfirmarEncerramentoDialogComponent, { width: '380px' });
    ref.afterClosed().subscribe((confirmado: boolean) => {
      if (confirmado) this.encerrar();
    });
  }

  private encerrar(): void {
    const ativa = this.consultaService.consultaAtiva();
    if (!ativa || this.form.invalid) return;

    const dataRetorno = this.form.value.dataProximoRetorno!;
    const dataStr = dataRetorno.toLocaleDateString('en-CA');

    const dados: EncerramentoCreate = {
      conduta: this.form.value.conduta!,
      encaminhamentos: this.encaminhamentosSelecionados(),
      dataProximoRetorno: dataStr,
      observacoes: this.form.value.observacoes || undefined,
    };

    this.salvando.set(true);
    this.encerramentoService.encerrar(ativa.idConsulta, dados).subscribe({
      next: (enc) => {
        this.encerramento = enc;
        this.salvando.set(false);
        this.encerrado.set(true);
      },
      error: () => {
        this.salvando.set(false);
        this.snackBar.open('Erro ao encerrar a consulta. Tente novamente.', 'Fechar', { duration: 4000 });
      },
    });
  }

  baixarPdf(): void {
    const id = this.consultaService.consultaAtiva()?.idConsulta;
    if (!id) return;
    this.encerramentoService.baixarResumoPdf(id).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `resumo-pec-${id}.pdf`;
        link.click();
        URL.revokeObjectURL(url);
      },
      error: () => this.snackBar.open('Erro ao gerar PDF.', 'Fechar', { duration: 4000 }),
    });
  }

  novaConsulta(): void {
    this.router.navigate(['/consulta/nova']);
  }

  voltarInicio(): void {
    this.router.navigate(['/home']);
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

  textoFaixa(faixa: string): string {
    const mapa: Record<string, string> = {
      VERDE: 'Baixo Risco',
      AMARELO: 'Risco Moderado',
      LARANJA: 'Risco Elevado',
      VERMELHO: 'Risco Alto',
    };
    return mapa[faixa] ?? faixa;
  }

  corNivel(nivel: string): string {
    const mapa: Record<string, string> = {
      BAIXO: '#2e7d32',
      MODERADO: '#e65100',
      ALTO: '#b71c1c',
    };
    return mapa[nivel] ?? '#757575';
  }

  get faixaRisco(): string {
    return this.resultado?.faixaRisco ?? '';
  }

  get precisaAlerta(): boolean {
    return this.faixaRisco === 'LARANJA' || this.faixaRisco === 'VERMELHO';
  }
}
