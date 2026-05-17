import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthService } from '../../../core/auth/auth.service';
import { NotificationService } from '../../../core/services/notification.service';
import { extrairMensagemErro } from '../../../core/utils/http-error.utils';
import { ConsultaAssumidaOut, ConsultaFilaItem } from '../models/fila.model';
import { FilaService } from '../services/fila.service';
import { FormatDataPipe } from '../../../shared/pipes/format-data.pipe';

@Component({
  selector: 'app-fila-consultas',
  standalone: true,
  imports: [
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatIconModule,
    MatProgressSpinnerModule,
    FormatDataPipe,
  ],
  templateUrl: './fila-consultas.component.html',
  styleUrl: './fila-consultas.component.scss',
})
export class FilaConsultasComponent implements OnInit, OnDestroy {
  private readonly filaService = inject(FilaService);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly notification = inject(NotificationService);

  readonly consultas = signal<ConsultaFilaItem[]>([]);
  readonly emAndamento = signal<ConsultaAssumidaOut | null>(null);
  readonly carregando = signal(false);
  readonly assumindo = signal(false);
  readonly atualizadoEm = signal<Date | null>(null);
  readonly isMedico = computed(() => this.authService.getRole() === 'MEDICO');

  private polling?: number;
  private relogio?: number;
  private _inicialCarregado = false;

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
    if (!this._inicialCarregado) this.carregando.set(true);
    this.filaService.listar().subscribe({
      next: (items) => {
        this.consultas.set(items);
        this.atualizadoEm.set(new Date());
        this.carregando.set(false);
        this._inicialCarregado = true;
      },
      error: (err: HttpErrorResponse) => {
        this.notification.erro(extrairMensagemErro(err, 'Erro ao carregar fila'));
        this.carregando.set(false);
        this._inicialCarregado = true;
      },
    });
    if (this.isMedico()) {
      this.filaService.emAndamento().subscribe({
        next: (consulta) => this.emAndamento.set(consulta),
        error: (err: HttpErrorResponse) =>
          this.notification.erro(extrairMensagemErro(err, 'Erro ao verificar consulta em andamento')),
      });
    }
  }

  atender(consulta: ConsultaFilaItem): void {
    this.assumindo.set(true);
    this.filaService.assumir(consulta.idConsulta).subscribe({
      next: () => this.router.navigate(['/consulta', consulta.idConsulta, 'atendimento']),
      error: (err: HttpErrorResponse) => {
        this.assumindo.set(false);
        this.notification.erro(extrairMensagemErro(err, 'Erro ao assumir consulta'));
        if (err.status === 409) this.carregar();
      },
    });
  }

  continuar(): void {
    const consulta = this.emAndamento();
    if (consulta) this.router.navigate(['/consulta', consulta.idConsulta, 'atendimento']);
  }

  tempoAguardando(item: ConsultaFilaItem): string {
    const minutos = Math.max(
      Math.floor((Date.now() - new Date(item.triagemConcluidaEm).getTime()) / 60000),
      0,
    );
    if (minutos < 60) return `${minutos} min`;
    return `${Math.floor(minutos / 60)}h ${minutos % 60}min`;
  }

  horaAtualizacao(): string {
    const data = this.atualizadoEm();
    return data
      ? data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
      : '--:--';
  }
}
