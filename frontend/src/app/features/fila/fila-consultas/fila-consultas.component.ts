import { DatePipe } from '@angular/common';
import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { Subject, forkJoin, interval, takeUntil } from 'rxjs';
import { MatBadgeModule } from '@angular/material/badge';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { AuthService } from '../../../core/auth/auth.service';
import { ConsultaAssumidaOut, ConsultaFilaItem } from '../models/fila.model';
import { FilaService } from '../services/fila.service';

@Component({
  selector: 'app-fila-consultas',
  standalone: true,
  imports: [
    DatePipe,
    MatBadgeModule,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
  ],
  templateUrl: './fila-consultas.component.html',
  styles: [`
    .fila-page { padding: 24px; max-width: 1180px; margin: 0 auto; }
    .topbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 18px; }
    .title h1 { margin: 0; font-size: 1.6rem; font-weight: 600; }
    .title p { margin: 4px 0 0; color: #667085; }
    .actions { display: flex; align-items: center; gap: 12px; color: #667085; }
    .andamento { margin-bottom: 18px; background: #e3f2fd; border: 1px solid #90caf9; }
    .empty { min-height: 280px; display: grid; place-items: center; text-align: center; color: #667085; }
    .empty mat-icon { font-size: 54px; width: 54px; height: 54px; color: #90a4ae; }
    .lista { display: flex; flex-direction: column; gap: 12px; }
    .item { border: 1px solid #e0e0e0; box-shadow: none; }
    .item.proxima { border: 2px solid #1976d2; }
    .item-content { display: grid; grid-template-columns: 72px 1fr minmax(180px, 300px); gap: 18px; align-items: center; }
    .ordem { display: flex; align-items: center; gap: 8px; font-size: 1.6rem; font-weight: 700; color: #344054; }
    .alert-icon { color: #c62828; }
    .paciente h2 { margin: 0 0 8px; font-size: 1.1rem; }
    .meta { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; color: #667085; }
    .direita { display: flex; justify-content: flex-end; align-items: center; gap: 8px; flex-wrap: wrap; }
    .critico { background: #ffebee !important; color: #b71c1c !important; }
    .proxima-badge { background: #e3f2fd; color: #0d47a1; border-radius: 999px; padding: 4px 10px; font-size: 0.78rem; font-weight: 600; }
    @media (max-width: 820px) {
      .topbar, .actions { align-items: flex-start; flex-direction: column; }
      .item-content { grid-template-columns: 1fr; }
      .direita { justify-content: flex-start; }
    }
  `],
})
export class FilaConsultasComponent implements OnInit, OnDestroy {
  private readonly filaService = inject(FilaService);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly snack = inject(MatSnackBar);
  private readonly destroy$ = new Subject<void>();

  readonly consultas = signal<ConsultaFilaItem[]>([]);
  readonly emAndamento = signal<ConsultaAssumidaOut | null>(null);
  readonly carregando = signal(false);
  readonly assumindoId = signal<string | null>(null);
  readonly atualizadoEm = signal<Date | null>(null);
  readonly agora = signal(new Date());

  readonly total = computed(() => this.consultas().length);
  readonly ubsNome = computed(() => 'UBS vinculada');
  readonly usuario = computed(() => this.authService.getUser());

  ngOnInit(): void {
    this.carregarTudo();
    interval(30000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => this.carregarLista(false));
    interval(60000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => this.agora.set(new Date()));
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  carregarTudo(): void {
    this.carregando.set(true);
    forkJoin({
      consultas: this.filaService.listar(),
      emAndamento: this.filaService.emAndamento(),
    }).subscribe({
      next: ({ consultas, emAndamento }) => {
        this.consultas.set(consultas);
        this.emAndamento.set(emAndamento);
        this.atualizadoEm.set(new Date());
        this.carregando.set(false);
      },
      error: () => {
        this.carregando.set(false);
        this.snack.open('Erro ao carregar a fila de consultas.', 'OK', { duration: 4000 });
      },
    });
  }

  carregarLista(mostrarLoading = true): void {
    if (mostrarLoading) this.carregando.set(true);
    this.filaService.listar().subscribe({
      next: (consultas) => {
        this.consultas.set(consultas);
        this.atualizadoEm.set(new Date());
        if (mostrarLoading) this.carregando.set(false);
      },
      error: () => {
        if (mostrarLoading) this.carregando.set(false);
      },
    });
  }

  assumir(consulta: ConsultaFilaItem): void {
    this.assumindoId.set(consulta.idConsulta);
    this.filaService.assumir(consulta.idConsulta).subscribe({
      next: () => this.router.navigate(['/consulta', consulta.idConsulta, 'etapa2']),
      error: (error: HttpErrorResponse) => {
        this.assumindoId.set(null);
        if (error.status === 409) {
          this.snack.open('Esta consulta foi assumida por outro médico.', 'OK', { duration: 4000 });
          this.carregarTudo();
          return;
        }
        this.snack.open('Erro ao assumir consulta.', 'OK', { duration: 4000 });
      },
    });
  }

  continuar(consulta: ConsultaAssumidaOut): void {
    this.router.navigate(['/consulta', consulta.idConsulta, 'etapa2']);
  }

  tempoAguardando(dataIso: string): string {
    const diffMin = Math.max(0, Math.floor((this.agora().getTime() - new Date(dataIso).getTime()) / 60000));
    if (diffMin < 60) return `Aguardando há ${diffMin} min`;
    const horas = Math.floor(diffMin / 60);
    const minutos = diffMin % 60;
    return `Aguardando há ${horas}h ${minutos}min`;
  }

  formatarIg(item: ConsultaFilaItem): string | null {
    if (item.igSemanas == null) return null;
    return `${item.igSemanas} sem. e ${item.igDias ?? 0} dias`;
  }
}
