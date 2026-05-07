import { Component, computed, signal } from '@angular/core';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

import { AuthService } from '../../core/auth/auth.service';

interface FeatureCard {
  icon: string;
  title: string;
  description: string;
  route: string;
}

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [MatButtonModule, MatCardModule, MatIconModule],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
})
export class HomeComponent {
  readonly currentUser = computed(() => this.authService.getUser());

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
    private router: Router,
  ) {}

  navegar(path: string): void {
    this.router.navigate([path]);
  }
}
