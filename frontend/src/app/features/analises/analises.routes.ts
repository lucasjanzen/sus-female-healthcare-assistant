import { Routes } from '@angular/router';
import { roleGuard } from '../../core/auth/role.guard';

export const analisesRoutes: Routes = [
  {
    path: '',
    canActivate: [roleGuard(['MEDICO', 'ENFERMEIRO'])],
    loadComponent: () =>
      import('./fila-analises/fila-analises.component').then((m) => m.FilaAnalisesComponent),
  },
  {
    path: ':id',
    canActivate: [roleGuard(['MEDICO', 'ENFERMEIRO'])],
    loadComponent: () =>
      import('./detalhe-analise/detalhe-analise.component').then((m) => m.DetalheAnaliseComponent),
  },
];
