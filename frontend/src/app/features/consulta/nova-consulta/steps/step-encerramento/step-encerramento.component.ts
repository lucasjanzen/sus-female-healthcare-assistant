import {
  Component,
  EventEmitter,
  Input,
  OnInit,
  Output,
  inject,
  signal,
} from '@angular/core';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import {
  ConsultaAtiva,
  Encaminhamento,
  EncerramentoCreate,
  EncerramentoOut,
  Etapa1Out,
  FaixaRisco,
  ResultadoOut,
  VacinaAplicada,
} from '../../../models/consulta.model';
import { EncerramentoService } from '../../../services/encerramento.service';
import { ConfirmEncerramentoDialogComponent } from './confirm-encerramento-dialog.component';

export const ORIENTACOES: { value: string; label: string }[] = [
  { value: 'NUTRICAO', label: 'Orientação Nutricional' },
  { value: 'VACINACAO', label: 'Atualização Vacinal' },
  { value: 'ALEITAMENTO_MATERNO', label: 'Aleitamento Materno' },
  { value: 'SINAIS_ALARME', label: 'Sinais de Alarme' },
  { value: 'ATIVIDADE_FISICA', label: 'Atividade Física' },
  { value: 'SAUDE_MENTAL', label: 'Saúde Mental' },
  { value: 'VIOLENCIA_DOMESTICA', label: 'Violência Doméstica' },
  { value: 'SUPORTE_SOCIAL', label: 'Suporte Social' },
  { value: 'RETORNO_CONSULTA', label: 'Retorno à Consulta' },
];

export const VACINAS = ['DT', 'HEPATITE_B', 'INFLUENZA', 'OUTRO'];
export const DESTINOS: { value: string; label: string }[] = [
  { value: 'CAPS', label: 'CAPS — Centro de Atenção Psicossocial' },
  { value: 'CVR', label: 'CVR — Centro de Valorização da Vida' },
  { value: 'ASSISTENCIA_SOCIAL', label: 'Assistência Social' },
  { value: 'PRE_NATAL_ALTO_RISCO', label: 'Pré-Natal de Alto Risco' },
  { value: 'PSICOLOGIA', label: 'Psicologia' },
  { value: 'SERVICO_SOCIAL', label: 'Serviço Social' },
  { value: 'DELEGACIA_MULHER', label: 'Delegacia da Mulher' },
  { value: 'OUTRO', label: 'Outro' },
];

@Component({
  selector: 'app-step-encerramento',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatCheckboxModule,
    MatDatepickerModule,
    MatDialogModule,
    MatDividerModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatSnackBarModule,
  ],
  templateUrl: './step-encerramento.component.html',
})
export class StepEncerramentoComponent implements OnInit {
  @Input() consultaAtiva!: ConsultaAtiva;
  @Input() etapa1!: Etapa1Out;
  @Input() resultado!: ResultadoOut;

  private readonly svc = inject(EncerramentoService);
  private readonly dialog = inject(MatDialog);
  private readonly snack = inject(MatSnackBar);
  private readonly router = inject(Router);

  readonly orientacoes = ORIENTACOES;
  readonly vacinas = VACINAS;
  readonly destinos = DESTINOS;

  // form state
  readonly orientacoesSelecionadas = signal(new Set<string>());
  readonly vacinasList = signal<VacinaAplicada[]>([]);
  readonly encaminhamentosList = signal<Encaminhamento[]>([]);
  readonly cartaoGestante = signal(false);
  readonly observacoesFinais = signal('');
  readonly dataRetornoCtrl = new FormControl<Date | null>(null, Validators.required);

  // inline form state
  readonly exibirFormVacina = signal(false);
  readonly novaVacina = signal('');
  readonly novaVacinaLote = signal('');
  readonly novaVacinaData = new FormControl<Date | null>(null);

  readonly exibirFormEncaminhamento = signal(false);
  readonly novoEncDestino = signal('');
  readonly novoEncMotivo = signal('');

  readonly carregando = signal(false);
  readonly encerrando = signal(false);
  readonly concluido = signal(false);
  readonly encerradoOut = signal<EncerramentoOut | null>(null);
  readonly baixandoPdf = signal(false);

  readonly dataMinima = new Date();

  ngOnInit(): void {
    this.svc.obterSugestao(this.consultaAtiva.idConsulta).subscribe({
      next: (s) => {
        const [ano, mes, dia] = s.dataProximoRetornoSugerida.split('-').map(Number);
        this.dataRetornoCtrl.setValue(new Date(ano, mes - 1, dia));
        this.orientacoesSelecionadas.set(new Set(s.orientacoesRecomendadas));
      },
      error: () => {
        this.snack.open('Não foi possível carregar sugestão de retorno.', 'OK', { duration: 3000 });
      },
    });
  }

  get idConsulta(): string {
    return this.consultaAtiva.idConsulta;
  }

  get faixaRisco(): FaixaRisco {
    return this.resultado?.faixaRisco ?? 'VERDE';
  }

  get corFaixa(): string {
    const cores: Record<FaixaRisco, string> = {
      VERDE: '#2e7d32',
      AMARELO: '#f9a825',
      LARANJA: '#e65100',
      VERMELHO: '#c62828',
    };
    return cores[this.faixaRisco];
  }

  get bgFaixa(): string {
    const bgs: Record<FaixaRisco, string> = {
      VERDE: '#e8f5e9',
      AMARELO: '#fff8e1',
      LARANJA: '#fff3e0',
      VERMELHO: '#ffebee',
    };
    return bgs[this.faixaRisco];
  }

  get alertasCriticos(): string[] {
    return (this.resultado?.alertas ?? [])
      .filter((a) => a.nivel === 'CRITICO')
      .map((a) => a.descricao);
  }

  get mostrarAlertaEncaminhamento(): boolean {
    return this.faixaRisco === 'LARANJA' || this.faixaRisco === 'VERMELHO';
  }

  get podeEncerrar(): boolean {
    return (
      this.orientacoesSelecionadas().size > 0 &&
      this.dataRetornoCtrl.valid &&
      this.cartaoGestante()
    );
  }

  toggleOrientacao(valor: string): void {
    const set = new Set(this.orientacoesSelecionadas());
    set.has(valor) ? set.delete(valor) : set.add(valor);
    this.orientacoesSelecionadas.set(set);
  }

  isOrientacaoSelecionada(valor: string): boolean {
    return this.orientacoesSelecionadas().has(valor);
  }

  adicionarVacina(): void {
    if (!this.novaVacina() || !this.novaVacinaData.value) return;
    const d = this.novaVacinaData.value;
    const dataStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    this.vacinasList.update((list) => [
      ...list,
      { vacina: this.novaVacina(), lote: this.novaVacinaLote() || undefined, dataAplicacao: dataStr },
    ]);
    this.novaVacina.set('');
    this.novaVacinaLote.set('');
    this.novaVacinaData.setValue(null);
    this.exibirFormVacina.set(false);
  }

  removerVacina(index: number): void {
    this.vacinasList.update((list) => list.filter((_, i) => i !== index));
  }

  adicionarEncaminhamento(): void {
    if (!this.novoEncDestino() || !this.novoEncMotivo()) return;
    this.encaminhamentosList.update((list) => [
      ...list,
      { destino: this.novoEncDestino(), motivo: this.novoEncMotivo() },
    ]);
    this.novoEncDestino.set('');
    this.novoEncMotivo.set('');
    this.exibirFormEncaminhamento.set(false);
  }

  removerEncaminhamento(index: number): void {
    this.encaminhamentosList.update((list) => list.filter((_, i) => i !== index));
  }

  labelDestino(valor: string): string {
    return DESTINOS.find((d) => d.value === valor)?.label ?? valor;
  }

  confirmarEncerramento(): void {
    const ref = this.dialog.open(ConfirmEncerramentoDialogComponent, {
      width: '380px',
    });
    ref.afterClosed().subscribe((confirmado) => {
      if (confirmado) this._encerrar();
    });
  }

  private _encerrar(): void {
    const dataRetorno = this.dataRetornoCtrl.value!;
    const dataStr = `${dataRetorno.getFullYear()}-${String(dataRetorno.getMonth() + 1).padStart(2, '0')}-${String(dataRetorno.getDate()).padStart(2, '0')}`;

    const payload: EncerramentoCreate = {
      orientacoes: Array.from(this.orientacoesSelecionadas()),
      vacinacao: this.vacinasList().length > 0 ? this.vacinasList() : undefined,
      dataProximoRetorno: dataStr,
      encaminhamentos: this.encaminhamentosList().length > 0 ? this.encaminhamentosList() : undefined,
      cartaoGestanteAtualizado: this.cartaoGestante(),
      observacoesFinais: this.observacoesFinais() || undefined,
    };

    this.encerrando.set(true);
    this.svc.encerrar(this.idConsulta, payload).subscribe({
      next: (out) => {
        this.encerrando.set(false);
        this.encerradoOut.set(out);
        this.concluido.set(true);
      },
      error: () => {
        this.encerrando.set(false);
        this.snack.open('Erro ao encerrar consulta. Tente novamente.', 'OK', { duration: 4000 });
      },
    });
  }

  baixarPdf(): void {
    this.baixandoPdf.set(true);
    this.svc.baixarResumoPdf(this.idConsulta).subscribe({
      next: (blob) => {
        this.baixandoPdf.set(false);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `resumo_pec_${this.idConsulta}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
      },
      error: () => {
        this.baixandoPdf.set(false);
        this.snack.open('Erro ao gerar PDF.', 'OK', { duration: 3000 });
      },
    });
  }

  iniciarNovaConsulta(): void {
    this.router.navigate(['/consulta/nova']);
  }

  voltarHome(): void {
    this.router.navigate(['/home']);
  }
}
