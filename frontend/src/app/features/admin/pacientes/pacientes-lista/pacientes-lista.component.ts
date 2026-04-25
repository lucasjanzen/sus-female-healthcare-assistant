import { Component, OnInit } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { Router } from '@angular/router';

import { PacienteListItem } from '../../models/paciente-admin.model';
import { PacienteAdminService } from '../../services/paciente-admin.service';

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
    MatSnackBarModule,
  ],
  templateUrl: './pacientes-lista.component.html',
  styles: [`
    .page-container { padding: 24px; }
    .header-row { display: flex; align-items: center; margin-bottom: 24px; gap: 16px; }
    .header-row h1 { margin: 0; flex: 1; font-size: 1.5rem; font-weight: 500; }
    .search-row { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 16px; }
    .search-row mat-form-field { flex: 1; }
    .spinner-container { display: flex; justify-content: center; padding: 48px; }
    .status-chip {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 16px;
      font-size: 12px;
      font-weight: 500;
    }
    .status-ativo { background-color: #e8f5e9; color: #2e7d32; }
    .status-inativo { background-color: #ffebee; color: #c62828; }
    table { width: 100%; }
    .empty-msg { text-align: center; padding: 32px; color: #666; }
  `],
})
export class PacientesListaComponent implements OnInit {
  readonly colunas = ['nome', 'dataNascimento', 'cns', 'status', 'acoes'];
  dataSource: PacienteListItem[] = [];
  total = 0;
  currentPage = 1;
  pageSize = 20;
  carregando = false;

  readonly termoBusca = new FormControl('');

  constructor(
    private service: PacienteAdminService,
    private router: Router,
    private snackBar: MatSnackBar,
  ) {}

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
      error: () => {
        this.snackBar.open('Erro ao carregar pacientes', 'Fechar', { duration: 3000 });
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
      error: () => {
        this.snackBar.open('Erro ao buscar pacientes', 'Fechar', { duration: 3000 });
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
        this.snackBar.open('Paciente desativada com sucesso', 'Fechar', { duration: 3000 });
        this.carregar();
      },
      error: () => {
        this.snackBar.open('Erro ao desativar paciente', 'Fechar', { duration: 3000 });
      },
    });
  }

  formatarData(data: string): string {
    if (!data) return '';
    const [ano, mes, dia] = data.split('-');
    return `${dia}/${mes}/${ano}`;
  }
}
