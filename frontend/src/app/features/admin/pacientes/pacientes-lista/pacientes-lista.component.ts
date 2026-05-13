import { Component, OnInit, inject } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTableModule } from '@angular/material/table';
import { Router } from '@angular/router';

import { HttpErrorResponse } from '@angular/common/http';
import { PacienteListItem } from '../../models/paciente-admin.model';
import { PacienteAdminService } from '../../services/paciente-admin.service';
import { NotificationService } from 'app/core/services/notification.service';
import { FormatDataPipe } from 'app/shared/pipes/format-data.pipe';
import { extrairMensagemErro } from 'app/core/utils/http-error.utils';

@Component({
  selector: 'app-pacientes-lista',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatIconModule,
    MatTableModule,
    MatPaginatorModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
    FormatDataPipe,
  ],
  templateUrl: './pacientes-lista.component.html',
  styleUrl: './pacientes-lista.component.scss',
})
export class PacientesListaComponent implements OnInit {
  private readonly service = inject(PacienteAdminService);
  private readonly router = inject(Router);
  private readonly notification = inject(NotificationService);

  readonly colunas = ['nome', 'dataNascimento', 'cns', 'status', 'acoes'];
  dataSource: PacienteListItem[] = [];
  total = 0;
  currentPage = 1;
  pageSize = 20;
  carregando = false;

  readonly termoBusca = new FormControl('');

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.carregando = true;
    this.service.listar(this.currentPage, this.pageSize).subscribe({
      next: (resp) => {
        this.dataSource = resp.items;
        this.total = resp.total;
        this.carregando = false;
      },
      error: (err: HttpErrorResponse) => {
        this.notification.erro(extrairMensagemErro(err, 'Erro ao carregar pacientes'));
        this.carregando = false;
      },
    });
  }

  buscar(): void {
    const termo = this.termoBusca.value?.trim() ?? '';
    if (!termo) {
      this.currentPage = 1;
      this.carregar();
      return;
    }
    this.carregando = true;
    this.service.buscar(termo).subscribe({
      next: (items) => {
        this.dataSource = items;
        this.total = items.length;
        this.carregando = false;
      },
      error: (err: HttpErrorResponse) => {
        this.notification.erro(extrairMensagemErro(err, 'Erro ao buscar pacientes'));
        this.carregando = false;
      },
    });
  }

  mudarPagina(event: PageEvent): void {
    this.currentPage = event.pageIndex + 1;
    this.pageSize = event.pageSize;
    this.carregar();
  }

  voltar(): void {
    this.router.navigate(['/home']);
  }

  novaPaciente(): void {
    this.router.navigate(['/admin/pacientes/novo']);
  }

  editar(id: string): void {
    this.router.navigate(['/admin/pacientes', id, 'editar']);
  }

  desativar(paciente: PacienteListItem): void {
    if (!confirm(`Deseja desativar a paciente "${paciente.nome}"?`)) return;
    this.service.desativar(paciente.id).subscribe({
      next: () => {
        this.notification.sucesso('Paciente desativada com sucesso');
        this.carregar();
      },
      error: (err: HttpErrorResponse) => {
        this.notification.erro(extrairMensagemErro(err, 'Erro ao desativar paciente'));
      },
    });
  }
}
