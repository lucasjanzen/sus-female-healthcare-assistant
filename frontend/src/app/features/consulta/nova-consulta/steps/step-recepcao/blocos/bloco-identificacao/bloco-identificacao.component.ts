import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Output, inject } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import {
  ConsultaIniciarRequest,
  Etapa1Out,
  PacienteConsultaOut,
  TipoConsulta,
} from '../../../../../models/consulta.model';
import { ConsultaService } from '../../../../../services/consulta.service';
import { PacienteConsultaService } from '../../../../../services/paciente-consulta.service';

export interface IdentificacaoConcluida {
  idConsulta: string;
  tipo: TipoConsulta;
  igSemanas: number | null;
  igDias: number | null;
  alturaCm: number;
  etapa1: Etapa1Out;
}

@Component({
  selector: 'app-bloco-identificacao',
  standalone: true,
  imports: [
    DatePipe,
    FormsModule,
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatCheckboxModule,
    MatDatepickerModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatSnackBarModule,
  ],
  templateUrl: './bloco-identificacao.component.html',
})
export class BlocoIdentificacaoComponent {
  @Output() consultaIniciada = new EventEmitter<IdentificacaoConcluida>();

  private fb = inject(FormBuilder);
  private pacienteConsultaService = inject(PacienteConsultaService);
  private consultaService = inject(ConsultaService);
  private snackBar = inject(MatSnackBar);

  buscando = false;
  salvando = false;
  termoBusca = '';
  resultados: PacienteConsultaOut[] = [];
  pacienteSelecionada: PacienteConsultaOut | null = null;

  readonly hoje = new Date();

  readonly tiposConsulta: { value: TipoConsulta; label: string }[] = [
    { value: 'PRENATAL', label: 'Pré-natal' },
    { value: 'GINECOLOGICA', label: 'Ginecológica' },
    { value: 'PUERPERIO', label: 'Puerpério' },
    { value: 'PLANEJAMENTO_FAMILIAR', label: 'Planejamento Familiar' },
  ];

  form: FormGroup = this.fb.group({
    tipoConsulta: ['' as TipoConsulta | '', Validators.required],
    dum: [null as Date | null],
    tcleAssinado: [false, Validators.requiredTrue],
  });

  get tipoConsultaValue(): string {
    return this.form.get('tipoConsulta')?.value ?? '';
  }

  get igDisplay(): string | null {
    const dum = this.form.get('dum')?.value as Date | null;
    if (!dum || !(dum instanceof Date)) return null;
    const diffMs = this.hoje.getTime() - dum.getTime();
    if (diffMs < 0) return null;
    const diffDias = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const semanas = Math.floor(diffDias / 7);
    const dias = diffDias % 7;
    return `${semanas} semana${semanas !== 1 ? 's' : ''} e ${dias} dia${dias !== 1 ? 's' : ''}`;
  }

  get podeAvancar(): boolean {
    if (!this.pacienteSelecionada) return false;
    if (this.form.get('tipoConsulta')?.invalid) return false;
    if (this.tipoConsultaValue === 'PRENATAL' && !this.form.get('dum')?.value)
      return false;
    if (!this.form.get('tcleAssinado')?.value) return false;
    return true;
  }

  buscar(): void {
    const termo = this.termoBusca.trim();
    if (!termo) return;
    this.buscando = true;
    this.resultados = [];
    this.pacienteConsultaService.buscar(termo).subscribe({
      next: (res) => {
        this.resultados = res;
        this.buscando = false;
      },
      error: () => {
        this.buscando = false;
        this.snackBar.open('Erro ao buscar pacientes', 'Fechar', { duration: 3000 });
      },
    });
  }

  selecionarPaciente(paciente: PacienteConsultaOut): void {
    this.pacienteSelecionada = paciente;
  }

  limparSelecao(): void {
    this.pacienteSelecionada = null;
    this.resultados = [];
    this.termoBusca = '';
    this.form.reset({ tipoConsulta: '', dum: null, tcleAssinado: false });
    this._sincronizarDum('');
  }

  onTipoConsultaChange(tipo: string): void {
    this._sincronizarDum(tipo);
  }

  confirmarIdentificacao(): void {
    if (!this.podeAvancar) {
      this.form.markAllAsTouched();
      return;
    }
    this.salvando = true;
    const v = this.form.getRawValue();
    const payload: ConsultaIniciarRequest = {
      pacienteId: this.pacienteSelecionada!.id,
      tipoConsulta: v.tipoConsulta as TipoConsulta,
      dum: v.dum ? this._dateToIso(v.dum) : undefined,
      tcleAssinado: true,
    };
    this.consultaService.iniciar(payload).subscribe({
      next: (etapa1) => {
        this.salvando = false;
        const dum = this.form.get('dum')?.value as Date | null;
        let igSemanas: number | null = null;
        let igDias: number | null = null;
        if (dum) {
          const diffDias = Math.floor((this.hoje.getTime() - dum.getTime()) / 86400000);
          igSemanas = Math.floor(diffDias / 7);
          igDias = diffDias % 7;
        }
        this.consultaIniciada.emit({
          idConsulta: etapa1.idConsulta,
          tipo: v.tipoConsulta as TipoConsulta,
          igSemanas,
          igDias,
          alturaCm: this.pacienteSelecionada!.alturaCm,
          etapa1,
        });
      },
      error: (err: { error?: { detail?: string } }) => {
        this.salvando = false;
        const msg = err?.error?.detail ?? 'Erro ao iniciar consulta';
        this.snackBar.open(msg, 'Fechar', { duration: 5000 });
      },
    });
  }

  private _sincronizarDum(tipo: string): void {
    const dumCtrl = this.form.get('dum')!;
    if (tipo === 'PRENATAL') {
      dumCtrl.setValidators([Validators.required]);
    } else {
      dumCtrl.clearValidators();
      dumCtrl.setValue(null);
    }
    dumCtrl.updateValueAndValidity();
  }

  private _dateToIso(d: Date): string {
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  }
}
