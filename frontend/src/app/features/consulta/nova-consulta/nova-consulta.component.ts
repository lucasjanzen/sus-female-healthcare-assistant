import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

import { ConsultaService } from '../services/consulta.service';
import { StepConsultaComponent } from './steps/step-consulta/step-consulta.component';
import { StepEncerramentoComponent } from './steps/step-encerramento/step-encerramento.component';
import { StepRecepcaoComponent } from './steps/step-recepcao/step-recepcao.component';

@Component({
  selector: 'app-nova-consulta',
  standalone: true,
  imports: [StepRecepcaoComponent, StepConsultaComponent, StepEncerramentoComponent],
  templateUrl: './nova-consulta.component.html',
  styleUrl: './nova-consulta.component.scss',
})
export class NovaConsultaComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly consultaService = inject(ConsultaService);

  readonly consultaAtiva = computed(() => this.consultaService.consultaAtiva());
  readonly encerramentoPronto = signal(false);
  modo: 'nova' | 'assumir' = 'nova';

  readonly titulo = computed(() => {
    if (this.modo === 'nova') return 'Triagem';
    if (this.encerramentoPronto()) return 'Encerramento';
    return 'Consulta';
  });

  readonly faseBadge = computed(() => {
    if (this.modo === 'nova') return null;
    if (this.encerramentoPronto()) return '3 / 3';
    return '2 / 3';
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.modo = 'assumir';
      this.consultaService.obterEtapa1(id).subscribe((etapa) => {
        this.consultaService.definirConsultaAtiva({ idConsulta: id, tipo: etapa.tipoConsulta });
      });
    } else {
      this.consultaService.definirConsultaAtiva(null);
    }
  }

  irParaEncerramento(): void {
    this.encerramentoPronto.set(true);
  }
}
