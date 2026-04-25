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
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { PacienteOut } from '../../../models/paciente.model';
import { PacienteService } from '../../../services/paciente.service';

@Component({
  selector: 'app-step-paciente',
  standalone: true,
  imports: [
    FormsModule,
    ReactiveFormsModule,
    DatePipe,
    MatButtonModule,
    MatCardModule,
    MatDatepickerModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatNativeDateModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatSnackBarModule,
  ],
  templateUrl: './step-paciente.component.html',
})
export class StepPacienteComponent {
  @Output() pacienteSalva = new EventEmitter<string>();

  private fb = inject(FormBuilder);
  private pacienteService = inject(PacienteService);
  private snackBar = inject(MatSnackBar);

  buscando = false;
  salvando = false;
  termoBusca = '';
  resultadosBusca: PacienteOut[] = [];
  pacienteSelecionada: PacienteOut | null = null;

  readonly maxDataNascimento = new Date();

  readonly estadosCivis = [
    { value: 'SOLTEIRA', label: 'Solteira' },
    { value: 'CASADA', label: 'Casada' },
    { value: 'DIVORCIADA', label: 'Divorciada' },
    { value: 'VIUVA', label: 'Viúva' },
    { value: 'UNIAO_ESTAVEL', label: 'União Estável' },
  ];

  form: FormGroup = this.fb.group({
    cpf: ['', [Validators.required, Validators.pattern(/^\d{11}$/)]],
    nome: ['', [Validators.required, Validators.minLength(3)]],
    telefone: ['', [Validators.required, Validators.minLength(10)]],
    dataNascimento: [null, Validators.required],
    estadoCivil: ['', Validators.required],
    possuiFilhos: [false],
    quantidadeFilhos: [null],
    alturaCm: [null, [Validators.required, Validators.min(100), Validators.max(250)]],
    pesoKg: [null, [Validators.required, Validators.min(30), Validators.max(300)]],
    endereco: [''],
    email: ['', Validators.email],
  });

  get possuiFilhosValue(): boolean {
    return !!this.form.get('possuiFilhos')?.value;
  }

  buscar(): void {
    const termo = this.termoBusca.trim();
    if (!termo) return;
    this.buscando = true;
    this.resultadosBusca = [];
    this.pacienteService.buscar(termo).subscribe({
      next: (res) => {
        this.resultadosBusca = res;
        this.buscando = false;
      },
      error: () => {
        this.buscando = false;
        this.snackBar.open('Erro ao buscar pacientes', 'Fechar', { duration: 3000 });
      },
    });
  }

  selecionarPaciente(paciente: PacienteOut): void {
    this.pacienteSelecionada = paciente;
    const [ano, mes, dia] = paciente.dataNascimento.split('-').map(Number);
    this.form.patchValue({
      nome: paciente.nome,
      telefone: paciente.telefone,
      email: paciente.email ?? '',
      estadoCivil: paciente.estadoCivil,
      dataNascimento: new Date(ano, mes - 1, dia),
      possuiFilhos: paciente.possuiFilhos,
      quantidadeFilhos: paciente.quantidadeFilhos ?? null,
      alturaCm: paciente.alturaCm,
      endereco: paciente.endereco ?? '',
    });
    this.form.get('cpf')?.disable();
    this._sincronizarValidacaoFilhos(paciente.possuiFilhos);
  }

  novaPaciente(): void {
    this.pacienteSelecionada = null;
    this.resultadosBusca = [];
    this.termoBusca = '';
    this.form.reset({ possuiFilhos: false });
    this.form.get('cpf')?.enable();
    this._sincronizarValidacaoFilhos(false);
  }

  onPossuiFilhosChange(checked: boolean): void {
    this._sincronizarValidacaoFilhos(checked);
  }

  submeter(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.salvando = true;
    const v = this.form.getRawValue();
    const dataNascimento = this._dateToIso(v.dataNascimento);

    if (this.pacienteSelecionada) {
      this.pacienteService
        .atualizar(this.pacienteSelecionada.id, {
          nome: v.nome,
          telefone: v.telefone,
          email: v.email || undefined,
          estadoCivil: v.estadoCivil,
          dataNascimento,
          possuiFilhos: v.possuiFilhos,
          quantidadeFilhos: v.possuiFilhos ? v.quantidadeFilhos : undefined,
          alturaCm: v.alturaCm,
          pesoKg: v.pesoKg,
          endereco: v.endereco || undefined,
        })
        .subscribe({
          next: (res) => this._onSucesso(res.idConsulta),
          error: (err) => this._onErro(err),
        });
    } else {
      this.pacienteService
        .criar({
          cpf: v.cpf,
          nome: v.nome,
          telefone: v.telefone,
          email: v.email || undefined,
          estadoCivil: v.estadoCivil,
          dataNascimento,
          possuiFilhos: v.possuiFilhos,
          quantidadeFilhos: v.possuiFilhos ? v.quantidadeFilhos : undefined,
          alturaCm: v.alturaCm,
          pesoKg: v.pesoKg,
          endereco: v.endereco || undefined,
        })
        .subscribe({
          next: (res) => this._onSucesso(res.idConsulta),
          error: (err) => this._onErro(err),
        });
    }
  }

  private _sincronizarValidacaoFilhos(possui: boolean): void {
    const ctrl = this.form.get('quantidadeFilhos')!;
    if (possui) {
      ctrl.setValidators([Validators.required, Validators.min(1)]);
    } else {
      ctrl.clearValidators();
      ctrl.setValue(null);
    }
    ctrl.updateValueAndValidity();
  }

  private _dateToIso(date: Date): string {
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  }

  private _onSucesso(idConsulta: string): void {
    this.salvando = false;
    this.snackBar.open('Paciente salva com sucesso', 'Fechar', { duration: 3000 });
    this.pacienteSalva.emit(idConsulta);
  }

  private _onErro(err: { error?: { detail?: string } }): void {
    this.salvando = false;
    const msg = err?.error?.detail ?? 'Erro ao salvar paciente';
    this.snackBar.open(msg, 'Fechar', { duration: 5000 });
  }
}
