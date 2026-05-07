import { Routes } from '@angular/router';
import { roleGuard } from '../../core/auth/role.guard';

export const consultaRoutes: Routes = [
  {
    path: 'nova',
    canActivate: [roleGuard(['MEDICO', 'ENFERMEIRO'])],
    loadComponent: () =>
      import('./triagem/triagem.component').then((m) => m.TriagemComponent),
  },
  {
    path: ':id/atendimento',
    canActivate: [roleGuard(['MEDICO'])],
    loadComponent: () =>
      import('./atendimento/atendimento.component').then((m) => m.AtendimentoComponent),
  },
];
