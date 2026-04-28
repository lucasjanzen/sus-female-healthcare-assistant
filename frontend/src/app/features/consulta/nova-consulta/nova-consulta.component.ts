import { Component, ViewChild, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatStepperModule, MatStepper } from '@angular/material/stepper';
import { Router } from '@angular/router';
import { ConsultaAtiva, Etapa1Out } from '../models/consulta.model';
import { StepRecepcaoComponent } from './steps/step-recepcao/step-recepcao.component';
import { StepConsultaComponent } from './steps/step-consulta/step-consulta.component';

export type { ConsultaAtiva };

@Component({
  selector: 'app-nova-consulta',
  standalone: true,
  imports: [
    MatStepperModule,
    MatButtonModule,
    MatIconModule,
    StepRecepcaoComponent,
    StepConsultaComponent,
  ],
  templateUrl: './nova-consulta.component.html',
})
export class NovaConsultaComponent {
  @ViewChild('stepper') stepper!: MatStepper;

  readonly consultaAtiva = signal<ConsultaAtiva | null>(null);
  readonly etapa1 = signal<Etapa1Out | null>(null);
  readonly recepcaoConcluida = signal(false);
  readonly consultaConcluida = signal(false);

  constructor(private router: Router) {}

  onRecepcaoConcluida(etapa1: Etapa1Out): void {
    this.etapa1.set(etapa1);
    this.consultaAtiva.set({
      idConsulta: etapa1.idConsulta,
      tipo: etapa1.tipoConsulta,
    });
    this.recepcaoConcluida.set(true);
    setTimeout(() => this.stepper.next(), 100);
  }

  onConsultaConcluida(): void {
    this.consultaConcluida.set(true);
    setTimeout(() => this.stepper.next(), 100);
  }

  voltarHome(): void {
    this.router.navigate(['/home']);
  }
}
