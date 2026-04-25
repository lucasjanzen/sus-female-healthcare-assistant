import { Routes } from '@angular/router';

export const adminRoutes: Routes = [
  {
    path: 'pacientes',
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./pacientes/pacientes-lista/pacientes-lista.component').then(
            (m) => m.PacientesListaComponent,
          ),
      },
      {
        path: 'novo',
        loadComponent: () =>
          import('./pacientes/paciente-form/paciente-form.component').then(
            (m) => m.PacienteFormComponent,
          ),
      },
      {
        path: ':id/editar',
        loadComponent: () =>
          import('./pacientes/paciente-form/paciente-form.component').then(
            (m) => m.PacienteFormComponent,
          ),
      },
    ],
  },
];
