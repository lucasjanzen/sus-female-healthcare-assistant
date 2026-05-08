import { Component, OnInit, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { ActivatedRoute, Router } from '@angular/router';

import { PacienteAdminCreate, PacienteAdminUpdate } from '../../models/paciente-admin.model';
import { PacienteAdminService } from '../../services/paciente-admin.service';
import { NotificationService } from 'app/core/services/notification.service';
import { formatarDataIso } from 'app/core/utils/date.utils';

function notFutureDate(control: AbstractControl): ValidationErrors | null {
  if (!control.value) return null;
  const today = new Date();
  today.setHours(23, 59, 59, 999);
  return control.value > today ? { futureDate: true } : null;
}

function minDigitsValidator(min: number) {
  return (control: AbstractControl): ValidationErrors | null => {
    const digits = String(control.value ?? '').replace(/\D/g, '');
    return digits.length >= min ? null : { minDigits: true };
  };
}

@Component({
  selector: 'app-paciente-form',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatSlideToggleModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './paciente-form.component.html',
  styleUrl: './paciente-form.component.scss',
})
export class PacienteFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly service = inject(PacienteAdminService);
  private readonly notification = inject(NotificationService);

  form!: FormGroup;
  modoEdicao = false;
  pacienteId: string | null = null;
  salvando = false;
  carregando = false;
  readonly possuiFilhos = signal(false);
  readonly hoje = new Date();

  readonly estadosCivis = [
    { value: 'SOLTEIRA', label: 'Solteira' },
    { value: 'CASADA', label: 'Casada' },
    { value: 'DIVORCIADA', label: 'Divorciada' },
    { value: 'VIUVA', label: 'Viúva' },
    { value: 'UNIAO_ESTAVEL', label: 'União Estável' },
  ];

  ngOnInit(): void {
    this.pacienteId = this.route.snapshot.paramMap.get('id');
    this.modoEdicao = !!this.pacienteId;
    this.initForm();

    if (this.modoEdicao && this.pacienteId) {
      this.carregarPaciente(this.pacienteId);
    }
  }

  private initForm(): void {
    this.form = this.fb.group({
      cpf: [
        { value: '', disabled: this.modoEdicao },
        [Validators.required, Validators.pattern(/^\d{11}$/)],
      ],
      cns: ['', [Validators.pattern(/^\d{15,20}$/)]],
      nome: ['', [Validators.required, Validators.minLength(3)]],
      dataNascimento: [null, [Validators.required, notFutureDate]],
      telefone: ['', [Validators.required, minDigitsValidator(10)]],
      email: ['', [Validators.email]],
      estadoCivil: ['', [Validators.required]],
      possuiFilhos: [false],
      quantidadeFilhos: [null],
      alturaCm: [null, [Validators.required, Validators.min(100), Validators.max(250)]],
      endereco: [''],
    });
  }

  onPossuiFilhosChange(checked: boolean): void {
    this.possuiFilhos.set(checked);
    const ctrl = this.form.get('quantidadeFilhos')!;
    if (checked) {
      ctrl.setValidators([Validators.required, Validators.min(1)]);
    } else {
      ctrl.clearValidators();
      ctrl.setValue(null);
    }
    ctrl.updateValueAndValidity();
  }

  private carregarPaciente(id: string): void {
    this.carregando = true;
    this.service.obter(id).subscribe({
      next: (p) => {
        const [ano, mes, dia] = p.dataNascimento.split('-').map(Number);
        this.form.patchValue({
          cns: p.cns ?? '',
          nome: p.nome,
          dataNascimento: new Date(ano, mes - 1, dia),
          telefone: p.telefone,
          email: p.email ?? '',
          estadoCivil: p.estadoCivil,
          possuiFilhos: p.possuiFilhos,
          quantidadeFilhos: p.quantidadeFilhos ?? null,
          alturaCm: p.alturaCm,
          endereco: p.endereco ?? '',
        });
        this.onPossuiFilhosChange(p.possuiFilhos);
        this.carregando = false;
      },
      error: () => {
        this.notification.erro('Erro ao carregar dados da paciente');
        this.router.navigate(['/admin/pacientes']);
      },
    });
  }

  submeter(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const v = this.form.getRawValue();
    const dataNascimento = formatarDataIso(v.dataNascimento as Date);
    this.salvando = true;

    if (this.modoEdicao && this.pacienteId) {
      this.salvarEdicao(this.pacienteId, this.buildPayloadBase(v, dataNascimento));
    } else {
      this.salvarCriacao({
        cpf: v.cpf,
        ...this.buildPayloadBase(v, dataNascimento),
      } as PacienteAdminCreate);
    }
  }

  private buildPayloadBase(
    v: ReturnType<typeof this.form.getRawValue>,
    dataNascimento: string,
  ): PacienteAdminUpdate {
    return {
      cns: v.cns || undefined,
      nome: v.nome,
      dataNascimento,
      telefone: v.telefone,
      email: v.email || undefined,
      estadoCivil: v.estadoCivil,
      possuiFilhos: v.possuiFilhos,
      quantidadeFilhos: v.possuiFilhos ? v.quantidadeFilhos : undefined,
      alturaCm: v.alturaCm,
      endereco: v.endereco || undefined,
    };
  }

  private salvarEdicao(id: string, payload: PacienteAdminUpdate): void {
    this.service.atualizar(id, payload).subscribe({
      next: () => {
        this.notification.sucesso('Dados atualizados com sucesso');
        this.router.navigate(['/admin/pacientes']);
      },
      error: (err) => {
        this.notification.erro(err?.error?.detail ?? 'Erro ao atualizar paciente', 4000);
        this.salvando = false;
      },
    });
  }

  private salvarCriacao(payload: PacienteAdminCreate): void {
    this.service.criar(payload).subscribe({
      next: () => {
        this.notification.sucesso('Paciente cadastrada com sucesso');
        this.router.navigate(['/admin/pacientes']);
      },
      error: (err) => {
        this.notification.erro(err?.error?.detail ?? 'Erro ao cadastrar paciente', 4000);
        this.salvando = false;
      },
    });
  }

  cancelar(): void {
    this.router.navigate(['/admin/pacientes']);
  }
}
