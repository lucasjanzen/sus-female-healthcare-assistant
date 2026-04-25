import { Component, computed } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatToolbarModule } from '@angular/material/toolbar';
import { Router } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
  ],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
})
export class HomeComponent {
  readonly currentUser = computed(() => this.authService.getUser());

  readonly canStartConsulta = computed(() => {
    const role = this.authService.getRole();
    return role === 'MEDICO' || role === 'ENFERMEIRO';
  });

  readonly isAdmin = computed(() => this.authService.getRole() === 'ADMIN');

  constructor(
    private authService: AuthService,
    private router: Router,
  ) {}

  iniciarNovaConsulta(): void {
    this.router.navigate(['/consulta/nova']);
  }

  gerenciarPacientes(): void {
    this.router.navigate(['/admin/pacientes']);
  }

  logout(): void {
    this.authService.logout();
  }
}
