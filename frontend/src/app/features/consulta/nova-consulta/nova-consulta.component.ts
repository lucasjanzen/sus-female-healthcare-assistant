import { Component, ViewChild, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatStepperModule, MatStepper } from '@angular/material/stepper';
import { Router } from '@angular/router';
import { StepIdentificacaoComponent } from './steps/step-identificacao/step-identificacao.component';

export interface ConsultaAtiva {
  idConsulta: string;
  tipo: string;
}

@Component({
  selector: 'app-nova-consulta',
  standalone: true,
  imports: [
    MatStepperModule,
    MatButtonModule,
    MatIconModule,
    StepIdentificacaoComponent,
  ],
  templateUrl: './nova-consulta.component.html',
})
export class NovaConsultaComponent {
  @ViewChild('stepper') stepper!: MatStepper;

  readonly consultaAtiva = signal<ConsultaAtiva | null>(null);

  constructor(private router: Router) {}

  onConsultaIniciada(data: ConsultaAtiva): void {
    this.consultaAtiva.set(data);
    this.stepper.next();
  }

  voltarHome(): void {
    this.router.navigate(['/home']);
  }
}
