import { Component, computed, inject, signal } from "@angular/core";
import { FormBuilder, ReactiveFormsModule, Validators } from "@angular/forms";
import { Router } from "@angular/router";
import { MatButtonModule } from "@angular/material/button";
import { MatCardModule } from "@angular/material/card";
import { MatDatepickerModule } from "@angular/material/datepicker";
import { MatDividerModule } from "@angular/material/divider";
import { MatFormFieldModule } from "@angular/material/form-field";
import { MatIconModule } from "@angular/material/icon";
import { MatInputModule } from "@angular/material/input";
import { MatProgressSpinnerModule } from "@angular/material/progress-spinner";
import { MatSelectModule } from "@angular/material/select";
import { MatSnackBar, MatSnackBarModule } from "@angular/material/snack-bar";

import {
  PacienteConsultaOut,
  TipoConsulta,
} from "../../../models/consulta.model";
import { ConsultaService } from "../../../services/consulta.service";

@Component({
  selector: "app-step-recepcao",
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatDatepickerModule,
    MatDividerModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatSnackBarModule,
  ],
  templateUrl: "./step-recepcao.component.html",
  styleUrl: "./step-recepcao.component.scss",
})
export class StepRecepcaoComponent {
  private fb = inject(FormBuilder);
  private consultaService = inject(ConsultaService);
  private snackBar = inject(MatSnackBar);
  private router = inject(Router);

  pacientes = signal<PacienteConsultaOut[]>([]);
  pacienteSelecionada = signal<PacienteConsultaOut | null>(null);
  etapa1Concluida = signal(false);
  triagemConcluida = signal(false);
  carregando = signal(false);
  consultaId = signal<string | null>(null);
  tipos: TipoConsulta[] = [
    "PRENATAL",
    "GINECOLOGICA",
    "PUERPERIO",
    "PLANEJAMENTO_FAMILIAR",
  ];

  maxDate: Date = new Date();

  busca = this.fb.nonNullable.control("", [Validators.required]);
  identificacaoForm = this.fb.group({
    tipoConsulta: this.fb.nonNullable.control<TipoConsulta>("PRENATAL", [
      Validators.required,
    ]),
    dum: this.fb.nonNullable.control<Date | null>(null, [Validators.required]),
  });
  triagemForm = this.fb.nonNullable.group({
    pesoKg: [
      null as number | null,
      [Validators.required, Validators.min(30), Validators.max(300)],
    ],
    paSistolica: [
      null as number | null,
      [Validators.required, Validators.min(60), Validators.max(250)],
    ],
    paDiastolica: [
      null as number | null,
      [Validators.required, Validators.min(40), Validators.max(150)],
    ],
  });

  ig = computed(() => {
    const dum = this.identificacaoForm.controls.dum.value;
    if (!dum) return null;
    const hoje = new Date();
    const diff = Math.max(
      Math.floor((hoje.getTime() - dum.getTime()) / 86400000),
      0,
    );
    return { semanas: Math.floor(diff / 7), dias: diff % 7 };
  });

  buscar(): void {
    const termo = this.busca.value.trim();
    if (!termo) return;
    this.carregando.set(true);
    this.consultaService.buscarPacientes(termo).subscribe({
      next: (pacientes) => {
        this.pacientes.set(pacientes);
        this.carregando.set(false);
      },
      error: () => {
        this.snackBar.open("Erro ao buscar pacientes", "Fechar", {
          duration: 3000,
        });
        this.carregando.set(false);
      },
    });
  }

  selecionar(paciente: PacienteConsultaOut): void {
    this.pacienteSelecionada.set(paciente);
    this.pacientes.set([]);
  }

  limparSelecao(): void {
    this.pacienteSelecionada.set(null);
    this.etapa1Concluida.set(false);
    this.consultaId.set(null);
    this.consultaService.definirConsultaAtiva(null);
    this.identificacaoForm.enable();
    this.identificacaoForm.reset();
  }

  confirmarIdentificacao(): void {
    const paciente = this.pacienteSelecionada();
    const tipo = this.identificacaoForm.controls.tipoConsulta.value;
    const dum = this.identificacaoForm.controls.dum.value;

    if (!paciente) return;
    if (tipo === "PRENATAL" && !dum) {
      this.snackBar.open(
        "Informe a Data última menstruação para consulta pre-natal",
        "Fechar",
        {
          duration: 3000,
        },
      );
      return;
    }
    this.consultaService
      .iniciar({
        pacienteId: paciente.id,
        tipoConsulta: tipo,
        dum: dum ? this.formatarDataIso(dum) : null,
      })
      .subscribe({
        next: (consulta) => {
          this.consultaId.set(consulta.idConsulta);
          this.consultaService.definirConsultaAtiva({
            idConsulta: consulta.idConsulta,
            tipo: consulta.tipoConsulta,
          });
          this.etapa1Concluida.set(true);
          this.identificacaoForm.disable();
        },
        error: () =>
          this.snackBar.open("Erro ao iniciar consulta", "Fechar", {
            duration: 3000,
          }),
      });
  }

  concluirTriagem(): void {
    const id = this.consultaId();
    if (!id || this.triagemForm.invalid) return;
    const value = this.triagemForm.getRawValue();
    this.consultaService
      .salvarTriagem(id, {
        pesoKg: Number(value.pesoKg),
        paSistolica: Number(value.paSistolica),
        paDiastolica: Number(value.paDiastolica),
      })
      .subscribe({
        next: () => this.triagemConcluida.set(true),
        error: () =>
          this.snackBar.open("Erro ao concluir triagem", "Fechar", {
            duration: 3000,
          }),
      });
  }

  novaConsulta(): void {
    this.pacienteSelecionada.set(null);
    this.etapa1Concluida.set(false);
    this.triagemConcluida.set(false);
    this.consultaId.set(null);
    this.busca.reset("");
    this.identificacaoForm.reset({ tipoConsulta: "PRENATAL", dum: null });
    this.triagemForm.reset();
  }

  voltarInicio(): void {
    this.router.navigate(["/home"]);
  }

  formatarData(data: string): string {
    const [ano, mes, dia] = data.split("-");
    return `${dia}/${mes}/${ano}`;
  }

  private formatarDataIso(data: Date): string {
    const ano = data.getFullYear();
    const mes = String(data.getMonth() + 1).padStart(2, "0");
    const dia = String(data.getDate()).padStart(2, "0");
    return `${ano}-${mes}-${dia}`;
  }
}
