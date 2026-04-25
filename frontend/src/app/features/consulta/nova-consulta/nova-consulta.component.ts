import { Component, ViewChild } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatStepperModule, MatStepper } from '@angular/material/stepper';
import { Router } from '@angular/router';
import { StepPacienteComponent } from './steps/step-paciente/step-paciente.component';

@Component({
  selector: 'app-nova-consulta',
  standalone: true,
  imports: [
    MatStepperModule,
    MatButtonModule,
    MatIconModule,
    StepPacienteComponent,
  ],
  templateUrl: './nova-consulta.component.html',
})
export class NovaConsultaComponent {
  @ViewChild('stepper') stepper!: MatStepper;

  idConsulta: string | null = null;

  constructor(private router: Router) {}

  onPacienteSalva(idConsulta: string): void {
    this.idConsulta = idConsulta;
    this.stepper.next();
  }

  voltarHome(): void {
    this.router.navigate(['/home']);
  }
}
