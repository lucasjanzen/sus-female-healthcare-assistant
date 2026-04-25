import { Component, OnInit } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { provideNativeDateAdapter } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatToolbarModule } from '@angular/material/toolbar';
import { ActivatedRoute, Router } from '@angular/router';

import { PacienteAdminCreate, PacienteAdminUpdate } from '../../models/paciente-admin.model';
import { PacienteAdminService } from '../../services/paciente-admin.service';

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
  providers: [provideNativeDateAdapter()],
  imports: [
    ReactiveFormsModule,
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatSlideToggleModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
  ],
  templateUrl: './paciente-form.component.html',
  styles: [`
    .page-container { padding: 24px; max-width: 860px; margin: 0 auto; }
    .form-section { margin-top: 24px; }
    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0 16px;
    }
    .full-width { grid-column: 1 / -1; }
    .toggle-row {
      grid-column: 1 / -1;
      padding: 12px 0;
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .form-actions {
      display: flex;
      gap: 12px;
      justify-content: flex-end;
      margin-top: 24px;
    }
    mat-form-field { width: 100%; }
    .spinner-container { display: flex; justify-content: center; padding: 64px; }
    .submit-spinner { display: inline-flex; align-items: center; gap: 8px; }
  `],
})
export class PacienteFormComponent implements OnInit {
  form!: FormGroup;
  modoEdicao = false;
  pacienteId: string | null = null;
  salvando = false;
  carregando = false;

  readonly hoje = new Date();

  readonly estadosCivis = [
    { value: 'SOLTEIRA', label: 'Solteira' },
    { value: 'CASADA', label: 'Casada' },
    { value: 'DIVORCIADA', label: 'Divorciada' },
    { value: 'VIUVA', label: 'Viúva' },
    { value: 'UNIAO_ESTAVEL', label: 'União Estável' },
  ];

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private service: PacienteAdminService,
    private snackBar: MatSnackBar,
  ) {}

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

  get possuiFilhos(): boolean {
    return !!this.form.get('possuiFilhos')?.value;
  }

  onPossuiFilhosChange(checked: boolean): void {
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
        if (p.possuiFilhos) {
          this.onPossuiFilhosChange(true);
        }
        this.carregando = false;
      },
      error: () => {
        this.snackBar.open('Erro ao carregar dados da paciente', 'Fechar', { duration: 3000 });
        this.router.navigate(['/admin/pacientes']);
      },
    });
  }

  private formatarData(d: Date): string {
    const ano = d.getFullYear();
    const mes = String(d.getMonth() + 1).padStart(2, '0');
    const dia = String(d.getDate()).padStart(2, '0');
    return `${ano}-${mes}-${dia}`;
  }

  submeter(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const v = this.form.getRawValue();
    const dataNascimento = this.formatarData(v.dataNascimento as Date);

    this.salvando = true;

    if (this.modoEdicao && this.pacienteId) {
      const payload: PacienteAdminUpdate = {
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
      this.service.atualizar(this.pacienteId, payload).subscribe({
        next: () => {
          this.snackBar.open('Dados atualizados com sucesso', 'Fechar', { duration: 3000 });
          this.router.navigate(['/admin/pacientes']);
        },
        error: (err) => {
          const msg = err?.error?.detail ?? 'Erro ao atualizar paciente';
          this.snackBar.open(msg, 'Fechar', { duration: 4000 });
          this.salvando = false;
        },
      });
    } else {
      const payload: PacienteAdminCreate = {
        cpf: v.cpf,
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
      this.service.criar(payload).subscribe({
        next: () => {
          this.snackBar.open('Paciente cadastrada com sucesso', 'Fechar', { duration: 3000 });
          this.router.navigate(['/admin/pacientes']);
        },
        error: (err) => {
          const msg = err?.error?.detail ?? 'Erro ao cadastrar paciente';
          this.snackBar.open(msg, 'Fechar', { duration: 4000 });
          this.salvando = false;
        },
      });
    }
  }

  cancelar(): void {
    this.router.navigate(['/admin/pacientes']);
  }
}
