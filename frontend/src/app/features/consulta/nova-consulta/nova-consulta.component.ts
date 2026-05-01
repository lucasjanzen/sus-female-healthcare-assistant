import { Component, OnInit, ViewChild, computed, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatStepper, MatStepperModule } from '@angular/material/stepper';

import { ConsultaService } from '../services/consulta.service';
import { StepConsultaComponent } from './steps/step-consulta/step-consulta.component';
import { StepRecepcaoComponent } from './steps/step-recepcao/step-recepcao.component';

@Component({
  selector: 'app-nova-consulta',
  standalone: true,
  imports: [MatStepperModule, MatIconModule, StepRecepcaoComponent, StepConsultaComponent],
  templateUrl: './nova-consulta.component.html',
  styles: [`
    .page { padding: 24px; max-width: 1120px; margin: 0 auto; }
    .locked-step { display: inline-flex; align-items: center; gap: 6px; }
  `],
})
export class NovaConsultaComponent implements OnInit {
  @ViewChild(MatStepper) stepper?: MatStepper;

  private readonly route = inject(ActivatedRoute);
  private readonly consultaService = inject(ConsultaService);

  readonly consultaAtiva = computed(() => this.consultaService.consultaAtiva());
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
  }
}
