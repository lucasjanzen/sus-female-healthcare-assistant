import { Component, computed } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatToolbarModule } from '@angular/material/toolbar';

import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatSnackBarModule,
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

  constructor(
    private authService: AuthService,
    private snackBar: MatSnackBar
  ) {}

  iniciarNovaConsulta(): void {
    this.snackBar.open('Funcionalidade em desenvolvimento', 'Fechar', {
      duration: 4000,
      horizontalPosition: 'center',
      verticalPosition: 'bottom',
    });
  }

  logout(): void {
    this.authService.logout();
  }
}
