import { Routes } from '@angular/router';
import { roleGuard } from '../../core/auth/role.guard';

export const filaRoutes: Routes = [
  {
    path: '',
    canActivate: [roleGuard(['MEDICO', 'ENFERMEIRO'])],
    loadComponent: () =>
      import('./fila-consultas/fila-consultas.component').then((m) => m.FilaConsultasComponent),
  },
];
