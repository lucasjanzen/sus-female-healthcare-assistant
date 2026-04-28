import { Component, OnInit, computed, signal } from '@angular/core';
import { MatBadgeModule } from '@angular/material/badge';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { Router } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';
import { FilaService } from '../fila/services/fila.service';

interface FeatureCard {
  icon: string;
  title: string;
  description: string;
  route: string;
  badge?: number;
}

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    MatBadgeModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
  ],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
})
export class HomeComponent implements OnInit {
  readonly currentUser = computed(() => this.authService.getUser());
  readonly totalFila = signal(0);

  readonly roleLabel = computed((): string => {
    const role = this.authService.getRole();
    if (role === 'MEDICO') return 'Dr.';
    if (role === 'ENFERMEIRO') return 'Enf.';
    return '';
  });

  readonly featureCards = computed((): FeatureCard[] => {
    const role = this.authService.getRole();
    if (role === 'MEDICO') {
      return [
        {
          icon: 'format_list_bulleted',
          title: 'Fila de Consultas',
          description: 'Acompanhe e assuma consultas aguardando atendimento',
          route: '/fila',
          badge: this.totalFila(),
        },
        {
          icon: 'add_circle_outline',
          title: 'Iniciar Nova Consulta',
          description: 'Inicie uma nova consulta para uma paciente',
          route: '/consulta/nova',
        },
      ];
    }
    if (role === 'ENFERMEIRO') {
      return [
        {
          icon: 'add_circle_outline',
          title: 'Iniciar Nova Consulta',
          description: 'Inicie uma nova consulta para uma paciente',
          route: '/consulta/nova',
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

  constructor(
    private authService: AuthService,
    private filaService: FilaService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    if (this.authService.getRole() === 'MEDICO') {
      this.filaService.total().subscribe({
        next: (res) => this.totalFila.set(res.total),
        error: () => this.totalFila.set(0),
      });
    }
  }

  navigateTo(route: string): void {
    this.router.navigate([route]);
  }
}
