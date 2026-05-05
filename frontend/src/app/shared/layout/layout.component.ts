import { Component, computed, inject } from '@angular/core';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { filter, map } from 'rxjs';
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
      @if (showBack()) {
        <button mat-icon-button (click)="irParaInicio()" title="Voltar ao início" aria-label="Início">
          <mat-icon>arrow_back</mat-icon>
        </button>
      }
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

  private readonly router = inject(Router);

  private readonly currentUrl = toSignal(
    this.router.events.pipe(
      filter((e) => e instanceof NavigationEnd),
      map((e) => (e as NavigationEnd).urlAfterRedirects),
    ),
    { initialValue: this.router.url },
  );

  readonly showBack = computed(() => this.currentUrl() !== '/home');

  constructor(private authService: AuthService) {}

  irParaInicio(): void {
    this.router.navigate(['/home']);
  }

  logout(): void {
    this.authService.logout();
  }
}
