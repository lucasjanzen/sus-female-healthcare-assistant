import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { filter, map } from 'rxjs';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatBadgeModule } from '@angular/material/badge';

import { AuthService } from '../../core/auth/auth.service';
import { AnalisesService } from '../../features/analises/services/analises.service';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [RouterOutlet, MatToolbarModule, MatButtonModule, MatIconModule, MatBadgeModule],
  templateUrl: './layout.component.html',
  styleUrl: './layout.component.scss',
})
export class LayoutComponent implements OnInit {
  readonly router = inject(Router);
  private readonly authService = inject(AuthService);
  private readonly analisesService = inject(AnalisesService);

  private readonly currentUrl = toSignal(
    this.router.events.pipe(
      filter((e) => e instanceof NavigationEnd),
      map((e) => (e as NavigationEnd).urlAfterRedirects),
    ),
    { initialValue: this.router.url },
  );

  readonly currentUser = computed(() => this.authService.getUser());
  readonly showBack = computed(() => this.currentUrl() !== '/home');
  readonly role = computed(() => this.authService.getRole());
  readonly isMedicoOuEnfermeiro = computed(
    () => this.role() === 'MEDICO' || this.role() === 'ENFERMEIRO',
  );

  readonly badgeCriticos = signal(0);

  ngOnInit(): void {
    if (this.isMedicoOuEnfermeiro()) {
      this.carregarTotais();
      window.setInterval(() => this.carregarTotais(), 60000);
    }
  }

  private carregarTotais(): void {
    this.analisesService.obterTotais().subscribe({
      next: (t) => this.badgeCriticos.set(t.criticos),
      error: () => {},
    });
  }

  irParaInicio(): void {
    this.router.navigate(['/home']);
  }

  logout(): void {
    this.authService.logout();
  }
}
