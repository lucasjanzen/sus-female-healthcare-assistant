import { Component, EventEmitter, Input, OnInit, Output, inject, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatRadioModule } from '@angular/material/radio';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { RastreioOut } from '../../../../../models/consulta.model';
import { ConsultaClinicaService } from '../../../../../services/consulta-clinica.service';
import { AlertaRastreioDialogComponent } from './alerta-rastreio-dialog.component';

export const EPDS_ITENS = [
  'Tenho sido capaz de rir e ver o lado engraçado das coisas',
  'Tenho tido esperança no futuro',
  'Tenho me culpado sem necessidade quando as coisas correm mal',
  'Tenho estado ansiosa ou preocupada sem motivo',
  'Tenho me sentido com medo ou apavorada sem um bom motivo',
  'As coisas têm me oprimido',
  'Tenho me sentido tão infeliz que quase não consigo dormir',
  'Tenho me sentido triste ou muito mal',
  'Tenho me sentido tão infeliz que estou chorando',
  'Já me passou pela cabeça a ideia de me machucar',
];

export const GAD7_ITENS = [
  'Se sentir nervosa, ansiosa ou muito tensa',
  'Não ser capaz de impedir ou controlar as preocupações',
  'Se preocupar muito com diversas coisas',
  'Dificuldade para relaxar',
  'Ficar tão agitada que se torna difícil permanecer sentada',
  'Ficar facilmente aborrecida ou irritável',
  'Sentir medo como se algo horrível pudesse acontecer',
];

export const HITS_ITENS = [
  'Com que frequência seu parceiro te machuca fisicamente?',
  'Com que frequência seu parceiro te insulta ou fala coisas ruins sobre você?',
  'Com que frequência seu parceiro te ameaça com dano físico?',
  'Com que frequência seu parceiro grita ou xinga você?',
];

export const HITS_ESCALA = [
  { value: 1, label: 'Nunca' },
  { value: 2, label: 'Raramente' },
  { value: 3, label: 'Às vezes' },
  { value: 4, label: 'Frequentemente' },
  { value: 5, label: 'Sempre' },
];

export const SITUACAO_SOCIAL_ITENS = [
  'Tem moradia estável',
  'Tem renda própria ou familiar',
  'Tem apoio do companheiro/parceiro',
  'Tem apoio de familiares ou amigos próximos',
  'Tem acesso regular a alimentação',
  'Não enfrenta situação de violência no ambiente doméstico',
];

@Component({
  selector: 'app-rastreio',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatRadioModule, MatCheckboxModule, MatExpansionModule,
    MatFormFieldModule, MatButtonModule, MatIconModule,
    MatProgressBarModule, MatProgressSpinnerModule,
    MatSnackBarModule, MatDialogModule,
  ],
  templateUrl: './rastreio.component.html',
})
export class RastreioComponent implements OnInit {
  @Input() idConsulta!: string;
  @Output() salvo = new EventEmitter<RastreioOut>();

  readonly epdsItens = EPDS_ITENS;
  readonly gad7Itens = GAD7_ITENS;
  readonly hitsItens = HITS_ITENS;
  readonly hitsEscala = HITS_ESCALA;
  readonly situacaoSocialItens = SITUACAO_SOCIAL_ITENS;
  readonly ESCALA_0_3 = [0, 1, 2, 3];

  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(ConsultaClinicaService);
  private readonly dialog = inject(MatDialog);
  private readonly snack = inject(MatSnackBar);

  readonly salvando = signal(false);
  readonly dadosSalvos = signal<RastreioOut | null>(null);

  form: FormGroup = this._buildForm();

  private _buildForm(): FormGroup {
    const controls: Record<string, unknown> = {};
    for (let i = 1; i <= 10; i++) controls[`epds_item_${i}`] = [null];
    for (let i = 1; i <= 7; i++) controls[`gad7_item_${i}`] = [null];
    for (let i = 1; i <= 4; i++) controls[`hits_item_${i}`] = [null];
    for (let i = 1; i <= 6; i++) controls[`social_item_${i}`] = [false];
    return this.fb.group(controls);
  }

  ngOnInit(): void {
    this.svc.obterRastreio(this.idConsulta).subscribe({
      next: (dados) => {
        this.dadosSalvos.set(dados);
        this._preencherForm(dados);
      },
      error: () => {},
    });
  }

  private _preencherForm(dados: RastreioOut): void {
    const patch: Record<string, unknown> = {};
    for (let i = 1; i <= 10; i++) patch[`epds_item_${i}`] = dados.epdsRespostas[`item_${i}`] ?? null;
    for (let i = 1; i <= 7; i++) patch[`gad7_item_${i}`] = dados.gad7Respostas[`item_${i}`] ?? null;
    for (let i = 1; i <= 4; i++) patch[`hits_item_${i}`] = dados.hitsRespostas[`item_${i}`] ?? null;
    for (let i = 1; i <= 6; i++) patch[`social_item_${i}`] = dados.situacaoSocial[`item_${i}`] ?? false;
    this.form.patchValue(patch);
  }

  get epdsScore(): number {
    let total = 0;
    for (let i = 1; i <= 10; i++) {
      const v = this.form.value[`epds_item_${i}`];
      if (v != null) total += Number(v);
    }
    return total;
  }

  get gad7Score(): number {
    let total = 0;
    for (let i = 1; i <= 7; i++) {
      const v = this.form.value[`gad7_item_${i}`];
      if (v != null) total += Number(v);
    }
    return total;
  }

  get hitsScore(): number {
    let total = 0;
    for (let i = 1; i <= 4; i++) {
      const v = this.form.value[`hits_item_${i}`];
      if (v != null) total += Number(v);
    }
    return total;
  }

  get epdsColor(): string {
    if (this.epdsScore >= 12) return '#d32f2f';
    if (this.epdsScore >= 8) return '#f57c00';
    return '#388e3c';
  }

  get gad7Color(): string {
    if (this.gad7Score >= 10) return '#d32f2f';
    if (this.gad7Score >= 5) return '#f57c00';
    return '#388e3c';
  }

  get hitsColor(): string {
    return this.hitsScore >= 11 ? '#d32f2f' : '#388e3c';
  }

  onEpdsItem10Change(valor: number): void {
    if (valor >= 1) {
      this.dialog.open(AlertaRastreioDialogComponent, {
        disableClose: true,
        data: { tipo: 'EPDS_ITEM_10' },
        width: '480px',
      });
    }
  }

  onHitsChange(): void {
    if (this.hitsScore >= 11) {
      this.dialog.open(AlertaRastreioDialogComponent, {
        disableClose: true,
        data: { tipo: 'HITS_FLAG' },
        width: '480px',
      });
    }
  }

  private _buildPayload() {
    const v = this.form.value;
    const epdsRespostas: Record<string, number> = {};
    for (let i = 1; i <= 10; i++) epdsRespostas[`item_${i}`] = Number(v[`epds_item_${i}`] ?? 0);

    const gad7Respostas: Record<string, number> = {};
    for (let i = 1; i <= 7; i++) gad7Respostas[`item_${i}`] = Number(v[`gad7_item_${i}`] ?? 0);

    const hitsRespostas: Record<string, number> = {};
    for (let i = 1; i <= 4; i++) hitsRespostas[`item_${i}`] = Number(v[`hits_item_${i}`] ?? 1);

    const situacaoSocial: Record<string, boolean> = {};
    for (let i = 1; i <= 6; i++) situacaoSocial[`item_${i}`] = Boolean(v[`social_item_${i}`]);

    return { epdsRespostas, gad7Respostas, hitsRespostas, situacaoSocial };
  }

  salvar(): void {
    this.salvando.set(true);
    const payload = this._buildPayload();
    const obs = this.dadosSalvos()
      ? this.svc.atualizarRastreio(this.idConsulta, payload)
      : this.svc.salvarRastreio(this.idConsulta, payload);

    obs.subscribe({
      next: (res) => {
        this.dadosSalvos.set(res);
        this.salvando.set(false);
        this.salvo.emit(res);
        this.snack.open('Rastreio psicossocial salvo.', 'OK', { duration: 3000 });
      },
      error: () => {
        this.salvando.set(false);
        this.snack.open('Erro ao salvar rastreio.', 'OK', { duration: 4000 });
      },
    });
  }
}
