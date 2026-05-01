import { Component, computed } from '@angular/core';

import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [],
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

  constructor(private authService: AuthService) {}
}
