import { Component, EventEmitter, Input, OnDestroy, OnInit, Output, inject, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { ParecerOut } from '../../../../../models/consulta.model';
import { ConsultaClinicaService } from '../../../../../services/consulta-clinica.service';
import { AudioService } from '../../../../../services/audio.service';

@Component({
  selector: 'app-parecer',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatFormFieldModule, MatInputModule, MatButtonModule,
    MatIconModule, MatProgressSpinnerModule, MatSnackBarModule,
    MatExpansionModule,
  ],
  templateUrl: './parecer.component.html',
})
export class ParecerComponent implements OnInit, OnDestroy {
  @Input() idConsulta!: string;
  @Output() salvo = new EventEmitter<ParecerOut>();

  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(ConsultaClinicaService);
  private readonly audioSvc = inject(AudioService);
  private readonly snack = inject(MatSnackBar);

  readonly salvando = signal(false);
  readonly dadosSalvos = signal<ParecerOut | null>(null);
  readonly gravandoParecer = signal(false);
  readonly audioParecerId = signal<string | null>(null);
  readonly transcricaoParecer = signal<string | null>(null);

  private _pollingInterval: ReturnType<typeof setInterval> | null = null;

  form: FormGroup = this.fb.group({ parecerTexto: [''] });

  ngOnInit(): void {
    this.svc.obterParecer(this.idConsulta).subscribe({
      next: (dados) => {
        this.dadosSalvos.set(dados);
        this.form.patchValue({ parecerTexto: dados.parecerTexto });
      },
      error: () => {},
    });
  }

  ngOnDestroy(): void {
    this._pararPolling();
  }

  iniciarGravacaoParecer(): void {
    this.audioSvc.iniciarGravacao(this.idConsulta, 'PARECER_PROFISSIONAL').subscribe({
      next: (res) => {
        this.audioParecerId.set(res.audioId);
        this.gravandoParecer.set(true);
        this.snack.open('Gravação do parecer iniciada.', 'OK', { duration: 2000 });
      },
      error: () => this.snack.open('Erro ao iniciar gravação.', 'OK', { duration: 3000 }),
    });
  }

  encerrarGravacaoParecer(): void {
    this.audioSvc.encerrarGravacao(this.idConsulta).subscribe({
      next: () => {
        this.gravandoParecer.set(false);
        this.snack.open('Gravação encerrada. Transcrição em processamento.', 'OK', { duration: 3000 });
        this._iniciarPolling();
      },
      error: () => this.snack.open('Erro ao encerrar gravação.', 'OK', { duration: 3000 }),
    });
  }

  private _iniciarPolling(): void {
    this._pollingInterval = setInterval(() => {
      this.audioSvc.obterStatus(this.idConsulta).subscribe({
        next: (res) => {
          if (res.transcricao) {
            this.transcricaoParecer.set(res.transcricao);
            this._pararPolling();
          }
        },
        error: () => this._pararPolling(),
      });
    }, 10000);
  }

  private _pararPolling(): void {
    if (this._pollingInterval) {
      clearInterval(this._pollingInterval);
      this._pollingInterval = null;
    }
  }

  salvar(): void {
    this.salvando.set(true);
    const payload = {
      parecerTexto: this.form.value.parecerTexto || null,
      audioParecerId: this.audioParecerId() ?? undefined,
    };
    const obs = this.dadosSalvos()
      ? this.svc.atualizarParecer(this.idConsulta, payload)
      : this.svc.salvarParecer(this.idConsulta, payload);

    obs.subscribe({
      next: (res) => {
        this.dadosSalvos.set(res);
        this.salvando.set(false);
        this.salvo.emit(res);
        this.snack.open('Parecer salvo.', 'OK', { duration: 3000 });
      },
      error: () => {
        this.salvando.set(false);
        this.snack.open('Erro ao salvar parecer.', 'OK', { duration: 4000 });
      },
    });
  }
}
