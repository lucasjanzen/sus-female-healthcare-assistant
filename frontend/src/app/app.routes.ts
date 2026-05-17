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
        path: 'consulta',
        loadChildren: () =>
          import('./features/consulta/consulta.routes').then((m) => m.consultaRoutes),
      },
      {
        path: 'fila',
        loadChildren: () => import('./features/fila/fila.routes').then((m) => m.filaRoutes),
      },
      {
        path: 'analises',
        loadChildren: () =>
          import('./features/analises/analises.routes').then((m) => m.analisesRoutes),
      },
    ],
  },
  {
    path: '**',
    redirectTo: 'home',
  },
];
