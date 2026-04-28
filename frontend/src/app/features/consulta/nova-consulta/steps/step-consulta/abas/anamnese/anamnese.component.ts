import { Component, EventEmitter, Input, OnInit, Output, inject, signal } from '@angular/core';
import { FormArray, FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { AnamneseOut } from '../../../../../models/consulta.model';
import { ConsultaClinicaService } from '../../../../../services/consulta-clinica.service';

const DOENCAS_OPCOES = [
  'HIPERTENSAO', 'DIABETES', 'HIPOTIREOIDISMO', 'HIPERTIREOIDISMO',
  'CARDIOPATIA', 'ASMA', 'EPILEPSIA', 'DEPRESSAO', 'ANSIEDADE',
  'ANEMIA', 'HIV', 'SIFILIS', 'HEPATITE_B', 'HEPATITE_C',
];

@Component({
  selector: 'app-anamnese',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatFormFieldModule, MatInputModule, MatSelectModule,
    MatButtonModule, MatIconModule, MatChipsModule,
    MatSnackBarModule, MatProgressSpinnerModule,
  ],
  templateUrl: './anamnese.component.html',
})
export class AnamneseComponent implements OnInit {
  @Input() idConsulta!: string;
  @Output() salvo = new EventEmitter<AnamneseOut>();

  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(ConsultaClinicaService);
  private readonly snack = inject(MatSnackBar);

  readonly doencasOpcoes = DOENCAS_OPCOES;
  readonly salvando = signal(false);
  readonly dadosSalvos = signal<AnamneseOut | null>(null);

  form: FormGroup = this.fb.group({
    gestacoes: [null],
    partos: [null],
    abortos: [null],
    doencas: [[]],
    situacaoMoradia: [null],
    situacaoRenda: [null],
    suporteFamiliar: [null],
    historicoSaudeMental: [null],
    medicamentos: this.fb.array([]),
  });

  ngOnInit(): void {
    this.svc.obterAnamnese(this.idConsulta).subscribe({
      next: (dados) => {
        this.dadosSalvos.set(dados);
        this.form.patchValue(dados);
        (dados.medicamentos || []).forEach((m) => this.adicionarMedicamento(m));
      },
      error: () => {},
    });
  }

  get medicamentosArray(): FormArray {
    return this.form.get('medicamentos') as FormArray;
  }

  adicionarMedicamento(valores?: { nome?: string; dose?: string; frequencia?: string }): void {
    this.medicamentosArray.push(this.fb.group({
      nome: [valores?.nome ?? ''],
      dose: [valores?.dose ?? ''],
      frequencia: [valores?.frequencia ?? ''],
    }));
  }

  removerMedicamento(idx: number): void {
    this.medicamentosArray.removeAt(idx);
  }

  salvar(): void {
    this.salvando.set(true);
    const payload = this.form.value;
    const obs = this.dadosSalvos()
      ? this.svc.atualizarAnamnese(this.idConsulta, payload)
      : this.svc.salvarAnamnese(this.idConsulta, payload);

    obs.subscribe({
      next: (res) => {
        this.dadosSalvos.set(res);
        this.salvando.set(false);
        this.salvo.emit(res);
        this.snack.open('Anamnese salva com sucesso.', 'OK', { duration: 3000 });
      },
      error: () => {
        this.salvando.set(false);
        this.snack.open('Erro ao salvar anamnese. Tente novamente.', 'OK', { duration: 4000 });
      },
    });
  }
}
