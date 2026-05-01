import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { ConsultaAssumidaOut, ConsultaFilaItem } from '../models/fila.model';
import { FilaService } from '../services/fila.service';

@Component({
  selector: 'app-fila-consultas',
  standalone: true,
  imports: [MatButtonModule, MatCardModule, MatChipsModule, MatIconModule, MatProgressSpinnerModule, MatSnackBarModule],
  templateUrl: './fila-consultas.component.html',
  styles: [`
    .page { padding: 24px; max-width: 960px; margin: 0 auto; }
    .banner { background: #e3f2fd; padding: 16px; border-radius: 8px; display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 20px; }
    .header { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 20px; }
    .title { display: flex; align-items: center; gap: 10px; }
    .badge { background: #1976d2; color: white; border-radius: 999px; padding: 3px 9px; font-size: 0.8rem; }
    .list { display: grid; gap: 12px; }
    .item { border-left: 4px solid transparent; }
    .next { border-left-color: #1976d2; }
    .row { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
    .patient { font-weight: 600; }
    .muted { color: #666; font-size: 0.9rem; }
    .empty { text-align: center; padding: 36px 12px; }
  `],
})
export class FilaConsultasComponent implements OnInit, OnDestroy {
  private readonly filaService = inject(FilaService);
  private readonly router = inject(Router);
  private readonly snackBar = inject(MatSnackBar);

  readonly consultas = signal<ConsultaFilaItem[]>([]);
  readonly emAndamento = signal<ConsultaAssumidaOut | null>(null);
  readonly carregando = signal(false);
  readonly atualizadoEm = signal<Date | null>(null);

  private polling?: number;
  private relogio?: number;

  ngOnInit(): void {
    this.carregar();
    this.polling = window.setInterval(() => this.carregar(), 30000);
    this.relogio = window.setInterval(() => this.consultas.update((items) => [...items]), 60000);
  }

  ngOnDestroy(): void {
    if (this.polling) window.clearInterval(this.polling);
    if (this.relogio) window.clearInterval(this.relogio);
  }

  carregar(): void {
    this.carregando.set(true);
    this.filaService.listar().subscribe({
      next: (items) => {
        this.consultas.set(items);
        this.atualizadoEm.set(new Date());
        this.carregando.set(false);
      },
      error: () => {
        this.snackBar.open('Erro ao carregar fila', 'Fechar', { duration: 3000 });
        this.carregando.set(false);
      },
    });
    this.filaService.emAndamento().subscribe((consulta) => this.emAndamento.set(consulta));
  }

  atender(consulta: ConsultaFilaItem): void {
    this.filaService.assumir(consulta.idConsulta).subscribe({
      next: () => this.router.navigate(['/consulta', consulta.idConsulta, 'etapa2']),
      error: (erro) => {
        if (erro.status === 409) {
          this.snackBar.open('Consulta assumida por outro médico', 'Fechar', { duration: 3000 });
          this.carregar();
        } else {
          this.snackBar.open('Erro ao assumir consulta', 'Fechar', { duration: 3000 });
        }
      },
    });
  }

  continuar(): void {
    const consulta = this.emAndamento();
    if (consulta) this.router.navigate(['/consulta', consulta.idConsulta, 'etapa2']);
  }

  tempoAguardando(item: ConsultaFilaItem): string {
    const minutos = Math.max(Math.floor((Date.now() - new Date(item.triagemConcluidaEm).getTime()) / 60000), 0);
    if (minutos < 60) return `${minutos} min`;
    return `${Math.floor(minutos / 60)}h ${minutos % 60}min`;
  }

  formatarData(data: string): string {
    const [ano, mes, dia] = data.split('-');
    return `${dia}/${mes}/${ano}`;
  }

  horaAtualizacao(): string {
    const data = this.atualizadoEm();
    return data ? data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : '--:--';
  }
}
