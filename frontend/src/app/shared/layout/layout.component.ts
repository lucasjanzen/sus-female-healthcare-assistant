import { Component, computed } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';

import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [RouterOutlet, MatToolbarModule, MatButtonModule, MatIconModule],
  template: `
    <mat-toolbar color="primary" class="app-toolbar">
      <span class="app-name">Centro de Assistência à Saúde Feminina</span>
      <span class="spacer"></span>
      @if (currentUser(); as user) {
        <span class="user-name">{{ user.nome }}</span>
      }
      <button mat-stroked-button (click)="logout()" title="Sair da conta" aria-label="Sair">
        <mat-icon>logout</mat-icon>
        Sair
      </button>
    </mat-toolbar>
    <router-outlet />
  `,
  styleUrl: './layout.component.scss',
})
export class LayoutComponent {
  readonly currentUser = computed(() => this.authService.getUser());
  constructor(private authService: AuthService) {}

  logout(): void {
    this.authService.logout();
  }
}
