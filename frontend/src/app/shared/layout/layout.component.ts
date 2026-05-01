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
  styles: [`
    .app-toolbar { position: sticky; top: 0; z-index: 100; }
    .app-name { font-weight: 600; font-size: 0.95rem; letter-spacing: 0; }
    .spacer { flex: 1 1 auto; }
    .user-name { margin: 0 12px; font-size: 0.9rem; opacity: 0.9; }
  `],
})
export class LayoutComponent {
  readonly currentUser = computed(() => this.authService.getUser());
  constructor(private authService: AuthService) {}

  logout(): void {
    this.authService.logout();
  }
}
