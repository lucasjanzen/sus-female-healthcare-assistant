import {
  Component,
  EventEmitter,
  Input,
  OnInit,
  Output,
  inject,
} from "@angular/core";
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from "@angular/forms";
import { MatButtonModule } from "@angular/material/button";
import { MatCardModule } from "@angular/material/card";
import { MatChipListboxChange, MatChipsModule } from "@angular/material/chips";
import { MatDialog, MatDialogModule } from "@angular/material/dialog";
import { MatFormFieldModule } from "@angular/material/form-field";
import { MatIconModule } from "@angular/material/icon";
import { MatInputModule } from "@angular/material/input";
import { MatProgressSpinnerModule } from "@angular/material/progress-spinner";
import { MatSnackBar, MatSnackBarModule } from "@angular/material/snack-bar";
import {
  AlertaTriagem,
  Etapa1Out,
  TagQueixa,
  TipoConsulta,
  TriagemCreate,
} from "../../../../../models/consulta.model";
import { TriagemService } from "../../../../../services/triagem.service";
import {
  AlertasDialogComponent,
  AlertasDialogData,
} from "./alertas-dialog.component";

interface TagOpcao {
  value: TagQueixa;
  label: string;
}

@Component({
  selector: "app-bloco-triagem",
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
  ],
  templateUrl: "./bloco-triagem.component.html",
})
export class BlocoTriagemComponent implements OnInit {
  @Input({ required: true }) idConsulta!: string;
  @Input({ required: true }) tipoConsulta!: TipoConsulta;
  @Input() igSemanas: number | null = null;
  @Input() igDias: number | null = null;
  @Input({ required: true }) alturaCm!: number;

  @Output() triagemConcluida = new EventEmitter<Etapa1Out>();

  private fb = inject(FormBuilder);
  private triagemService = inject(TriagemService);
  private dialog = inject(MatDialog);
  private snackBar = inject(MatSnackBar);

  salvando = false;
  tagsSelecionadas: TagQueixa[] = [];

  readonly tagsQueixa: TagOpcao[] = [
    { value: "NAUSEA", label: "Náusea" },
    { value: "VOMITO", label: "Vômito" },
    { value: "DOR_CABECA", label: "Dor de cabeça" },
    { value: "DOR_ABDOMINAL", label: "Dor abdominal" },
    { value: "SANGRAMENTO", label: "Sangramento" },
    { value: "EDEMA", label: "Edema" },
    { value: "TONTURA", label: "Tontura" },
    { value: "FALTA_AR", label: "Falta de ar" },
    { value: "ARDENCIA_URINARIA", label: "Ardência urinária" },
    { value: "CORRIMENTO", label: "Corrimento" },
    {
      value: "MOVIMENTOS_FETAIS_REDUZIDOS",
      label: "Movimentos fetais reduzidos",
    },
    { value: "SEM_QUEIXAS", label: "Sem queixas" },
  ];

  form!: FormGroup;

  ngOnInit(): void {
    this.form = this.fb.group({
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
      temperaturaC: [
        null as number | null,
        [Validators.required, Validators.min(34.0), Validators.max(42.0)],
      ],
      queixasTexto: [""],
    });
  }

  get imcDisplay(): string | null {
    const peso = this.form?.get("pesoKg")?.value as number | null;
    if (!peso || !this.alturaCm) return null;
    const alturaM = this.alturaCm / 100;
    const imc = peso / (alturaM * alturaM);
    const classificacao = this._classificarImc(imc);
    return `IMC: ${imc.toFixed(1)} — ${classificacao}`;
  }

  get igDisplay(): string | null {
    if (this.igSemanas === null) return null;
    const s = this.igSemanas ?? 0;
    const d = this.igDias ?? 0;
    return `${s} semana${s !== 1 ? "s" : ""} e ${d} dia${d !== 1 ? "s" : ""}`;
  }

  onTagsChange(event: MatChipListboxChange): void {
    this.tagsSelecionadas = (event.value ?? []) as TagQueixa[];
  }

  concluirTriagem(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const v = this.form.getRawValue();
    const payload: TriagemCreate = {
      pesoKg: v.pesoKg,
      paSistolica: v.paSistolica,
      paDiastolica: v.paDiastolica,
      temperaturaC: v.temperaturaC,
      queixasTexto: v.queixasTexto || undefined,
      queixasTags: this.tagsSelecionadas.length
        ? this.tagsSelecionadas
        : undefined,
    };

    this.salvando = true;
    this.triagemService.salvar(this.idConsulta, payload).subscribe({
      next: (resultado) => {
        this.salvando = false;
        const alertasCriticos: AlertaTriagem[] =
          resultado.triagem?.alertas?.filter((a) => a.nivel === "CRITICO") ??
          [];

        if (alertasCriticos.length > 0) {
          const dialogData: AlertasDialogData = { alertas: alertasCriticos };
          const ref = this.dialog.open<
            AlertasDialogComponent,
            AlertasDialogData,
            boolean
          >(AlertasDialogComponent, {
            data: dialogData,
            width: "480px",
            disableClose: true,
          });
          ref.afterClosed().subscribe((confirmar) => {
            if (confirmar) {
              this.triagemConcluida.emit(resultado);
            }
          });
        } else {
          this.triagemConcluida.emit(resultado);
        }
      },
      error: (err: { error?: { detail?: string } }) => {
        this.salvando = false;
        const msg = err?.error?.detail ?? "Erro ao registrar triagem";
        this.snackBar.open(msg, "Fechar", { duration: 5000 });
      },
    });
  }

  private _classificarImc(imc: number): string {
    if (imc < 18.5) return "Abaixo do peso";
    if (imc < 25) return "Normal";
    if (imc < 30) return "Sobrepeso";
    return "Obesidade";
  }
}
