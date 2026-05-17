import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatBadgeModule } from '@angular/material/badge';

import { AuthService } from '../../core/auth/auth.service';
import { AnalisesService } from '../analises/services/analises.service';

interface FeatureCard {
  icon: string;
  title: string;
  description: string;
  route: string;
  badge?: number;
  badgeCritico?: number;
}

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [MatButtonModule, MatCardModule, MatIconModule, MatBadgeModule],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
})
export class HomeComponent implements OnInit {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly analisesService = inject(AnalisesService);

  readonly currentUser = computed(() => this.authService.getUser());
  readonly totaisAnalises = signal({ total: 0, criticos: 0 });

  readonly roleLabel = computed((): string => {
    const role = this.authService.getRole();
    if (role === 'MEDICO') return 'Dr.';
    if (role === 'ENFERMEIRO') return 'Enf.';
    return '';
  });

  readonly featureCards = computed((): FeatureCard[] => {
    const role = this.authService.getRole();
    const totais = this.totaisAnalises();

    if (role === 'MEDICO') {
      return [
        {
          icon: 'format_list_bulleted',
          title: 'Fila de Consultas',
          description: 'Acompanhe e assuma consultas aguardando atendimento',
          route: '/fila',
        },
        {
          icon: 'add_circle_outline',
          title: 'Iniciar Nova Consulta',
          description: 'Inicie uma nova consulta para uma paciente',
          route: '/consulta/nova',
        },
        {
          icon: 'analytics',
          title: 'Fila de Análises',
          description: 'Revise análises de IA de consultas encerradas',
          route: '/analises',
          badge: totais.total || undefined,
          badgeCritico: totais.criticos || undefined,
        },
      ];
    }

    if (role === 'ENFERMEIRO') {
      return [
        {
          icon: 'format_list_bulleted',
          title: 'Fila de Consultas',
          description: 'Acompanhe as consultas aguardando atendimento médico',
          route: '/fila',
        },
        {
          icon: 'add_circle_outline',
          title: 'Iniciar Nova Consulta',
          description: 'Inicie uma nova consulta para uma paciente',
          route: '/consulta/nova',
        },
        {
          icon: 'analytics',
          title: 'Fila de Análises',
          description: 'Revise análises de IA de consultas encerradas',
          route: '/analises',
          badge: totais.total || undefined,
          badgeCritico: totais.criticos || undefined,
        },
      ];
    }

    return [
      {
        icon: 'manage_accounts',
        title: 'Gerenciar Pacientes',
        description: 'Visualize e gerencie o cadastro de pacientes',
        route: '/admin/pacientes',
      },
    ];
  });

  ngOnInit(): void {
    const role = this.authService.getRole();
    if (role === 'MEDICO' || role === 'ENFERMEIRO') {
      this.analisesService.obterTotais().subscribe({
        next: (t) => this.totaisAnalises.set(t),
        error: () => {},
      });
    }
  }

  navegar(path: string): void {
    this.router.navigate([path]);
  }
}
