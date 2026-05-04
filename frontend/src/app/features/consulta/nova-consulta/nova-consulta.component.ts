import { Component, OnInit, ViewChild, computed, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatStepper, MatStepperModule } from '@angular/material/stepper';

import { ConsultaService } from '../services/consulta.service';
import { StepConsultaComponent } from './steps/step-consulta/step-consulta.component';
import { StepEncerramentoComponent } from './steps/step-encerramento/step-encerramento.component';
import { StepRecepcaoComponent } from './steps/step-recepcao/step-recepcao.component';

@Component({
  selector: 'app-nova-consulta',
  standalone: true,
  imports: [
    MatStepperModule,
    MatIconModule,
    StepRecepcaoComponent,
    StepConsultaComponent,
    StepEncerramentoComponent,
  ],
  templateUrl: './nova-consulta.component.html',
  styleUrl: './nova-consulta.component.scss',
})
export class NovaConsultaComponent implements OnInit {
  @ViewChild(MatStepper) stepper?: MatStepper;

  private readonly route = inject(ActivatedRoute);
  private readonly consultaService = inject(ConsultaService);

  readonly consultaAtiva = computed(() => this.consultaService.consultaAtiva());
  readonly encerramentoPronto = signal(false);
  modo: 'nova' | 'assumir' = 'nova';

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.modo = 'assumir';
      this.consultaService.obterEtapa1(id).subscribe((etapa) => {
        this.consultaService.definirConsultaAtiva({ idConsulta: id, tipo: etapa.tipoConsulta });
        queueMicrotask(() => {
          if (this.stepper) this.stepper.selectedIndex = 1;
        });
      });
    } else {
      this.consultaService.definirConsultaAtiva(null);
    }
  }

  irParaEncerramento(): void {
    if (this.stepper) this.stepper.selectedIndex = 2;
    this.encerramentoPronto.set(true);
  }
}
