import { Component, OnInit, ViewChild, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatStepperModule, MatStepper } from '@angular/material/stepper';
import { ActivatedRoute, Router } from '@angular/router';
import { ConsultaAtiva, Etapa1Out, ResultadoOut } from '../models/consulta.model';
import { ConsultaAssumidaOut } from '../../fila/models/fila.model';
import { FilaService } from '../../fila/services/fila.service';
import { StepRecepcaoComponent } from './steps/step-recepcao/step-recepcao.component';
import { StepConsultaComponent } from './steps/step-consulta/step-consulta.component';
import { StepEncerramentoComponent } from './steps/step-encerramento/step-encerramento.component';

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
    StepEncerramentoComponent,
  ],
  templateUrl: './nova-consulta.component.html',
})
export class NovaConsultaComponent implements OnInit {
  @ViewChild('stepper') stepper!: MatStepper;

  readonly consultaAtiva = signal<ConsultaAtiva | null>(null);
  readonly etapa1 = signal<Etapa1Out | null>(null);
  readonly consultaAssumida = signal<ConsultaAssumidaOut | null>(null);
  readonly resultadoEtapa2 = signal<ResultadoOut | null>(null);
  readonly recepcaoConcluida = signal(false);
  readonly consultaConcluida = signal(false);
  readonly modoAssumir = signal(false);
  readonly carregandoAssumida = signal(false);

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private filaService: FilaService,
  ) {}

  ngOnInit(): void {
    const idConsulta = this.route.snapshot.paramMap.get('id');
    if (!idConsulta) return;

    this.modoAssumir.set(true);
    this.carregandoAssumida.set(true);
    this.filaService.obterEmAndamento(idConsulta).subscribe({
      next: (consulta) => {
        this.consultaAssumida.set(consulta);
        this.consultaAtiva.set({
          idConsulta: consulta.idConsulta,
          tipo: consulta.tipoConsulta,
        });
        this.etapa1.set({
          idConsulta: consulta.idConsulta,
          pacienteId: '',
          tipoConsulta: consulta.tipoConsulta,
          status: 'EM_ATENDIMENTO',
          igSemanas: consulta.igSemanas,
          igDias: consulta.igDias,
          tcleAssinado: true,
          triagemConcluida: true,
          triagem: consulta.triagemResumo,
          abertaEm: consulta.assumidaEm,
          triagemConcluidaEm: consulta.assumidaEm,
        });
        this.recepcaoConcluida.set(true);
        this.carregandoAssumida.set(false);
        setTimeout(() => {
          if (this.stepper) this.stepper.selectedIndex = 1;
        }, 100);
      },
      error: () => {
        this.carregandoAssumida.set(false);
        this.router.navigate(['/fila']);
      },
    });
  }

  onRecepcaoConcluida(etapa1: Etapa1Out): void {
    this.etapa1.set(etapa1);
    this.consultaAtiva.set({
      idConsulta: etapa1.idConsulta,
      tipo: etapa1.tipoConsulta,
    });
    this.recepcaoConcluida.set(true);
    setTimeout(() => this.stepper.next(), 100);
  }

  onConsultaConcluida(resultado: ResultadoOut): void {
    this.resultadoEtapa2.set(resultado);
    this.consultaConcluida.set(true);
    setTimeout(() => this.stepper.next(), 100);
  }

  voltarHome(): void {
    this.router.navigate(['/home']);
  }
}
