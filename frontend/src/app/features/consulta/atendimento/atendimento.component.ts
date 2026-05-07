import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

import { ConsultaService } from '../services/consulta.service';
import { StepConsultaComponent } from './steps/step-consulta/step-consulta.component';
import { StepEncerramentoComponent } from './steps/step-encerramento/step-encerramento.component';

@Component({
  selector: 'app-atendimento',
  standalone: true,
  imports: [StepConsultaComponent, StepEncerramentoComponent],
  templateUrl: './atendimento.component.html',
  styleUrl: './atendimento.component.scss',
})
export class AtendimentoComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly consultaService = inject(ConsultaService);

  readonly consultaAtiva = computed(() => this.consultaService.consultaAtiva());
  readonly encerramentoPronto = signal(false);
  readonly titulo = computed(() => (this.encerramentoPronto() ? 'Encerramento' : 'Consulta'));
  readonly faseBadge = computed(() => (this.encerramentoPronto() ? '3 / 3' : '2 / 3'));

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.consultaService.obterTriagem(id).subscribe((etapa) => {
      this.consultaService.definirConsultaAtiva({ idConsulta: id, tipo: etapa.tipoConsulta });
    });
  }

  irParaEncerramento(): void {
    this.encerramentoPronto.set(true);
  }
}
