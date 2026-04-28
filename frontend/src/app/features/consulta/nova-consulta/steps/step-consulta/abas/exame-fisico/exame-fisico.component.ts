import { Component, EventEmitter, Input, OnInit, Output, inject, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { AlertaExame, ExameFisicoOut } from '../../../../../models/consulta.model';
import { ConsultaClinicaService } from '../../../../../services/consulta-clinica.service';

@Component({
  selector: 'app-exame-fisico',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatFormFieldModule, MatInputModule, MatSelectModule,
    MatButtonModule, MatProgressSpinnerModule, MatSnackBarModule,
  ],
  templateUrl: './exame-fisico.component.html',
})
export class ExameFisicoComponent implements OnInit {
  @Input() idConsulta!: string;
  @Input() igSemanas: number | null = null;
  @Output() salvo = new EventEmitter<ExameFisicoOut>();

  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(ConsultaClinicaService);
  private readonly snack = inject(MatSnackBar);

  readonly salvando = signal(false);
  readonly dadosSalvos = signal<ExameFisicoOut | null>(null);
  readonly alertas = signal<AlertaExame[]>([]);

  form: FormGroup = this.fb.group({
    alturaUterinaCm: [null],
    bcfBpm: [null],
    movimentacaoFetal: [null],
    edemaGrau: [null],
    edemaLocalizacao: [null],
    apresentacaoFetal: [null],
  });

  ngOnInit(): void {
    this.svc.obterExameFisico(this.idConsulta).subscribe({
      next: (dados) => {
        this.dadosSalvos.set(dados);
        this.alertas.set(dados.alertas ?? []);
        this.form.patchValue(dados);
      },
      error: () => {},
    });
  }

  get mostrarApresentacao(): boolean {
    return (this.igSemanas ?? 0) >= 28;
  }

  salvar(): void {
    this.salvando.set(true);
    const payload = this.form.value;
    const obs = this.dadosSalvos()
      ? this.svc.atualizarExameFisico(this.idConsulta, payload)
      : this.svc.salvarExameFisico(this.idConsulta, payload);

    obs.subscribe({
      next: (res) => {
        this.dadosSalvos.set(res);
        this.alertas.set(res.alertas ?? []);
        this.salvando.set(false);
        this.salvo.emit(res);
        if (res.alertas?.length) {
          this.snack.open(`${res.alertas.length} alerta(s) identificado(s).`, 'OK', { duration: 5000 });
        } else {
          this.snack.open('Exame físico salvo.', 'OK', { duration: 3000 });
        }
      },
      error: () => {
        this.salvando.set(false);
        this.snack.open('Erro ao salvar exame físico.', 'OK', { duration: 4000 });
      },
    });
  }
}
