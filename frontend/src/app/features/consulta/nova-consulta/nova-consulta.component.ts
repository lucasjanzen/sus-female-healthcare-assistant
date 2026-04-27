import { Component, ViewChild, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatStepperModule, MatStepper } from '@angular/material/stepper';
import { Router } from '@angular/router';
import { Etapa1Out, TipoConsulta } from '../models/consulta.model';
import { StepRecepcaoComponent } from './steps/step-recepcao/step-recepcao.component';

export interface ConsultaAtiva {
  idConsulta: string;
  tipo: TipoConsulta;
}

@Component({
  selector: 'app-nova-consulta',
  standalone: true,
  imports: [
    MatStepperModule,
    MatButtonModule,
    MatIconModule,
    StepRecepcaoComponent,
  ],
  templateUrl: './nova-consulta.component.html',
})
export class NovaConsultaComponent {
  @ViewChild('stepper') stepper!: MatStepper;

  readonly consultaAtiva = signal<ConsultaAtiva | null>(null);
  readonly recepcaoConcluida = signal(false);

  constructor(private router: Router) {}

  onRecepcaoConcluida(etapa1: Etapa1Out): void {
    this.consultaAtiva.set({
      idConsulta: etapa1.idConsulta,
      tipo: etapa1.tipoConsulta,
    });
    this.recepcaoConcluida.set(true);
  }

  voltarHome(): void {
    this.router.navigate(['/home']);
  }
}
