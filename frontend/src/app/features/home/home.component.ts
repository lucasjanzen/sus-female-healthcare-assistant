import { Component, computed } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { Router } from '@angular/router';

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
  imports: [
    MatCardModule,
    MatIconModule,
  ],
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
    if (role === 'MEDICO' || role === 'ENFERMEIRO') {
      return [
        {
          icon: 'add_circle_outline',
          title: 'Nova Consulta',
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

  navigateTo(route: string): void {
    this.router.navigate([route]);
  }
}
