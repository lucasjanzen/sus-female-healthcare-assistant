import {
  Component,
  EventEmitter,
  Input,
  Output,
  computed,
  input,
  inject,
} from '@angular/core';
import { ReactiveFormsModule, FormControl } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { NotificationService } from 'app/core/services/notification.service';
import { extrairMensagemErro } from 'app/core/utils/http-error.utils';
import { IndicadorIA, IndicadorRisco, ResultadoIAOut } from 'app/features/consulta/models/consulta.model';
import { RelatoService } from 'app/features/consulta/services/relato.service';
import { ResultadoService } from 'app/features/consulta/services/resultado.service';

@Component({
  selector: 'app-consulta-resultado',
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
    MatSnackBarModule,
  ],
  templateUrl: './consulta-resultado.component.html',
  styleUrl: './consulta-resultado.component.scss',
})
export class ConsultaResultadoComponent {
  readonly resultado = input.required<ResultadoIAOut>();
  readonly idConsulta = input.required<string>();
  @Input() textoClinicoCtrl!: FormControl<string>;
  @Output() readonly confirmado = new EventEmitter<void>();

  private readonly relatoService = inject(RelatoService);
  private readonly resultadoService = inject(ResultadoService);
  private readonly snackBar = inject(MatSnackBar);
  private readonly notification = inject(NotificationService);

  readonly indicadoresVisiveis = computed(() =>
    (this.resultado().sumarioEstruturado?.indicadores ?? []).filter(
      (i): i is IndicadorRisco => i.nivel === 'MODERADO' || i.nivel === 'ALTO',
    ),
  );

  readonly pontosAtencao = computed(
    () => this.resultado().sumarioEstruturado?.pontosAtencao ?? [],
  );

  readonly encaminhamentosSugeridos = computed(
    () => this.resultado().sumarioEstruturado?.encaminhamentosSugeridos ?? [],
  );

  readonly modoFallback = computed(
    () => this.resultado().sumarioEstruturado?.modoFallback ?? false,
  );

  readonly respostaBrutaFormatada = computed(() => {
    const raw = this.resultado().respostaBrutaLlm;
    if (!raw) return '';
    try { return JSON.stringify(JSON.parse(raw), null, 2); } catch { return raw; }
  });

  salvarTextoClinico(): void {
    this.relatoService
      .atualizar(this.idConsulta(), { parecerMedico: this.textoClinicoCtrl.value })
      .subscribe({
        next: () => this.snackBar.open('Texto clínico salvo.', '', { duration: 2000 }),
        error: (err: HttpErrorResponse) =>
          this.notification.erro(extrairMensagemErro(err, 'Erro ao salvar texto clínico')),
      });
  }

  copiarTextoClinico(): void {
    const texto = this.textoClinicoCtrl.value;
    if (!texto) return;
    navigator.clipboard.writeText(texto).then(
      () => this.snackBar.open('Texto copiado!', '', { duration: 2000 }),
      () => this.notification.erro('Não foi possível copiar o texto'),
    );
  }

  copiarDebug(texto: string): void {
    if (!texto) return;
    navigator.clipboard.writeText(texto).then(
      () => this.snackBar.open('Copiado!', '', { duration: 1500 }),
      () => this.notification.erro('Não foi possível copiar'),
    );
  }

  confirmarAnalise(): void {
    this.salvarTextoClinico();
    this.resultadoService.confirmar(this.idConsulta()).subscribe({
      next: () => this.confirmado.emit(),
      error: (err: HttpErrorResponse) =>
        this.notification.erro(extrairMensagemErro(err, 'Erro ao confirmar análise')),
    });
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

  formatarIndicador(indicador: IndicadorIA | IndicadorRisco): string {
    return indicador.tipo
      .replaceAll('_', ' ')
      .toLowerCase()
      .replace(/\b\w/g, (c) => c.toUpperCase());
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
}
