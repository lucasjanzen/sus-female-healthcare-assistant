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
  styleUrl: './pacientes-lista.component.scss',
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
