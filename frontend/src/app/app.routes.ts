import { Routes } from '@angular/router';
import { authGuard } from './core/auth/auth.guard';
import { roleGuard } from './core/auth/role.guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'home',
    pathMatch: 'full',
  },
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'home',
    loadComponent: () =>
      import('./features/home/home.component').then((m) => m.HomeComponent),
    canActivate: [authGuard],
  },
  {
    path: 'consulta/nova',
    loadComponent: () =>
      import('./features/consulta/nova-consulta/nova-consulta.component').then(
        (m) => m.NovaConsultaComponent,
      ),
    canActivate: [authGuard, roleGuard(['MEDICO', 'ENFERMEIRO'])],
  },
  {
    path: 'admin',
    canActivate: [authGuard, roleGuard(['ADMIN'])],
    loadChildren: () =>
      import('./features/admin/admin.routes').then((m) => m.adminRoutes),
  },
  {
    path: '**',
    redirectTo: 'home',
  },
];
