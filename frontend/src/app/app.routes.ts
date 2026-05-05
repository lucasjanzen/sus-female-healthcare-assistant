import { Routes } from '@angular/router';
import { authGuard } from './core/auth/auth.guard';
import { roleGuard } from './core/auth/role.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: '',
    loadComponent: () => import('./shared/layout/layout.component').then((m) => m.LayoutComponent),
    canActivate: [authGuard],
    children: [
      {
        path: '',
        redirectTo: 'home',
        pathMatch: 'full',
      },
      {
        path: 'home',
        loadComponent: () => import('./features/home/home.component').then((m) => m.HomeComponent),
      },
      {
        path: 'admin',
        canActivate: [roleGuard(['ADMIN'])],
        loadChildren: () => import('./features/admin/admin.routes').then((m) => m.adminRoutes),
      },
      {
        path: 'consulta/nova',
        canActivate: [roleGuard(['MEDICO', 'ENFERMEIRO'])],
        loadComponent: () =>
          import('./features/consulta/triagem/triagem.component').then((m) => m.TriagemComponent),
      },
      {
        path: 'consulta/:id/atendimento',
        canActivate: [roleGuard(['MEDICO'])],
        loadComponent: () =>
          import('./features/consulta/atendimento/atendimento.component').then(
            (m) => m.AtendimentoComponent,
          ),
      },
      {
        path: 'fila',
        canActivate: [roleGuard(['MEDICO'])],
        loadComponent: () =>
          import('./features/fila/fila-consultas/fila-consultas.component').then(
            (m) => m.FilaConsultasComponent,
          ),
      },
    ],
  },
  {
    path: '**',
    redirectTo: 'home',
  },
];
