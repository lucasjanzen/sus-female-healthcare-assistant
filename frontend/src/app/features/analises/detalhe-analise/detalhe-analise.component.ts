import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { NotificationService } from '../../../core/services/notification.service';
import { extrairMensagemErro } from '../../../core/utils/http-error.utils';
import { ConsultaResultadoComponent } from '../../consulta/atendimento/componentes/consulta-resultado/consulta-resultado.component';
import { AnalisesService } from '../services/analises.service';
import { AnaliseResultadoOut, EncaminharRequest } from '../models/analise.model';
import { EncaminharDialogComponent } from './encaminhar-dialog.component';
import { ConfirmarRevisaoDialogComponent } from './confirmar-revisao-dialog.component';

@Component({
  selector: 'app-detalhe-analise',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatDialogModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    ConsultaResultadoComponent,
  ],
  templateUrl: './detalhe-analise.component.html',
  styleUrl: './detalhe-analise.component.scss',
})
export class DetalheAnaliseComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly analisesService = inject(AnalisesService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  private readonly notification = inject(NotificationService);
  private readonly fb = inject(FormBuilder);

  readonly idConsulta = signal('');
  readonly resultado = signal<AnaliseResultadoOut | null>(null);
  readonly carregando = signal(false);
  readonly salvando = signal(false);

  readonly parecerCtrl = this.fb.nonNullable.control('');

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.idConsulta.set(id);
    this.carregar(id);
  }

  private carregar(id: string): void {
    this.carregando.set(true);
    this.analisesService.obterResultado(id).subscribe({
      next: (res) => {
        this.resultado.set(res);
        this.carregando.set(false);
      },
      error: (err: HttpErrorResponse) => {
        this.notification.erro(extrairMensagemErro(err, 'Erro ao carregar resultado da análise'));
        this.carregando.set(false);
      },
    });
  }

  abrirEncaminhar(): void {
    const ref = this.dialog.open(EncaminharDialogComponent, { width: '420px' });
    ref.afterClosed().subscribe((dados: EncaminharRequest | undefined) => {
      if (dados !== undefined) this.encaminhar(dados);
    });
  }

  private encaminhar(dados: EncaminharRequest): void {
    this.salvando.set(true);
    this.analisesService.encaminhar(this.idConsulta(), dados).subscribe({
      next: () => {
        this.salvando.set(false);
        this.snackBar.open('Encaminhamento registrado com sucesso.', '', { duration: 3000 });
        this.router.navigate(['/analises']);
      },
      error: (err: HttpErrorResponse) => {
        this.salvando.set(false);
        this.notification.erro(extrairMensagemErro(err, 'Erro ao registrar encaminhamento'));
      },
    });
  }

  abrirRevisao(): void {
    const ref = this.dialog.open(ConfirmarRevisaoDialogComponent, { width: '380px' });
    ref.afterClosed().subscribe((confirmado: boolean) => {
      if (confirmado) this.revisar();
    });
  }

  private revisar(): void {
    this.salvando.set(true);
    this.analisesService.revisar(this.idConsulta()).subscribe({
      next: () => {
        this.salvando.set(false);
        this.router.navigate(['/analises']);
      },
      error: (err: HttpErrorResponse) => {
        this.salvando.set(false);
        this.notification.erro(extrairMensagemErro(err, 'Erro ao revisar análise'));
      },
    });
  }

  voltar(): void {
    this.router.navigate(['/analises']);
  }

  labelFaixa(faixa: string): string {
    const mapa: Record<string, string> = {
      VERDE: 'Baixo Risco',
      AMARELO: 'Risco Moderado',
      LARANJA: 'Risco Elevado',
      VERMELHO: 'Risco Crítico',
    };
    return mapa[faixa] ?? faixa;
  }

  corFaixa(faixa: string): string {
    const mapa: Record<string, string> = {
      VERDE: '#166534',
      AMARELO: '#854d0e',
      LARANJA: '#9a3412',
      VERMELHO: '#991b1b',
    };
    return mapa[faixa] ?? '#666';
  }

  corFundoFaixa(faixa: string): string {
    const mapa: Record<string, string> = {
      VERDE: '#dcfce7',
      AMARELO: '#fef9c3',
      LARANJA: '#ffedd5',
      VERMELHO: '#fee2e2',
    };
    return mapa[faixa] ?? '#f5f5f5';
  }

  formatarData(dataStr?: string): string {
    if (!dataStr) return '—';
    return new Date(dataStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}
