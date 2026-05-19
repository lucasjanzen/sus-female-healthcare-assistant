import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { NotificationService } from 'app/core/services/notification.service';
import { extrairMensagemErro } from 'app/core/utils/http-error.utils';
import { AnalisesService } from '../services/analises.service';
import { AnaliseFilaItem, FaixaRisco } from '../models/analise.model';

@Component({
  selector: 'app-fila-analises',
  standalone: true,
  imports: [
    NgTemplateOutlet,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatIconModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './fila-analises.component.html',
  styleUrl: './fila-analises.component.scss',
})
export class FilaAnalisesComponent implements OnInit, OnDestroy {
  private readonly analisesService = inject(AnalisesService);
  private readonly router = inject(Router);
  private readonly notification = inject(NotificationService);

  readonly items = signal<AnaliseFilaItem[]>([]);
  readonly carregando = signal(false);
  readonly revisandoId = signal<string | null>(null);
  readonly reprocessandoId = signal<string | null>(null);
  readonly atualizadoEm = signal<Date | null>(null);

  private polling?: number;
  private _inicialCarregado = false;

  readonly total = computed(() => this.items().length);
  readonly criticos = computed(
    () =>
      this.items().filter((i) => i.faixaRisco === 'LARANJA' || i.faixaRisco === 'VERMELHO').length,
  );

  readonly emProcessamento = computed(() => this.items().filter((i) => i.emProcessamento));
  readonly vermelho = computed(() =>
    this.items().filter((i) => !i.emProcessamento && i.faixaRisco === 'VERMELHO'),
  );
  readonly laranja = computed(() =>
    this.items().filter((i) => !i.emProcessamento && i.faixaRisco === 'LARANJA'),
  );
  readonly amarelo = computed(() =>
    this.items().filter((i) => !i.emProcessamento && i.faixaRisco === 'AMARELO'),
  );
  readonly verde = computed(() =>
    this.items().filter((i) => !i.emProcessamento && i.faixaRisco === 'VERDE'),
  );

  ngOnInit(): void {
    this.carregar();
    this.polling = window.setInterval(() => {
      this.carregar();
      this._ajustarPolling();
    }, 15000);
  }

  private _ajustarPolling(): void {
    const intervalo = this.emProcessamento().length > 0 ? 10000 : 60000;
    window.clearInterval(this.polling);
    this.polling = window.setInterval(() => {
      this.carregar();
      this._ajustarPolling();
    }, intervalo);
  }

  ngOnDestroy(): void {
    if (this.polling) window.clearInterval(this.polling);
  }

  carregar(): void {
    if (!this._inicialCarregado) this.carregando.set(true);
    this.analisesService.listarFila().subscribe({
      next: (items) => {
        this.items.set(items);
        this.atualizadoEm.set(new Date());
        this.carregando.set(false);
        this._inicialCarregado = true;
      },
      error: (err: HttpErrorResponse) => {
        this.notification.erro(extrairMensagemErro(err, 'Erro ao carregar fila de análises'));
        this.carregando.set(false);
        this._inicialCarregado = true;
      },
    });
  }

  verAnalise(idConsulta: string): void {
    this.router.navigate(['/analises', idConsulta]);
  }

  revisarSemEncaminhar(item: AnaliseFilaItem): void {
    this.revisandoId.set(item.idConsulta);
    this.analisesService.revisar(item.idConsulta).subscribe({
      next: () => {
        this.revisandoId.set(null);
        this.items.update((prev) => prev.filter((i) => i.idConsulta !== item.idConsulta));
        this.notification.sucesso('Análise marcada como revisada.', 3000);
      },
      error: (err: HttpErrorResponse) => {
        this.revisandoId.set(null);
        this.notification.erro(extrairMensagemErro(err, 'Erro ao revisar análise'));
      },
    });
  }

  horaAtualizacao(): string {
    const data = this.atualizadoEm();
    return data
      ? data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
      : '--:--';
  }

  formatarData(dataStr: string): string {
    const data = new Date(dataStr);
    const hoje = new Date();
    if (data.toDateString() === hoje.toDateString()) {
      return `Hoje às ${data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`;
    }
    return data.toLocaleDateString('pt-BR');
  }

  corFundo(faixa: FaixaRisco): string {
    const mapa: Record<FaixaRisco, string> = {
      VERDE: '#dcfce7',
      AMARELO: '#fef9c3',
      LARANJA: '#ffedd5',
      VERMELHO: '#fee2e2',
    };
    return mapa[faixa];
  }

  corTexto(faixa: FaixaRisco): string {
    const mapa: Record<FaixaRisco, string> = {
      VERDE: '#166534',
      AMARELO: '#854d0e',
      LARANJA: '#9a3412',
      VERMELHO: '#991b1b',
    };
    return mapa[faixa];
  }

  corBorda(faixa: FaixaRisco): string {
    const mapa: Record<FaixaRisco, string> = {
      VERDE: 'transparent',
      AMARELO: 'transparent',
      LARANJA: '#ea580c',
      VERMELHO: '#dc2626',
    };
    return mapa[faixa];
  }

  labelFaixa(faixa: FaixaRisco): string {
    const mapa: Record<FaixaRisco, string> = {
      VERDE: 'Baixo Risco',
      AMARELO: 'Risco Moderado',
      LARANJA: 'Risco Elevado',
      VERMELHO: 'Risco Crítico',
    };
    return mapa[faixa];
  }

  reprocessar(item: AnaliseFilaItem): void {
    this.reprocessandoId.set(item.idConsulta);
    this.analisesService.reprocessar(item.idConsulta).subscribe({
      next: () => {
        this.reprocessandoId.set(null);
        this.notification.sucesso('Análise reenfileirada para processamento.', 3000);
      },
      error: (err: HttpErrorResponse) => {
        this.reprocessandoId.set(null);
        this.notification.erro(extrairMensagemErro(err, 'Erro ao reprocessar análise'));
      },
    });
  }

  formatarIndicador(tipo: string): string {
    return tipo
      .replaceAll('_', ' ')
      .toLowerCase()
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }
}
