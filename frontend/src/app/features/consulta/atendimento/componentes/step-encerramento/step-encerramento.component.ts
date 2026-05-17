import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { catchError, forkJoin, of } from 'rxjs';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipListboxChange, MatChipsModule } from '@angular/material/chips';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { NotificationService } from 'app/core/services/notification.service';
import { extrairMensagemErro } from 'app/core/utils/http-error.utils';
import { ConsultaResultadoComponent } from '../consulta-resultado/consulta-resultado.component';

import {
  ResultadoIAOut,
  EncerramentoCreate,
  EncerramentoOut,
} from '../../../models/consulta.model';
import { ConsultaService } from '../../../services/consulta.service';
import { EncerramentoService } from '../../../services/encerramento.service';
import { RelatoService } from '../../../services/relato.service';
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
    ConsultaResultadoComponent,
  ],
  templateUrl: './step-encerramento.component.html',
  styleUrl: './step-encerramento.component.scss',
})
export class StepEncerramentoComponent {
  readonly pronto = input(false);

  private readonly fb = inject(FormBuilder);
  private readonly consultaService = inject(ConsultaService);
  private readonly resultadoService = inject(ResultadoService);
  private readonly encerramentoService = inject(EncerramentoService);
  private readonly relatoService = inject(RelatoService);
  private readonly dialog = inject(MatDialog);
  private readonly notification = inject(NotificationService);
  private readonly router = inject(Router);
  protected readonly idConsulta = computed(() => this.consultaService.consultaAtiva()?.idConsulta);

  private inicializado = false;
  readonly carregando = signal(false);
  readonly salvando = signal(false);
  readonly encerrado = signal(false);
  readonly resultado = signal<ResultadoIAOut | null>(null);
  readonly encaminhamentosSelecionados = signal<string[]>([]);
  readonly faixaRisco = computed(() => this.resultado()?.faixaRisco ?? '');
  readonly precisaAlerta = computed(
    () => this.faixaRisco() === 'LARANJA' || this.faixaRisco() === 'VERMELHO',
  );

  readonly minData = new Date();
  encerramento: EncerramentoOut | null = null;

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

  constructor() {
    effect(() => {
      if (this.pronto() && !this.inicializado) {
        const id = this.idConsulta();
        if (id) {
          this.inicializado = true;
          this.inicializar(id);
        }
      }
    });
  }

  private inicializar(idConsulta: string): void {
    this.carregando.set(true);

    forkJoin({
      resultado: this.resultadoService.obter(idConsulta),
      sugestao: this.encerramentoService.obterSugestao(idConsulta),
      relato: this.relatoService.obter(idConsulta).pipe(catchError(() => of({ parecerMedico: null as string | null | undefined }))),
    }).subscribe({
      next: ({ resultado, sugestao, relato }) => {
        this.resultado.set(resultado);

        // Encaminhamentos: preferir os do sumário LLM, depois os da sugestão de risco
        const encsLlm = resultado.sumarioEstruturado?.encaminhamentosSugeridos ?? [];
        this.encaminhamentosSelecionados.set(
          encsLlm.length > 0 ? encsLlm : sugestao.encaminhamentosSugeridos,
        );

        // Conduta: texto editado pelo médico > texto clínico do LLM > conduta sugerida
        const conduta =
          relato.parecerMedico ||
          resultado.textoClinico ||
          sugestao.condutaSugerida;

        this.form.patchValue({
          conduta,
          dataProximoRetorno: new Date(sugestao.dataSugerida),
        });
        this.carregando.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.carregando.set(false);
        this.notification.erro(extrairMensagemErro(err, 'Erro ao carregar dados da consulta.'));
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
    const id = this.idConsulta();
    if (!id || this.form.invalid) return;

    const dataRetorno = this.form.value.dataProximoRetorno!;
    const dataStr = dataRetorno.toISOString().split('T')[0];

    const dados: EncerramentoCreate = {
      conduta: this.form.value.conduta!,
      encaminhamentos: this.encaminhamentosSelecionados(),
      dataProximoRetorno: dataStr,
      observacoes: this.form.value.observacoes || undefined,
    };

    this.salvando.set(true);
    this.encerramentoService.encerrar(id, dados).subscribe({
      next: (enc) => {
        this.encerramento = enc;
        this.salvando.set(false);
        this.encerrado.set(true);
      },
      error: (err: HttpErrorResponse) => {
        this.salvando.set(false);
        this.notification.erro(extrairMensagemErro(err, 'Erro ao encerrar a consulta. Tente novamente.'));
      },
    });
  }

  baixarPdf(): void {
    const id = this.idConsulta();
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
      error: (err: HttpErrorResponse) => this.notification.erro(extrairMensagemErro(err, 'Erro ao gerar PDF.')),
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
}
